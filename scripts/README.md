# Entradas del flujo Colab

| Script | Uso |
| --- | --- |
| `iniciar_colab.py` | Buscar la raíz o extraer el ZIP de Drive; su código se incluye en la primera celda para funcionar antes de copiar scripts. |
| `reparar_dataset_colab.py` | Restaurar archivos dañados desde el ZIP compatible; respalda originales y conserva manifiesto y particiones. Incluido en las celdas de datos/configuración. |
| `flujo_colab.py` | Estado local, recuperación de experimentos, selección por validación y test sin repeticiones. |
| `preparar_datasets_reales.py` | Preparar/verificar fuentes reales. Conserva manifiestos y particiones. |
| `entrenar_yolo26.py` | Entrenar por terminal o desde los cuadernos; no ejecuta test salvo petición explícita. |
| `crear_notebooks_vision.py` | Generar los pasos actuales 00–04, sin entrenamiento. Regenerar descarta sus salidas de celdas. |
| `empaquetar_colab.py` | ZIP local del flujo y los datasets verificados para copiar a Drive. |

Los comandos `crear_notebook_fase2.py` y `crear_notebook_fase5.py` generan las
ramas control/riesgo; `crear_notebook_fase3.py` ahora genera 00 y
`crear_notebook_fase4.py` genera 03. No reintroducen los nombres antiguos en la raíz.

`preparar_dataset_vision.py` y otros scripts experimentales previos se conservan
por compatibilidad. El generador de dibujos sintéticos no forma parte del flujo
real y no debe ejecutarse sobre un dataset valioso.
