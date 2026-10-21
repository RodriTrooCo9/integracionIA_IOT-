# Experimento E1: Comparativa de Arquitecturas de Detección de Objetos en Papa

## Objetivo
Evaluar y comparar el desempeño de arquitecturas de detección de una etapa (**YOLO11n**, **YOLOv8n**) frente a dos etapas (**Faster R-CNN ResNet-50**) para patologías foliares y plagas en papa bajo invernadero en La Paz.

## Resultados Cuantitativos
| Modelo | mAP@0.50 | mAP@0.50:0.95 | Precision | Recall | F1-Score | Latencia CPU [ms] | FPS CPU | Parámetros [M] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **YOLO11n (Ganador)** | **0.884** | **0.652** | **0.892** | **0.851** | **0.871** | **78.4 ms** | **12.8** | **2.6 M** |
| YOLOv8n (Línea Base) | 0.842 | 0.618 | 0.854 | 0.817 | 0.835 | 84.6 ms | 11.8 | 3.2 M |
| Faster R-CNN ResNet-50 | 0.891 | 0.668 | 0.901 | 0.853 | 0.876 | 820.5 ms | 1.2 | 41.5 M |

## Conclusión para la Memoria de Tesis
Aunque Faster R-CNN obtiene un margen marginal de $+0.7\%$ en mAP@0.50, su latencia en CPU es **10.5 veces mayor** ($820.5\text{ ms}$ vs $78.4\text{ ms}$) y su peso en disco es de $160\text{ MB}$ frente a $5.4\text{ MB}$. YOLO11n ofrece el mejor compromiso entre precisión y velocidad de inferencia en tiempo real para el servidor local sin GPU.
