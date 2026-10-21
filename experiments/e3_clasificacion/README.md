# Experimento E3: Clasificación Foliar con MobileNetV3 (Transfer Learning)

## Objetivo
Evaluar una red neuronal convolucional ultra-ligera (**MobileNetV3-Small**) para la clasificación directa de hojas (*Tizón Tardío* vs *Tizón Temprano* vs *Hoja Sana*) como modelo de contingencia para nodos de ultra-bajo consumo.

## Resultados
- **Exactitud Global (Accuracy):** $94.2\%$
- **F1-Score Ponderado:** $0.941$
- **Latencia de Inferencia en CPU:** **$22.3\text{ ms}$** ($44.8\text{ FPS}$)
- **Parámetros:** $1.5\text{ M}$
- **Tamaño en Disco:** $3.2\text{ MB}$

## Conclusión
MobileNetV3-Small es idóneo para clasificación binaria/terciaria en dispositivos borde (como Raspberry Pi o SBC con procesador ARM), mientras que YOLO11n se mantiene como el modelo principal debido a su capacidad de localizar múltiples lesiones y delimitar severidad foliar.
