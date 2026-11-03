# YOLO26: modelos y entrega al backend

Actualizado el 3 de noviembre de 2026. Para el orden de ejecución, usar la
[guía actual de Colab](orden_cuadernos_colab.md) y el [índice de celdas](../notebooks/README.md).

## Modelos y datos

YOLO26n es la opción principal; YOLO11n/YOLOv8n quedan para comparación opcional.
El proyecto no presupone que YOLO26 gane: 03 selecciona por validación y 04
concentra toda la evaluación de test.

| Tarea | Modelo inicial | Dataset | Cuaderno |
| --- | --- | --- | --- |
| Clasificación | `yolo26n-cls.pt` | PlantVillage, 2.152 imágenes, 3 clases | `01_entrenar_clasificador.ipynb` |
| Detección | `yolo26n.pt` | PlantDoc, 219 imágenes, 2 enfermedades | `02_entrenar_detector.ipynb` |

Ambos entrenamientos son independientes. Los pesos generales se descargan al
comenzar el entrenamiento si faltan; no reconocen enfermedades de papa por el
simple hecho de cargarlos. Las cajas PlantDoc delimitan hojas completas y no
miden severidad de lesión. Estos pilotos no incluyen insectos.

## Flujo recomendado

Abrir `notebooks/00_inicio_y_datasets.ipynb`. Seguir 00 → 01 → 02 → 04,
o 00 → 01 → 02 → 03 → 04 para comparar familias. Las celdas numeradas indican
cuáles instalan, verifican, entrenan o evalúan. Cada sesión recupera resultados
del disco; `REENTRENAR=False` evita repetir ejecuciones equivalentes.

```bash
make colab-status       # estado real de datos/checkpoints y siguiente paso
make colab-package      # ZIP local listo para copiar a Drive
```

No se inicia entrenamiento ni se suben datos a Drive con estos comandos.

## Terminal: uso avanzado

```bash
python -m pip install -r requirements-vision.txt
python scripts/entrenar_yolo26.py --source plantdoc --dry-run
python scripts/entrenar_yolo26.py --source plantvillage --dry-run
```

`--dry-run` verifica los datos sin descargar pesos ni entrenar. Para una ejecución
nueva deliberada por terminal:

```bash
python scripts/entrenar_yolo26.py --source plantdoc --epochs 50
python scripts/entrenar_yolo26.py --source plantvillage --epochs 50
```

Este CLI de bajo nivel inicia un entrenamiento cada vez: para reutilización
usar los cuadernos o `run_or_reuse` de `scripts/flujo_colab.py`. Las alternativas
son `--family yolo11` y `--family yolov8`. Test es explícito mediante
`--evaluate-test`, aunque el flujo guiado lo reserva exclusivamente al cuaderno 04.

## Archivos producidos al entrenar

```text
runs/datasets_reales/<familia>n_<fuente>_<tarea>/
  weights/best.pt
  weights/best.metadata.json
  experiment.json
  args.yaml
  results.csv
```

Se utiliza la carpeta real de Ultralytics, incluidos sufijos incrementados.
Los metadatos registran tarea, clases, semántica de cajas, versiones, procedencia
y hash de los pesos. `experiment.json` registra validación; test se añade al
pasar por 04. La selección de 03 se conserva en `seleccion_por_validacion.json`.
El resumen de 04 se guarda en `resumen_evaluacion_final.csv`.

## Cargar pesos propios en el backend

Configurar `.env`, usando la ruta real de la ejecución:

```dotenv
MODEL_WEIGHTS_PATH=runs/datasets_reales/yolo26n_plantdoc_detect/weights/best.pt
VISION_DEMO_MODE=false
VISION_BOX_SEMANTICS=unknown
```

Conservar `best.metadata.json` junto al checkpoint. Si se renombran/copían los
pesos a `data/models/yolo26n_papa.pt`, los metadatos se llaman
`data/models/yolo26n_papa.metadata.json`.

El backend admite `detect` y `classify`, obtiene las clases de `model.names` y
verifica la correspondencia de los metadatos/hash. Rechaza taxonomías COCO y
tareas no soportadas. Sin pesos propios devuelve HTTP 503; no descarga un modelo
genérico y reinterpreta sus IDs como papa. Los pesos YOLO11 propios siguen
admitidos mediante su ruta explícita. Instalar `requirements-vision.txt` también
en el entorno que ejecute el backend; el ESP32 mantiene el PID.

SAHI usa `model_type='ultralytics'` y solo funciona con detectores. El clasificador
rechaza trampas y SAHI. Si falla la inicialización de SAHI, sigue disponible
la inferencia estándar del detector.

## Límites de interpretación

- `severidad_disponible=false` significa **no medido**; la interfaz muestra «No disponible».
- Las cajas de hoja completa no se convierten en daño porcentual ni en insectos.
- El clasificador no inventa cajas ni cuenta plagas.
- Solo cajas explícitamente identificadas como `lesion` permiten aproximar
  cobertura de cajas sobre la imagen; no equivale a segmentación calibrada.
- Pilotos foliares y modo demo no publican métricas al supervisor ni disparan
  alarmas automáticas desde FastAPI.
- Faltan revisión agronómica, datos locales, anotaciones de lesión y especies
  identificadas para afirmar desempeño físico del sistema completo.

## Verificación de integración

Se comprobó inferencia CPU de YOLO26n, YOLO26n-cls y slicing SAHI usando
arquitecturas con pesos aleatorios e imágenes de prueba; no se midió precisión.
El entorno local dispone de Ultralytics 8.4.183, SAHI 0.12.8 y PyTorch 2.14.1+cpu.
Se verificaron los datasets preparados y las pruebas de tareas, etiquetas,
metadatos, control de severidad, portabilidad y orden de ejecución.

No se ha ejecutado aquí un entrenamiento completo de 50 épocas. Los resultados
científicos se producen al ejecutar el flujo con los datos y el entorno indicados.

Referencias: [YOLO26](https://docs.ultralytics.com/models/yolo26/) e
[integración con SAHI](https://docs.ultralytics.com/guides/sahi-tiled-inference/).
