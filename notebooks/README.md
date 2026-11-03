# Colab: empieza aquí
La ruta actual usa pasos consecutivos. Los cuadernos previos están en `archivo/`; PID y riesgo son ramas independientes.
**Ruta corta:** `00 → 01 → 02 → 04`. **Con comparación:** `00 → 01 → 02 → 03 → 04`.
| Paso | Cuaderno | Qué ejecutar | Resultado |
| --- | --- | --- | --- |
| 00 | [Inicio y datasets](00_inicio_y_datasets.ipynb) | Celdas 1–4, sin GPU | Datos verificados y estado de pendientes |
| 01 | [Clasificador](01_entrenar_clasificador.ipynb) | Celdas 1–6; la 5 entrena si falta | YOLO26n-cls, 3 clases |
| 02 | [Detector](02_entrenar_detector.ipynb) | Celdas 1–6; la 5 entrena si falta | YOLO26n, hojas completas, 2 enfermedades |
| 03 | [Comparación](03_comparar_detectores.ipynb) | Opcional: celdas 1–6 | Selección por validación; reutiliza YOLO26 de 02 |
| 04 | [Evaluación y exportación](04_evaluacion_y_exportacion.ipynb) | Celdas 1–6; 7–9 opcionales | Test final, resumen y archivos de entrega |

## Celdas de cada cuaderno
Se numeran **las celdas de código**: el encabezado `Celda 01`, `Celda 02`, etc. aparece también dentro de la celda. Los contadores `[1]`, `[2]` de Colab indican ejecución y pueden cambiar; no son la guía de orden.

### 00_inicio_y_datasets.ipynb

| Celda | Acción | Tipo |
| --- | --- | --- |
| 1 | Conectar Drive y localizar o extraer el proyecto | obligatoria en este cuaderno |
| 2 | Instalar dependencias de esta sesión | obligatoria en este cuaderno |
| 3 | Comprobar entorno y cargar el flujo | obligatoria en este cuaderno |
| 4 | Preparar o verificar ambos datasets | obligatoria en este cuaderno |

### 01_entrenar_clasificador.ipynb

| Celda | Acción | Tipo |
| --- | --- | --- |
| 1 | Conectar Drive y localizar o extraer el proyecto | obligatoria en este cuaderno |
| 2 | Instalar dependencias de esta sesión | obligatoria en este cuaderno |
| 3 | Comprobar entorno y cargar el flujo | obligatoria en este cuaderno |
| 4 | Fijar la configuración y verificar el plan | obligatoria en este cuaderno |
| 5 | Entrenar o reutilizar una ejecución completa | obligatoria en este cuaderno; usa GPU si debe entrenar |
| 6 | Comprobar que quedaron guardados los resultados | obligatoria en este cuaderno |

### 02_entrenar_detector.ipynb

| Celda | Acción | Tipo |
| --- | --- | --- |
| 1 | Conectar Drive y localizar o extraer el proyecto | obligatoria en este cuaderno |
| 2 | Instalar dependencias de esta sesión | obligatoria en este cuaderno |
| 3 | Comprobar entorno y cargar el flujo | obligatoria en este cuaderno |
| 4 | Fijar la configuración y verificar el plan | obligatoria en este cuaderno |
| 5 | Entrenar o reutilizar una ejecución completa | obligatoria en este cuaderno; usa GPU si debe entrenar |
| 6 | Comprobar que quedaron guardados los resultados | obligatoria en este cuaderno |

### 03_comparar_detectores.ipynb

| Celda | Acción | Tipo |
| --- | --- | --- |
| 1 | Conectar Drive y localizar o extraer el proyecto | obligatoria en este cuaderno |
| 2 | Instalar dependencias de esta sesión | obligatoria en este cuaderno |
| 3 | Comprobar entorno y cargar el flujo | obligatoria en este cuaderno |
| 4 | Fijar la comparación | obligatoria en este cuaderno |
| 5 | Entrenar solo las familias que falten | opcional; usa GPU si debe entrenar |
| 6 | Seleccionar por validación y guardar la decisión | obligatoria en este cuaderno |

### 04_evaluacion_y_exportacion.ipynb

| Celda | Acción | Tipo |
| --- | --- | --- |
| 1 | Conectar Drive y localizar o extraer el proyecto | obligatoria en este cuaderno |
| 2 | Instalar dependencias de esta sesión | obligatoria en este cuaderno |
| 3 | Comprobar entorno y cargar el flujo | obligatoria en este cuaderno |
| 4 | Recuperar modelos guardados y fijar la evaluación | obligatoria en este cuaderno |
| 5 | Evaluar test final una vez | obligatoria en este cuaderno |
| 6 | Guardar resumen y mostrar archivos de entrega | obligatoria en este cuaderno |
| 7 | Evaluar los demás detectores de 03 — OPCIONAL | opcional |
| 8 | Medir latencia CPU — OPCIONAL | opcional |
| 9 | Exportar ONNX — OPCIONAL | opcional |

## Regla de ejecución

1. En una sesión nueva o un cuaderno distinto, repetir sus celdas 1–3.
2. En 01/02/03 mantener `REENTRENAR=False` y `REANUDAR=True`: se reutilizan ejecuciones
   completas equivalentes y se recupera un `last.pt` compatible con respaldo previo.
   Si el entrenamiento terminó y solo falta el registro, se completan validación y
   metadatos sin volver a entrenar. Las ejecuciones antiguas sin huella previa del
   dataset registran esa incertidumbre histórica; comprobar el dataset actual no
   acredita retrospectivamente los datos originales.
3. Si falta GPU, la celda de entrenamiento se detiene. `PERMITIR_CPU=True` es solo para una prueba deliberada en CPU.
   El perfil actual requiere GPU T4 y usa `DEVICE=0`, lote 16 en clasificación
   y lote 8 en detección/comparación. La celda 3 muestra la GPU real disponible.
   Tras cambiar el tipo de entorno, repetir 1–3; la celda 4 vuelve a importar
   `training_plan` y explica el orden si falta `PROJECT_ROOT`.
4. En 04 revisar la celda 4 y poner `CONFIRMAR_MODELOS_FIJADOS=True` solo cuando no vayas a seguir ajustando con validación; después ejecutar 5 y 6.
5. Las celdas 7–9 de 04 son opcionales: comparar test de los demás detectores, medir latencia CPU y exportar ONNX. Todas vienen desactivadas.
6. Si test ya está guardado, se muestra sin repetirlo, incluso al volver a ejecutar la misma celda.

No necesitas ejecutar control, riesgo ni archivo para entrenar YOLO26.

## Estado actualizado

Desde la raíz del proyecto, `make colab-status` muestra qué hay realmente y cuál es el siguiente cuaderno. No acredita trabajo hecho en una sesión remota de Drive que no se haya copiado aquí.

Detalles de pendientes, copia a Drive y entrega: [guía completa](../docs/orden_cuadernos_colab.md).
