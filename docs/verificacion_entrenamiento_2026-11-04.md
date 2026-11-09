# Verificación de entrenamiento y siguiente etapa

Fecha: 4 de noviembre de 2026. Se revisaron los artefactos de Drive y las salidas guardadas de los cuadernos 00–04. La ruta principal de YOLO26 tiene entrenamiento, selección por validación y test final guardados. La comparación de 03 se ejecutó con YOLO26 y YOLO11.

| Modelo | Épocas ejecutadas / máximo | Validación | Test final |
| --- | --- | --- | --- |
| YOLO26n-cls / PlantVillage | 25 / 50 | Exactitud top-1: 100.0% | Exactitud top-1: 100.0% |
| YOLO26n / PlantDoc | 40 / 50 | mAP50–95: 46.99% | mAP50: 49.26%; mAP50–95: 32.16% |
| YOLO11n / PlantDoc | 43 / 50 | mAP50–95: 39.81% | No evaluado; opcional |

Los CSV terminan antes de las 50 épocas previstas: la mejor época fue 10, 25 y 28, respectivamente, y la última 25, 40 y 43; coincide con la parada temprana configurada con paciencia 15. YOLO26 quedó seleccionado por su mAP50–95 de validación. El test de clasificación contiene 323 imágenes; el de detección, 33 imágenes y 85 cajas. La precisión del detector en test fue 45.51% y su recall 59.85%.

Se comprobaron los SHA-256 de los tres best.pt contra sus best.metadata.json. El servicio VisionInferenceService cargó los tres checkpoints y produjo inferencia real en CPU con una imagen de validación de cada tarea. Esta comprobación de carga no volvió a evaluar test ni estima exactitud con esas imágenes de muestra. El entorno local utilizó Ultralytics 8.4.183 y PyTorch 2.14.1+cpu.

Los manifiestos de Drive coinciden con las huellas guardadas al entrenar. Los manifiestos locales difieren en las notas de fuentes excluidas; sus registros, clases y particiones coinciden con los usados en entrenamiento. También se verificó la integridad de las 2.152 imágenes locales de PlantVillage y las 219 de PlantDoc. Cada copia de modelo incluye dataset.manifest.json con el manifiesto exacto de su entrenamiento.

YOLOv8 tiene una sola época registrada, last.pt y best.pt, pero carece de experiment.json y metadatos finales: sigue pendiente. Fue excluido de FAMILIES en el cuaderno 03. La comparación actual debe describirse como YOLO26 frente a YOLO11. Las celdas opcionales de test de otros detectores, benchmark CPU y ONNX se ejecutaron con sus indicadores en False y fueron omitidas.

Los pesos verificados ya están disponibles localmente:

- [Detector YOLO26](/home/rodrigo/Desktop/IOTtesis/data/models/entrenados_colab/yolo26n_plantdoc_detect/weights/best.pt).
- [Clasificador YOLO26](/home/rodrigo/Desktop/IOTtesis/data/models/entrenados_colab/yolo26n_plantvillage_classify/weights/best.pt).
- [Detector YOLO11](/home/rodrigo/Desktop/IOTtesis/data/models/entrenados_colab/yolo11n_plantdoc_detect/weights/best.pt).
- [Verificación detallada y hashes](/home/rodrigo/Desktop/IOTtesis/data/models/entrenados_colab/verificacion.json).

La siguiente etapa es probar el detector seleccionado en el dashboard. Configurar en .env:

```dotenv
MODEL_WEIGHTS_PATH=data/models/entrenados_colab/yolo26n_plantdoc_detect/weights/best.pt
VISION_DEMO_MODE=false
```

Después, reiniciar el servidor y cargar fotos propias desde la pantalla de visión. El comando local disponible es make server. El backend actual carga un modelo por configuración; para trabajar con fotos individuales de hoja se puede seleccionar el clasificador cambiando MODEL_WEIGHTS_PATH a su best.pt. Los metadatos permanecen junto a cada archivo de pesos.

Para la tesis, conservar los registros, la selección y el resumen de test, y describir el alcance real de los pilotos públicos. El 100% de PlantVillage corresponde al dataset público evaluado; hace falta una prueba independiente con imágenes propias del invernadero. El detector presenta un rendimiento piloto moderado y requiere revisar errores con anotaciones de campo. Sus cajas delimitan hojas completas de dos enfermedades; la severidad y el conteo de insectos siguen sin medirse con estos modelos. El PID del ESP32 permanece como lazo local independiente.

Fuentes verificadas: [resumen final de test](https://drive.google.com/file/d/1rGfIRnCVXpCqGS5S0fp1amjvFiMmpYki/view?usp=drivesdk), [selección por validación](https://drive.google.com/file/d/1UqHHLf3rn0CvIi0andSmE57vrZxFCnKq/view?usp=drivesdk), [registro del clasificador](https://drive.google.com/file/d/1up8rIaWW3wqrCkKI4KpuP7_ml3Q_sA64/view?usp=drivesdk), [registro del detector](https://drive.google.com/file/d/11dBl4aW7axBMqhQPjYgr_Id4s539ejCX/view?usp=drivesdk), [registro de YOLO11](https://drive.google.com/file/d/1OCdiuMdIB-NFquCdE7ctB1jiNsLx9fg3/view?usp=drivesdk).
