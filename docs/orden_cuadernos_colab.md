# Estructura y orden actual para Colab

Actualizado el 3 de noviembre de 2026. Esta es la guía vigente; la revisión anterior
se conserva en `docs/archivo/revision_cuadernos_2026-10-29.md`.

## Empieza por 00

Abre `notebooks/00_inicio_y_datasets.ipynb` y ejecuta sus **cuatro celdas de código**.
Cada celda muestra su número y su propósito. Al abrir otro cuaderno, repetir sus
celdas 1–3: cada sesión tiene sus propias variables y dependencias.

**Ruta corta:** 00 → 01 → 02 → 04.
**Ruta de comparación para la tesis:** 00 → 01 → 02 → 03 → 04.

| Paso | Cuaderno | Celdas necesarias | Qué falta/producirá |
| --- | --- | --- | --- |
| 00 | `00_inicio_y_datasets.ipynb` | 1–4 | Conectar proyecto, instalar datos, preparar/verificar y mostrar pendientes. Sin entrenamiento. |
| 01 | `01_entrenar_clasificador.ipynb` | 1–6 | La celda 5 entrena clasificación PlantVillage si no existe una ejecución equivalente. No consulta test. |
| 02 | `02_entrenar_detector.ipynb` | 1–6 | La celda 5 entrena detección PlantDoc si falta. No consulta test. |
| 03 | `03_comparar_detectores.ipynb` | 1–6, opcional | Reutilizar YOLO26 de 02, entrenar las otras familias que falten y seleccionar con validación. |
| 04 | `04_evaluacion_y_exportacion.ipynb` | 1–6 | Recuperar pesos de disco y evaluar test una vez, guardar resumen y localizar los archivos de entrega. |

En 04, revisar la **celda 4** y cambiar `CONFIRMAR_MODELOS_FIJADOS=True` después de
fijar los modelos por validación. Luego ejecutar 5 y 6. Las celdas 7–9 son opcionales:
evaluar otras familias de 03, medir latencia CPU y exportar ONNX. Se dejan desactivadas.
Los números de esta guía son los encabezados «Celda 01», «Celda 02», etc.; no los
contadores de ejecuciones `[n]` que Colab cambia al ejecutar fuera de orden.

El [índice de cuadernos](../notebooks/README.md) enumera cada celda y su función.

## Estructura

```text
IOTtesis/
├── notebooks/
│   ├── README.md
│   ├── 00_inicio_y_datasets.ipynb           ← empezar aquí
│   ├── 01_entrenar_clasificador.ipynb       ← YOLO26n-cls / PlantVillage
│   ├── 02_entrenar_detector.ipynb           ← YOLO26n / PlantDoc
│   ├── 03_comparar_detectores.ipynb         ← opcional, antes del test
│   ├── 04_evaluacion_y_exportacion.ipynb    ← test final y entrega
│   ├── control/
│   │   └── 01_identificacion_pid_fopdt.ipynb
│   ├── riesgo/
│   │   └── 01_modelo_riesgo_demo.ipynb
│   └── archivo/                           ← versiones previas; no ejecutar
├── scripts/
│   ├── preparar_datasets_reales.py         ← adquisición/verificación
│   ├── entrenar_yolo26.py                  ← entrenamiento y métricas
│   ├── flujo_colab.py                     ← estado, reutilización y selección
│   ├── crear_notebooks_vision.py           ← genera los pasos 00–04
│   └── empaquetar_colab.py                 ← crea paquete local para Drive
├── data/
│   ├── raw/fuentes_reales/                 ← caché y atribución de fuentes
│   └── processed/
│       ├── papa_plantvillage_clasificacion/
│       └── papa_plantdoc_yolo/
├── runs/datasets_reales/                   ← aparece al entrenar
│   └── <ejecucion>/weights/best.pt
└── requirements-vision.txt
```

Servidor, firmware, web y datos conservan sus ubicaciones. No se borraron datasets,
resultados anteriores ni las salidas guardadas del cuaderno PID. Los cuadernos
antiguos se movieron al archivo para evitar iniciar entrenamientos duplicados.

## Estado local al organizar el proyecto

| Elemento | Estado comprobado |
| --- | --- |
| PlantVillage, clasificación de tres clases | Preparado: 2.152 imágenes; train 1.506, val 323, test 323. |
| PlantDoc, detección de dos enfermedades | Preparado: 219 imágenes; train 153, val 33, test 33. |
| Hashes, particiones y etiquetas | Verificados localmente con el preparador. |
| Cuadernos y scripts del flujo | Preparados. |
| Modelos entrenados | No se encontraron `experiment.json`/`best.pt` completos del flujo local. Faltan 01 y 02. |
| Comparación de familias | Pendiente; opcional, antes de evaluar test. |
| Evaluación final | Pendiente; se hace en 04. |
| Subida a Drive y ejecución de Colab | No acreditadas por los archivos locales. El paquete se crea en el equipo. |
| Riesgo fitopatológico real | Faltan series temporales/etiquetas reales y validación; el cuaderno existente es demostrativo. |
| Uso con imágenes propias e integración en servidor | Pendiente tras obtener los pesos. |

Para consultar el estado **actual**, ejecutar:

```bash
make colab-status
```

El comando inspecciona datos y artefactos, no entrena ni contacta el ESP32.
Detecta checkpoints corruptos o incompatibles y entrenamientos que dejaron
`last.pt` sin registro completo. No trata una simple ejecución de celdas como
prueba de que existe un modelo entrenado.

## Pasar el flujo y los datasets a Drive

Crear un ZIP local, con datos ya particionados y los scripts necesarios:

```bash
make colab-package
```

Salida: `data/processed/colab_yolo26_listo.zip`. No incluye `.env`, credenciales,
bases de datos, `.venv`, `runs` ni pesos. Conserva atribución de las fuentes.
No sube archivos automáticamente a Drive.

1. Subir `colab_yolo26_listo.zip` a **Mi unidad**, conservando ese nombre.
2. Abrir la copia local actualizada de `notebooks/00_inicio_y_datasets.ipynb`
   en Colab mediante **Archivo → Subir notebook**.
3. Ejecutar su **celda 1**. Monta Drive, busca el proyecto y, si falta o está
   incompleto, extrae el ZIP automáticamente en `Mi unidad/Tesis_IOT_Papa`.
   También admite el ZIP subido al almacenamiento temporal `/content`.
   No necesita importar scripts antes de extraerlos. Muestra `Proyecto:` con
   la ruta encontrada. Conserva los archivos de datos existentes; la celda 4
   debe verificarlos. No escribe en `runs/` ni en `.env`.
4. Continuar con las celdas 2–4 del mismo cuaderno. Las copias extraídas de los
   siguientes cuadernos quedan en `Tesis_IOT_Papa/notebooks/`. Seguir los pasos
   00–04 del índice nuevo.
5. Para 01–04, seleccionar una sesión con GPU T4. La ruta se configura con
   `IOTTESIS_ROOT` si se elige otra carpeta.

El código usa `DEVICE=0`, el índice de la GPU asignada. La celda 3 comprueba
CUDA y muestra el nombre real del dispositivo; no cambia automáticamente a CPU.
Si cambias el tipo de entorno o Colab reinicia, vuelve a ejecutar 1, 2 y 3 en
el cuaderno actual antes de la celda 4. Las celdas de configuración importan
`training_plan` explícitamente para evitar depender de un import de otra sesión.
Se conservan 50 épocas, lote 16 para clasificación y lote 8 para detección y
comparación, con las mismas particiones y resolución que el perfil anterior.

Si aparece `Image checksum differs`, los archivos no coinciden con el manifiesto.
Las celdas 4 de 00–03 comprueban el conjunto y restauran los archivos dañados desde
`colab_yolo26_listo.zip`. Primero verifican el contenido del ZIP y que coincidan la
revisión, los registros, las clases y las particiones. Guardan los originales y
`repair.json` en `data/repair_backups/`. Conservan el manifiesto, las particiones y
los entrenamientos. No se debe cambiar el hash registrado para aceptar otra imagen.

Si un cuaderno muestra el error antiguo «Copia el proyecto actualizado a Drive»,
abrir la versión actualizada: su primera celda incluye el instalador completo.
Abrir solo un `.ipynb` en Colab no copia la carpeta `scripts/` ni los datasets.
`scripts/` va en la raíz, junto a `notebooks/`, `data/` y `Makefile`.
No hay que importar nada manualmente antes de la primera celda.
Si ya existe una copia completa en otra ubicación, definir antes de la celda 1:

```python
import os
os.environ['IOTTESIS_ROOT'] = '/content/drive/MyDrive/MiProyecto'  # contiene scripts/
```

Si el ZIP está en otra carpeta o tiene otro nombre, definir `IOTTESIS_ZIP` con
su ruta completa. No es necesario definir estas variables con los nombres
predeterminados. Si no hay proyecto ni ZIP, el mensaje indica qué subir, la ruta
esperada y la carpeta que debe contener `scripts/`; no descarga código de otro origen.

También se pueden copiar las carpetas manualmente. Si no se copian los datasets,
00 los prepara desde sus fuentes; esto puede descargar una revisión distinta de
la original, que quedará registrada en su manifiesto. Copiar los preparados
conserva exactamente las particiones y procedencia locales ya verificadas.

## No repetir trabajo terminado

- 01, 02 y 03 usan `REENTRENAR=False` y `REANUDAR=True`. Buscan un experimento completo que coincida
  en datos, tarea, familia y configuración, y reutilizan su checkpoint.
- Cada entrenamiento usa el directorio real de Ultralytics, incluidos nombres
  incrementados. Un cuaderno nuevo no necesita las variables del anterior.
- Si Colab se corta y queda `last.pt`, la celda 5 comprueba la compatibilidad de
  tarea, familia, configuración y datos, guarda un respaldo y continúa desde
  la época guardada cuando el checkpoint conserva el optimizador.
- Si el entrenamiento ya terminó y falta `experiment.json`, recupera la
  validación y los metadatos de `best.pt` sin repetir el entrenamiento. Si hay
  varios checkpoints pendientes de la misma familia, exige revisar cuál usar.
- Los entrenamientos nuevos guardan su plan antes de entrenar. En las ejecuciones
  antiguas que no tienen una huella previa del dataset, la recuperación registra
  esa limitación: verificar los datos actuales no demuestra que sean idénticos
  a los datos de la sesión original.
- `REENTRENAR=True` permite iniciar otra ejecución deliberadamente y conserva
  la anterior; tiene prioridad sobre `REANUDAR=True`. Para continuar una ejecución
  interrumpida, mantener `REENTRENAR=False`.
- Los registros y la selección se pueden recuperar después de copiar el proyecto
  a otra raíz: se resuelven las rutas actuales y se comprueba el manifiesto/hash.
- 04 lee test guardado antes de evaluar; repetir una celda no repite el test.
- Los datos de test nunca se usan para elegir el ganador. Tras ver el test,
  no utilizarlo para una nueva búsqueda de parámetros.

## Otras ramas y trabajo que falta

**Control PID:** `notebooks/control/01_identificacion_pid_fopdt.ipynb` es
independiente. Ejecutar desde el inicio, en CPU si se desea. Si falta el CSV,
genera un escalón sintético. Para una sintonización física hacen falta mediciones
del equipo. Las figuras y tablas nuevas se guardan en `runs/control/`.

**Riesgo climático:** `notebooks/riesgo/01_modelo_riesgo_demo.ipynb` no es requisito
para entrenar YOLO. Viene con `EJECUTAR_DEMO_RIESGO=False`. Falta reunir la serie
climática, etiquetas de enfermedad independientes y alinear objetivos/horizontes
antes de una comparación válida. La etiqueta sintética actual deriva del umbral
del baseline: su puntuación perfecta no acredita predicción real.

**Datos adicionales:** faltan imágenes locales revisadas, anotaciones de lesión
si se quiere severidad, y datasets identificados de minadora, pulgón y polilla.
PlantDoc tiene cajas de hojas completas; PlantVillage tiene etiquetas de imagen.
No se transforman automáticamente en segmentación, conteo de insectos ni daño porcentual.

**Entrega:** después de 04, conservar `best.pt`, `best.metadata.json`,
`experiment.json`, `args.yaml`, `results.csv` y el resumen final. Configurar el
backend con el checkpoint adecuado y verificar imágenes propias. No copiar los
pesos al ESP32 ni activar control automático solo porque terminó un entrenamiento.

## Verificación de la reorganización

La suite pasó 90 pruebas, con una advertencia de deprecación de TestClient. Se
comprobó la numeración de las celdas, la recuperación tras copiar a otra raíz,
la reutilización de pesos, la detección de ejecuciones incompletas y la separación
del test. Los siete cuadernos activos compilan tras transformar las instrucciones
de IPython. El paquete ZIP se comprobó y se pudo extraer/verificar desde otra ruta.
Estas verificaciones no ejecutaron entrenamientos GPU ni publicaron datos al equipo.
El inicio se probó también sin scripts instalados, extrayendo el paquete anterior
y verificando sus dos datasets desde otra raíz. Se comprobó que conserva datos y
pesos existentes y rechaza rutas de extracción externas. El ZIP distribuye los
cuadernos sin salidas de ejecución y conserva intactos los resultados locales.
También se reprodujo con la imagen y el manifiesto de Drive el error de checksum
de PlantDoc: se restauró desde el ZIP y se verificaron las 219 imágenes. Esa prueba
se ejecutó en una carpeta temporal; la reparación de Drive la realiza su celda 4.
