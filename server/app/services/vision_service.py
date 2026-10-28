"""Validated disease inference. Demonstration output never drives physical control."""
import json
import logging
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from server.app.core.config import settings

logger = logging.getLogger('vision_service')
CLASES_PAPA = {0: 'tizon_tardio', 1: 'tizon_temprano', 2: 'hoja_sana',
               3: 'mosca_minadora', 4: 'pulgon', 5: 'polilla_papa'}
LESIONES = {'tizon_tardio', 'tizon_temprano'}
INSECTOS = {'mosca_minadora', 'pulgon', 'polilla_papa'}


class VisionUnavailable(RuntimeError):
    pass


class VisionInferenceService:
    def __init__(self, weights_path=None):
        self.weights_path = Path(weights_path or settings.MODEL_WEIGHTS_PATH)
        self.modelo = None
        self.sahi_model = None
        self._cargar_modelo()

    def _cargar_modelo(self):
        if not self.weights_path.is_file():
            logger.warning('Pesos propios ausentes; inferencia real deshabilitada')
            return
        try:
            from ultralytics import YOLO
            model = YOLO(str(self.weights_path))
            names = model.names
            names = dict(enumerate(names)) if isinstance(names, list) else names
            if names != CLASES_PAPA:
                raise ValueError('Taxonomía de los pesos incompatible con las clases de papa')
            self.modelo = model
        except Exception as exc:
            logger.error('No se pudo cargar el modelo validado: %s', exc)
            return
        try:
            from sahi import AutoDetectionModel
            self.sahi_model = AutoDetectionModel.from_pretrained(
                model_type='ultralytics', model=self.modelo,
                confidence_threshold=0.25, device='cpu')
        except Exception as exc:
            logger.warning('SAHI no disponible: %s', exc)

    def procesar_imagen(self, ruta_imagen, tipo_origen='HOJA_FOLLAJE', usar_sahi=False):
        if tipo_origen not in {'HOJA_FOLLAJE', 'TRAMPA_AMARILLA'}:
            raise ValueError('Tipo de origen no válido')
        if self.modelo is None and not settings.VISION_DEMO_MODE:
            raise VisionUnavailable('Instale los pesos propios compatibles o habilite VISION_DEMO_MODE')
        if usar_sahi and self.modelo is not None and self.sahi_model is None:
            raise VisionUnavailable('SAHI solicitado pero no disponible')
        image_path = Path(ruta_imagen)
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError('Imagen no decodificable')
        start = time.monotonic()
        height, width = image.shape[:2]
        is_trap = tipo_origen == 'TRAMPA_AMARILLA'
        use_sahi = self.sahi_model is not None and (usar_sahi or is_trap)
        simulated = self.modelo is None
        boxes = []
        lesion_mask = np.zeros((height, width), dtype=np.uint8)
        if simulated:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            if is_trap:
                yellow = cv2.inRange(hsv, (20, 100, 100), (35, 255, 255))
                dark = cv2.inRange(hsv, (0, 0, 0), (179, 255, 75))
                # Components on an actual yellow background, without a forced minimum count.
                if np.mean(yellow > 0) > 0.25:
                    count, _, stats, _ = cv2.connectedComponentsWithStats(dark)
                    for x, y, w, h, area in stats[1:count]:
                        if 2 <= area <= height * width * 0.05:
                            boxes.append(('pulgon', 0.0, (x, y, x + w, y + h)))
            else:
                lesion_mask = cv2.inRange(hsv, (10, 80, 40), (25, 255, 120))
                disease = np.mean(lesion_mask > 0) > 0.03
                if not disease:
                    lesion_mask[:] = 0
                boxes.append(('tizon_tardio' if disease else 'hoja_sana',
                              0.0, (0, 0, width, height)))
        elif use_sahi:
            from sahi.predict import get_sliced_prediction
            result = get_sliced_prediction(str(image_path), self.sahi_model,
                                          slice_height=320, slice_width=320,
                                          overlap_height_ratio=0.2, overlap_width_ratio=0.2,
                                          verbose=0)
            for prediction in result.object_prediction_list:
                b = prediction.bbox
                boxes.append((CLASES_PAPA[prediction.category.id], float(prediction.score.value),
                              (b.minx, b.miny, b.maxx, b.maxy)))
        else:
            result = self.modelo(image, conf=0.25, verbose=False)[0]
            for box in result.boxes:
                boxes.append((CLASES_PAPA[int(box.cls[0].item())], float(box.conf[0].item()),
                              box.xyxy[0].tolist()))
        annotations = []
        for name, confidence, coords in boxes:
            x1, y1, x2, y2 = [int(v) for v in coords]
            x1, x2 = max(0, min(width, x1)), max(0, min(width, x2))
            y1, y2 = max(0, min(height, y1)), max(0, min(height, y2))
            if x2 <= x1 or y2 <= y1:
                continue
            if name in LESIONES and not simulated:
                lesion_mask[y1:y2, x1:x2] = 255
            annotations.append({'clase': name, 'confianza': round(confidence, 3),
                                'bbox': [x1, y1, x2, y2]})
            cv2.rectangle(image, (x1, y1), (x2 - 1, y2 - 1), (0, 0, 255) if name in LESIONES else (0, 255, 0), 2)
        classes = [b['clase'] for b in annotations]
        dominant = Counter(classes).most_common(1)[0][0] if classes else ('sin_captura' if is_trap else 'sin_deteccion')
        output = image_path.with_name(f'anotada_{image_path.name}')
        if not cv2.imwrite(str(output), image):
            raise OSError('No se pudo guardar la imagen anotada')
        return {
            'clase_detectada': dominant,
            'confianza': round(float(np.mean([b['confianza'] for b in annotations])), 3) if annotations else 0.0,
            'conteo_insectos': sum(c in INSECTOS for c in classes),
            'severidad_porcentaje': round(float(np.mean(lesion_mask > 0) * 100), 2) if not is_trap else 0.0,
            'metrica_severidad': 'area_color_simulada' if simulated else 'cobertura_cajas_lesion_imagen',
            'tiempo_inferencia_ms': round((time.monotonic() - start) * 1000, 2),
            'procesado_con_sahi': bool(use_sahi and not simulated),
            'simulado': simulated,
            'motor': 'heuristica_demo' if simulated else ('sahi' if use_sahi else 'yolo'),
            'bbox_json': json.dumps(annotations),
            'ruta_imagen_original': str(image_path), 'ruta_imagen_anotada': str(output),
        }


vision_service = VisionInferenceService()
