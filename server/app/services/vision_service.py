"""YOLO26/YOLO11 inference with task-aware labels and explicit box semantics."""
import hashlib
import json
import logging
from collections import Counter
from pathlib import Path
import threading
import time

import cv2
import numpy as np

from server.app.core.config import settings, BASE_DIR

logger = logging.getLogger('vision_service')
CLASES_PAPA = {0: 'tizon_tardio', 1: 'tizon_temprano', 2: 'hoja_sana',
               3: 'mosca_minadora', 4: 'pulgon', 5: 'polilla_papa'}
FOLIARES = {'tizon_tardio', 'tizon_temprano', 'hoja_sana'}
LESIONES = {'tizon_tardio', 'tizon_temprano'}
INSECTOS = {'mosca_minadora', 'pulgon', 'polilla_papa'}


class VisionUnavailable(RuntimeError):
    """Configured trained weights or an explicitly requested inference engine are absent."""


class VisionInferenceService:
    def __init__(self, weights_path=None):
        self.weights_path = Path(weights_path or settings.MODEL_WEIGHTS_PATH)
        if not self.weights_path.is_absolute():
            self.weights_path = BASE_DIR / self.weights_path
        self.modelo = None
        self.sahi_model = None
        self.tarea = None
        self.class_names = {}
        self.box_semantics = settings.VISION_BOX_SEMANTICS
        self.error_modelo = ''
        self._lock = threading.RLock()
        self._cargar_modelo()

    def _cargar_modelo(self):
        # A general COCO checkpoint is not a plant disease classifier.
        # In particular, never relabel COCO class IDs with CLASES_PAPA.
        if not self.weights_path.is_file():
            self.error_modelo = 'Faltan pesos entrenados. Configura MODEL_WEIGHTS_PATH con el best.pt de tu entrenamiento.'
            logger.warning('[VISION] %s', self.error_modelo)
            return
        try:
            from ultralytics import YOLO
            model = YOLO(str(self.weights_path))
            if model.task not in {'detect', 'classify'}:
                raise ValueError('Solo se admiten checkpoints de detección o clasificación')
            names = dict(enumerate(model.names)) if isinstance(model.names, list) else dict(model.names)
            names = {int(key): str(value) for key, value in names.items()}
            if (not names or set(names) != set(range(len(names))) or
                    len(set(names.values())) != len(names) or not set(names.values()) <= set(CLASES_PAPA.values())):
                raise ValueError('Clases incompatibles con papa; no se admiten pesos COCO genéricos')
            if model.task == 'classify' and not set(names.values()) <= FOLIARES:
                raise ValueError('El clasificador debe ser foliar; no permite contar insectos')
            metadata_file = self.weights_path.with_suffix('.metadata.json')
            if metadata_file.is_file():
                metadata = json.loads(metadata_file.read_text())
                if metadata.get('task') != model.task:
                    raise ValueError('Los metadatos no corresponden a la tarea de los pesos')
                if {int(k): v for k, v in metadata.get('names', {}).items()} != names:
                    raise ValueError('Las clases de los metadatos no corresponden a los pesos')
                expected = metadata.get('weights_sha256')
                if expected and hashlib.sha256(self.weights_path.read_bytes()).hexdigest() != expected:
                    raise ValueError('El hash de los pesos no corresponde a sus metadatos')
                self.box_semantics = metadata.get('box_semantics', 'unknown')
            if self.box_semantics not in {'unknown', 'whole_leaf', 'lesion', 'none'}:
                raise ValueError('Semántica de cajas inválida')
            self.modelo, self.tarea, self.class_names = model, model.task, names
        except Exception as exc:
            self.error_modelo = f'No se pudieron cargar pesos compatibles: {exc}'
            logger.error('[VISION] %s', self.error_modelo)
            return
        if self.tarea == 'detect':
            try:
                from sahi import AutoDetectionModel
                self.sahi_model = AutoDetectionModel.from_pretrained(
                    model_type='ultralytics', model=self.modelo,
                    confidence_threshold=0.25, device='cpu')
            except Exception as exc:
                # Standard YOLO still works if optional sliced inference cannot initialize.
                logger.warning('[VISION] SAHI no disponible: %s', exc)

    def procesar_imagen(self, ruta_imagen, tipo_origen='HOJA_FOLLAJE', usar_sahi=False):
        if tipo_origen not in {'HOJA_FOLLAJE', 'TRAMPA_AMARILLA'}:
            raise ValueError('Tipo de origen no válido')
        image_path = Path(ruta_imagen)
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError('No se pudo decodificar la imagen')
        if self.modelo is None and not settings.VISION_DEMO_MODE:
            raise VisionUnavailable(self.error_modelo)
        start = time.perf_counter()
        is_trap = tipo_origen == 'TRAMPA_AMARILLA'
        simulated = self.modelo is None
        annotations = []
        confidences = []
        height, width = image.shape[:2]
        lesion_mask = np.zeros((height, width), dtype=np.uint8)
        use_sahi = False
        severity_available = False
        count_available = False
        with self._lock:
            if simulated:
                dominant, confidence = 'demostracion_sin_modelo', 0.0
            elif self.tarea == 'classify':
                if is_trap or usar_sahi:
                    raise ValueError('El clasificador foliar no admite trampas ni SAHI')
                result = self.modelo(image, verbose=False)[0]
                if result.probs is None:
                    raise ValueError('El checkpoint no produjo probabilidades de clasificación')
                dominant = self.class_names[int(result.probs.top1)]
                confidence = float(result.probs.top1conf.item())
                cv2.putText(image, f'{dominant} {confidence:.2f}', (10, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)
            else:
                relevant_classes = INSECTOS if is_trap else FOLIARES
                if not set(self.class_names.values()) & relevant_classes:
                    raise ValueError('El modelo cargado no incluye clases para ese tipo de imagen')
                if usar_sahi and self.sahi_model is None:
                    raise VisionUnavailable('SAHI solicitado pero no está disponible para el modelo')
                use_sahi = self.sahi_model is not None and (usar_sahi or is_trap)
                detections = []
                if use_sahi:
                    from sahi.predict import get_sliced_prediction
                    results = get_sliced_prediction(str(image_path), self.sahi_model,
                                                   slice_height=320, slice_width=320,
                                                   overlap_height_ratio=0.2, overlap_width_ratio=0.2,
                                                   verbose=0)
                    for prediction in results.object_prediction_list:
                        box = prediction.bbox
                        detections.append((prediction.category.id, float(prediction.score.value),
                                           (box.minx, box.miny, box.maxx, box.maxy)))
                else:
                    result = self.modelo(image, conf=0.25, verbose=False)[0]
                    for box in result.boxes:
                        detections.append((int(box.cls[0].item()), float(box.conf[0].item()),
                                           box.xyxy[0].tolist()))
                for class_id, probability, coords in detections:
                    name = self.class_names[int(class_id)]
                    if name not in relevant_classes:
                        continue
                    x1, y1, x2, y2 = (int(v) for v in coords)
                    x1, x2 = max(0, min(width, x1)), max(0, min(width, x2))
                    y1, y2 = max(0, min(height, y1)), max(0, min(height, y2))
                    if x2 <= x1 or y2 <= y1:
                        continue
                    annotations.append({'clase': name, 'confianza': round(probability, 3),
                                        'bbox': [x1, y1, x2, y2]})
                    confidences.append(probability)
                    if name in LESIONES and self.box_semantics == 'lesion':
                        lesion_mask[y1:y2, x1:x2] = 255
                    cv2.rectangle(image, (x1, y1), (x2 - 1, y2 - 1), (0, 0, 255) if name in LESIONES else (0, 200, 0), 2)
                    cv2.putText(image, f'{name} {probability:.2f}', (x1, max(15, y1 - 5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
                names = [b['clase'] for b in annotations]
                dominant = Counter(names).most_common(1)[0][0] if names else 'sin_deteccion'
                confidence = float(np.mean(confidences)) if confidences else 0.0
                severity_available = not is_trap and self.box_semantics == 'lesion' and bool(set(self.class_names.values()) & LESIONES)
                count_available = is_trap
        output = image_path.with_name('anotada_' + image_path.name)
        if not cv2.imwrite(str(output), image):
            raise OSError('No se pudo guardar la imagen anotada')
        return {
            'clase_detectada': dominant, 'confianza': round(confidence, 3),
            'bbox_json': json.dumps(annotations),
            # Legacy numeric fields remain serializable; validity flags distinguish 0 from N/A.
            'conteo_insectos': sum(a['clase'] in INSECTOS for a in annotations) if count_available else 0,
            'severidad_porcentaje': round(float(np.mean(lesion_mask > 0) * 100), 2) if severity_available else 0.0,
            'severidad_disponible': severity_available,
            'conteo_disponible': count_available,
            'metrica_severidad': 'cobertura_cajas_lesion_imagen' if severity_available else 'no_disponible',
            'apto_supervision': not simulated and (severity_available or count_available),
            'simulado': simulated, 'tarea_modelo': self.tarea,
            'semantica_cajas': self.box_semantics,
            'tiempo_inferencia_ms': round((time.perf_counter() - start) * 1000, 2),
            'procesado_con_sahi': bool(use_sahi),
            'ruta_imagen_original': str(image_path), 'ruta_imagen_anotada': str(output),
        }


vision_service = VisionInferenceService()
