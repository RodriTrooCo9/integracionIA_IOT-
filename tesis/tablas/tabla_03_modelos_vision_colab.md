**Tabla 3**  
*Resultados reales de modelos de visión por computadora entrenados en Google Colab sobre datasets públicos PlantVillage y PlantDoc*

| Experimento Colab | Dataset (Real Público) | Épocas (CSV/Plan) | Validación (Best) | Test Único (Best) | Dinámica Últ. Épocas (M ± DE) | Peso (MB) |
| --- | --- | --- | --- | --- | --- | --- |
| yolo26n_plantvillage_classify | PlantVillage (2,152 imgs; 3 clases) | 25 / 50 | Acc@1 = 1.0000 | Acc@1 = 1.0000 | Acc@1 (21–25): 0.9944 ± 0.0034 | 3.04 |
| yolo26n_plantdoc_detect | PlantDoc (219 imgs; 569 cajas; 2 clases) | 40 / 50 | P=0.4690, R=0.7453, mAP50=0.6343, mAP50-95=0.4699 | P=0.4551, R=0.5985, mAP50=0.4926, mAP50-95=0.3216 | mAP50 (31–40): 0.5597 ± 0.0089; mAP50-95: 0.4151 ± 0.0118 | 5.18 |
| yolo11n_plantdoc_detect | PlantDoc (219 imgs; 569 cajas; 2 clases) | 43 / 50 | P=0.5566, R=0.5808, mAP50=0.5918, mAP50-95=0.3981 | No ejecutado (test: null) | mAP50 (31–40): 0.5045 ± 0.0208; mAP50-95: 0.3543 ± 0.0194 | 5.23 |

*Nota.* Pilotos reales entrenados en Google Colab GPU (2026-11-04; verificados en data/models/entrenados_colab/verificacion.json). Comparativa estadística por época sobre 40 épocas comunes (1–40) en validación de PlantDoc (YOLO26n vs. YOLO11n; prueba pareada de Wilcoxon de rangos con signo, N = 40 pares): mAP@0.50: W = 104.0, Z = 4.11, p = 3.905e-05, r = 0.650; mAP@0.50:0.95: W = 93.0, Z = 4.26, p = 2.036e-05, r = 0.674; Precision: W = 195.0, Z = 2.89, p = 0.0039, r = 0.457; Recall: W = 236.0, Z = 2.34, p = 0.0193, r = 0.370. Esta prueba pareada evalúa la dinámica de convergencia en validación (no equivale a inferencia sobre imágenes independientes de prueba); el test único independiente de YOLO26n (n = 33 imágenes) obtuvo mAP@0.50 = 0.4926, mAP@0.50:0.95 = 0.3216, Precision = 0.4551, Recall = 0.5985. Las cajas de PlantDoc delimitan hojas completas (no lesiones) y ambos datasets públicos no constituyen validación en el invernadero de La Paz.
