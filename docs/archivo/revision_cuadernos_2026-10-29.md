# Orden de los cuadernos Colab y revisión de entrenamiento

> **Actualización del 3 de noviembre de 2026:** se adaptaron `05` a YOLO26 y `03`
> a comparación medida con YOLO11/YOLOv8 sobre PlantDoc. Se eliminaron las tablas
> de métricas de ejemplo y las rutas fijas a checkpoints. Consulta
> [la guía actual de YOLO26](yolo26.md) para el flujo vigente. El texto que sigue
> documenta la revisión del 29 de octubre y sus hallazgos previos a estos cambios.

Revisión del 29 de octubre de 2026 sobre los archivos actuales del repositorio.

## La numeración no es una única cadena de dependencias

Los archivos `01`, `02`, `03` y `04` corresponden a las fases metodológicas 2, 3, 4 y 5, respectivamente. El cuaderno `05` agrega una ruta independiente para datos reales; no requiere ejecutar antes todos los de menor número.

| Cuaderno | Función real | Dependencia necesaria | Lugar en el flujo |
| --- | --- | --- | --- |
| `00_scratch_pruebas.ipynb` | Dos celdas vacías | Ninguna | Opcional; no prepara ni entrena |
| `01_identificacion_pid_fopdt.ipynb` | Ajuste FOPDT y sintonización PID/Optuna | CSV térmico; genera uno sintético si falta | Rama de control, independiente de visión |
| `02_curaduria_dataset_vision.ipynb` | Taxonomía, funciones de anotación/aumento y estructura YOLO | Imágenes y anotaciones revisadas para una curaduría real | Antes del detector de seis clases, pero actualmente incompleto |
| `03_entrenamiento_comparativa_yolo.ipynb` | Entrena YOLO11n/YOLOv8n; realiza benchmarks y ejemplo SAHI | `data/data.yaml` y train/val/test poblados y verificados | Después de preparar el dataset correspondiente |
| `04_modelo_riesgo_fusion_decision.ipynb` | Modelos de riesgo climático y demostración de fusión | Serie temporal climática con etiquetas; genera datos sintéticos si falta el CSV | Entrenamiento climático independiente; integración multimodal al final |
| `05_entrenamiento_datasets_reales.ipynb` | Prepara PlantVillage/PlantDoc y entrena clasificador y detector independientes | Proyecto y script `scripts/preparar_datasets_reales.py` accesibles desde Colab | Punto de entrada actual para entrenar con imágenes reales |

## Qué ejecutar ahora para entrenar con imágenes reales

Abrir `05_entrenamiento_datasets_reales.ipynb`. No es necesario ejecutar `00–04` antes.

El orden de sus celdas actuales, contado desde la primera celda del archivo e incluyendo Markdown, es:

| Paso | Celdas | Resultado |
| --- | --- | --- |
| 1 | 2–5 | Montaje de Drive, raíz del proyecto e instalación de dependencias |
| 2 | 6–7 | Preparación de ambas fuentes y revisión inicial de reportes |
| 3 | 8–10 | Instalación repetida de Ultralytics y diagnóstico de GPU |
| 4 | 11 | Comprobación de raíz, nueva llamada al preparador y definición de rutas |
| 5 | 13 | Entrenamiento del clasificador PlantVillage, tres clases |
| 6 | 14 | Evaluación final del clasificador y lectura del orden real de clases |
| 7 | 16 | Entrenamiento del detector PlantDoc, dos enfermedades |
| 8 | 17 | Evaluación final del detector |

Las celdas 3/5/8 repiten instalaciones y las 6/11 repiten preparación. No son fases nuevas. El preparador verifica la salida existente y retorna si ya está preparada. La organización puede simplificarse posteriormente sin cambiar el experimento.

El detector PlantDoc **no se inicializa con el clasificador PlantVillage**: carga `yolo11n.pt` por separado. Por tanto, ejecutar primero clasificación y luego detección es el orden del cuaderno, pero ambos entrenamientos son independientes.

Configurar `IOTTESIS_ROOT` con la carpeta que realmente contiene `scripts/preparar_datasets_reales.py`. Que Drive monte correctamente no significa que el proyecto exista allí. Evitar continuar si las comprobaciones de carpeta/script devuelven `False`.

Los resultados se escriben dentro de `PROJECT_ROOT/runs/datasets_reales`. Obtener el checkpoint desde `modelo.trainer.save_dir / 'weights/best.pt'`, como hace este cuaderno; no asumir que una repetición usará exactamente el mismo nombre de carpeta.

PlantVillage usa carpetas por clase: es **clasificación de imagen**. PlantDoc usa cajas de **hojas completas**, no segmentaciones ni cajas de lesión. Este piloto excluye la categoría genérica no confirmada como sana y usa dos clases de enfermedad. No estima severidad por área lesionada y no entrena insectos.

## Flujo completo de la tesis

1. **Rama de visión:** obtener imágenes y anotaciones fiables → separar grupos físicos/orígenes y duplicados → entrenar → elegir configuración con validación → evaluar una vez en test independiente → exportar.
2. **Rama de control:** ejecutar `01` con la curva térmica → identificar parámetros → sintonizar y evaluar PID. Puede avanzar en paralelo a visión.
3. **Rama climática:** ejecutar `04` con una serie temporal y etiquetas válidas → entrenamiento temporal → calibración/selección con validación → evaluación final.
4. **Integración:** alinear clima y detecciones reales por timestamp/nodo → validar la fusión y las consignas con el control ya evaluado.

Para detección local de seis clases, `02 → 03` sigue siendo el esquema previsto, **una vez completada la curaduría real**. `05` permite iniciar pilotos con fuentes públicas, pero sus datasets/modelos no sustituyen automáticamente el contrato de seis clases de esa ruta.

`04` no carga los pesos ni las predicciones de `03`/`05`. Sus columnas de visión actuales son simuladas; ejecutar YOLO primero no las convierte en observaciones reales. La dependencia entre visión y riesgo debe implementarse en la etapa de integración, no deducirse de la numeración.

## Hallazgos que afectan a los resultados

### Cuaderno 01

- Guarda errores `NameError` para `optuna`, `K_opt` y `kp_zn`, con contadores de ejecución fuera de secuencia.
- Se comprobó ejecución completa, de arriba abajo, en una carpeta temporal, omitiendo el montaje de Drive y usando su generación sintética: terminó correctamente y produjo cinco filas de comparación.
- Parámetros observados en esa prueba: K ≈ 0,1640; tau ≈ 244,29 s; theta ≈ 32,40 s. Corresponden al ensayo sintético, no a mediciones nuevas del invernadero.
- Si faltan dependencias, la instalación está comentada: debe habilitarse en la sesión Colab antes de importar.
- Las figuras/tablas se guardan con nombres relativos, aunque se monte Drive; revisar dónde se escriben antes de cerrar la sesión.

### Cuaderno 02

- La sección titulada partición 70/15/15 solo crea carpetas y `data/data.yaml`; no implementa la partición por planta/trampa ni copia/etiqueta imágenes.
- El contador de clases no demuestra ausencia de fuga de datos.
- La heurística HSV propone clases de insectos por tamaño: requiere revisión humana; no acredita especie.
- El script antiguo `preparar_dataset_vision.py` genera dibujos sintéticos y elimina/recrea `data/dataset_yolo`. No debe usarse como preparación de evidencia real ni sobre un dataset valioso.

### Cuaderno 03

- La tabla final contiene mAP/F1/accuracy numéricos escritos directamente y latencias escaladas con constantes; no son resultados derivados de las evaluaciones de todos esos modelos.
- Faster R-CNN se carga y cronometra sin entrenarlo/evaluarlo en papa. MobileNet reemplaza la capa final y cronometra, pero no entrena ese clasificador.
- La sección SAHI usa una muestra, no calcula por sí sola una comparación cuantitativa de recall/mAP, y permite volver al modelo genérico si falta el checkpoint propio.
- `project='runs/detect'` guarda en la sesión actual; montar Drive no cambia esa ruta. La ruta fija a `yolo11n_invernadero/weights/best.pt` puede apuntar a una ejecución anterior si Ultralytics incrementa el nombre de la nueva carpeta.
- No usar la tabla final como evidencia de la tesis hasta reemplazarla por métricas medidas y comparables sobre el mismo conjunto de prueba.

### Cuaderno 04

- Si no encuentra `../data/synthetic/dataset_agroclimatico_invernadero.csv`, genera 90 días sintéticos. La ruta es relativa al directorio de trabajo y no monta Drive.
- Se comprobó generación, ingeniería de características, partición y baseline: 2160 filas, divididas en 1296/432/432.
- La etiqueta `riesgo_infeccion_gt` se define como `blight_units_7d >= 14`. El baseline clasifica usando el mismo umbral. Se verificó identidad de etiquetas y baseline con ROC-AUC = 1 y F1 = 1. Eso comprueba consistencia interna del generador, no capacidad predictiva clínica/agronómica independiente.
- La LSTM predice la etiqueta del paso siguiente a su ventana y omite las primeras 24 muestras de cada partición; los modelos tabulares utilizan características del instante etiquetado. Alinear objetivo/horizonte e instantes antes de comparar métricas.
- La tabla llama a XGBoost ganador sin seleccionarlo mediante un criterio de validación implementado. No asumir esa conclusión sin evaluación.
- No exporta el modelo, el calibrador ni el escalador para el servidor; esa entrega sigue pendiente.

### Cuaderno 05 y despliegue

- El piloto PlantVillage tiene validación/test internos de esa fuente. No equivale a la validación de invernadero exigida en `docs/protocolo_captura_y_etiquetado.md`.
- El piloto PlantDoc recompone los grupos TRAIN/TEST originales: no es el benchmark oficial y requiere revisión agronómica.
- Un checkpoint de clasificación de tres clases o detección de dos clases no se puede conectar sin adaptación a un backend que interprete seis identificadores y salida de detección. Verificar `model.task`, `model.names`, preprocesamiento y significado de las cajas antes de copiar pesos.
- El cuaderno no aporta todavía entrenamiento de minadora, pulgón o polilla.

## Alcance de la verificación

Se inspeccionaron todas las celdas y los scripts de preparación relacionados. Todas las celdas de código compilan sintácticamente después de transformar las instrucciones de IPython/Colab. Se ejecutó íntegramente `01` en un directorio temporal y se ejecutaron las etapas de datos/características/partición/baseline de `04`, sin modificar sus archivos ni datos del proyecto.

No se ejecutaron entrenamientos YOLO ni descargas de datasets, ni se certificó una ejecución completa en un runtime real de Colab. No se modificaron los cuadernos durante esta revisión. Los resultados locales no acreditan entrenamiento previo en otra sesión de Drive.
