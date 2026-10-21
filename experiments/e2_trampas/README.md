# Experimento E2: Detección de Plagas Diminutas en Trampas Amarillas con SAHI

## Objetivo
Evaluar el impacto de **SAHI (Slicing Aided Hyper Inference)** para la detección de insectos pequeños (pulgones y mosca minadora, $< 25\times 25\text{ px}$) adheridos a láminas adhesivas amarillas.

## Configuración Óptima de SAHI
- Tamaño de corte (*Slice Size*): $320 \times 320\text{ píxeles}$
- Razón de solapamiento (*Overlap Ratio*): $0.20$ ($20\%$ en horizontal y vertical)
- Algoritmo de post-procesamiento: NMS con umbral IoU de $0.45$

## Resultados Comparativos
| Configuración | Recall Mosca Minadora | Recall Pulgón | Recall Polilla Papa | Recall Promedio | mAP@0.50 | Latencia CPU [ms] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Inferencia Estándar (Sin SAHI) | 0.650 | 0.580 | 0.770 | 0.668 | 0.712 | 78.4 ms |
| **Inferencia con SAHI ⭐** | **0.830** | **0.810** | **0.850** | **0.829** | **0.856** | **268.0 ms** |
| **Mejora Relativa** | **+27.7%** | **+39.7%** | **+10.4%** | **+24.1%** | **+20.2%** | — |

## Conclusión
La inferencia estándar pierde casi la mitad de los pulgones debido a la pérdida de resolución espacial en el stride de la red ($32\times$). Con SAHI, la sensibilidad para insectos diminutos se eleva del $58\%$ al $81\%$ ($+39.7\%$ de mejora) con una latencia de $268\text{ ms}$, compatible con el ciclo de escaneo periódico del servidor.
