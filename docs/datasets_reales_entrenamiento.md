# Datos reales para entrenar el piloto foliar

El preparador descarga datos reales de fuentes públicas. No usa el generador de
dibujos de `scripts/preparar_dataset_vision.py` ni su salida `data/dataset_yolo`.
No se ha entrenado todavía ningún modelo con estos nuevos conjuntos.

## Resultado de la preparación del 28 de octubre de 2026

| Conjunto | Train | Val | Test | Total |
|---|---:|---:|---:|---:|
| PlantVillage, clasificación de tres clases | 1.506 | 323 | 323 | 2.152 |
| PlantDoc, detección de dos enfermedades | 153 | 33 | 33 | 219 |

En PlantDoc una imagen puede contener ambas clases; por eso los conteos por clase
pueden sumar más que el número de imágenes. Se conservaron 569 cajas de hojas:
250 de tizón tardío y 319 de tizón temprano. Se excluyeron dos imágenes por ausencia
en la fuente o anotaciones de otros cultivos y tres por sanidad no confirmada.

Revisiones de origen:

- PlantVillage: `7f7ecc7e1eaca78107e3affe7cb5abd9427e139a`.
- PlantDoc: `4730a233a555b30ee98e0879c63ad25d82407455`.

## Preparación local

Desde la raíz del repositorio:

```bash
python -m pip install -r requirements-datasets.txt
python scripts/preparar_datasets_reales.py --source all
python scripts/preparar_datasets_reales.py --source all --verify
```

El primer comando de preparación descarga y comprueba imágenes. Las descargas
válidas se reutilizan si hay una interrupción; una imagen corrupta o una descarga
fallida produce un error, nunca un reemplazo sintético. Las imágenes ausentes del
árbol del proveedor y las escenas con anotaciones de otros cultivos se excluyen
de PlantDoc con su motivo en el manifiesto.

La salida se construye en un directorio temporal y se publica tras validarla.
Si ya existe, solo se valida: no se borra ni se sobrescribe el dataset.
Para comparar otra versión de la fuente, usa otra raíz con `--root` y conserva
los manifiestos anteriores.

## Conjuntos separados por tarea

| Fuente | Salida dentro del proyecto | Uso |
|---|---|---|
| [PlantVillage](https://github.com/spMohanty/PlantVillage-Dataset) | `data/processed/papa_plantvillage_clasificacion/` | Clasificación de la imagen de una hoja. |
| [PlantDoc Object Detection](https://github.com/pratikkayal/PlantDoc-Object-Detection-Dataset) | `data/processed/papa_plantdoc_yolo/` | Detección de hojas con dos clases de enfermedad; incluye `data.yaml`. |

PlantVillage aporta 2.152 imágenes: 1.000 de tizón tardío, 1.000 de tizón temprano
y 152 de hoja sana. Se conservan solo las imágenes originales de `raw/color`.
No se descargan versiones grises o segmentadas para contarlas como nuevas muestras.
No se fabrican cajas a partir de etiquetas de clasificación.

PlantDoc aporta cajas originales de hojas. El mapeo es:

| ID del detector | Etiqueta original | Clase del piloto |
|---|---|---|
| 0 | Potato leaf late blight | tizon_tardio |
| 1 | Potato leaf early blight | tizon_temprano |
| — | Potato leaf | Excluida: sanidad no confirmada |

La etiqueta genérica `Potato leaf` no confirma que la hoja esté sana. Las tres
imágenes de esa categoría se excluyen del piloto de detección. Las etiquetas de
enfermedad del proveedor también necesitan revisión agronómica.
**Las cajas de hojas no representan áreas de lesión: no sirven para calcular
porcentaje de severidad foliar.** El clasificador aprende su orden de etiquetas
desde las carpetas; consultar `model.names`, no asumir el orden numérico del detector.

## Rutas correctas en Jupyter y Colab

Abre `notebooks/02_curaduria_dataset_vision.ipynb` y ejecuta sus celdas en orden.
La Celda 2 localiza la raíz que contiene `scripts/preparar_datasets_reales.py`;
la Celda 6 ejecuta la descarga y la preparación completa. No crea una carpeta
vacía en `notebooks/data` ni supone que estás en `/content`.

En Colab, copia o clona el proyecto primero. Si está en Google Drive, monta Drive
y configura antes de la Celda 2:

```python
import os
os.environ['IOTTESIS_ROOT'] = '/content/drive/MyDrive/Tesis_IOT_Papa'
```

La ruta debe contener el proyecto y su carpeta `scripts/`, no solo imágenes.
Al copiar el dataset a otro ordenador, los cuadernos actualizan `path` de su YAML
antes de utilizarlo. `data/data.yaml` conserva la configuración previa de seis
clases; **no es el YAML de este piloto**.

## Entrenamiento

Abre `notebooks/05_entrenamiento_datasets_reales.ipynb`:

1. Ejecuta instalación y preparación/verificación.
2. Sección A: `yolo11n-cls.pt` aprende clasificación con PlantVillage.
3. Sección B: `yolo11n.pt` aprende detección de hojas con dos clases de enfermedad de PlantDoc.
4. Evalúa cada modelo en su test y conserva resultados, configuración y pesos en
   `runs/datasets_reales/`.

Las tareas son independientes. El cuaderno de comparación anterior de seis clases
no es la entrada de entrenamiento de estos datos. El servidor actual requiere
una adaptación explícita antes de usar cualquiera de estos pesos: no sustituir
automáticamente el modelo de lesiones/insectos por un clasificador o detector de hojas.

## Trazabilidad y límites de evaluación

- Cada salida incluye `manifest.json`: revisión Git, URLs, hashes de píxeles,
  grupos, partición y etiquetas. La caché en `data/raw/fuentes_reales/` conserva
  textos de licencia, README y cita que publica cada repositorio.
- `report.json` registra conteos por clase y partición. `--verify` vuelve a leer
  las imágenes, comprueba hashes, cajas y presencia de todas las clases declaradas.
- Se dividen grupos aproximadamente 70/15/15 con semilla 42. Duplicados exactos
  de píxeles y grupos de nombre de origen no cruzan particiones.
- Esto no acredita separación por planta física ni detecta todos los duplicados
  visualmente similares. Hace falta revisión manual y un test propio del invernadero.
- PlantDoc se redistribuye combinando TRAIN y TEST originales para disponer de
  las dos clases de enfermedad en cada partición. Por ello es un piloto nuevo y sus métricas
  no son el benchmark oficial PlantDoc.
- Las imágenes públicas conservan las condiciones del proveedor; guardar la
  atribución y revisar sus términos antes de redistribuirlas.

## Incorporación posterior de insectos

Las clases minadora, pulgón y polilla no se incluyen ni se simulan. Para pulgones
puede investigarse [Black Aphids Glue Paper Traps](https://zenodo.org/records/14097660),
verificando especie y condiciones. No asumir que representa *Myzus persicae*.
Minadora y polilla requieren imágenes identificadas de las especies objetivo.
El HSV del cuaderno solo propone regiones para revisión, sin asignar una especie
por el tamaño del contorno. No se inicia un entrenamiento de seis clases sin
ejemplos y anotaciones revisadas de las seis.
