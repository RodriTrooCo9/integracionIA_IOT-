**Tabla 4**  
*Evaluación comparativa de modelos de riesgo fitopatológico en conjunto de prueba temporal simulado (n = 432 horas)*

| Modelo | ROC-AUC | PR-AUC | Brier Score | F1-Score | Latencia CPU (ms) | Seleccionado |
| --- | --- | --- | --- | --- | --- | --- |
| BlightManager (Wallin 1962) | 1.0 | 1.0 | 0.0105 | 0.9712 | 0.0 | No (Línea Base) |
| Random Forest (Calibrado) | 0.6856 | 0.7783 | 0.2099 | 0.632 | 0.013 | No |
| XGBoost (Calibrado) | 0.7123 | 0.7641 | 0.1878 | 0.6497 | 0.038 | SI (Ganador) |
| Support Vector Machine (RBF) | 0.7358 | 0.8089 | 0.2037 | 0.6402 | 0.026 | No |
| Bioclimatic LSTM (PyTorch) | 0.6656 | 0.7931 | 0.2649 | 0.6629 | 0.019 | No (Complejidad) |

*Nota.* Evaluación sobre partición temporal estricta de la simulación agroclimática de 90 días (Train = 1296 h [462 pos., 35.6%]; Val = 432 h [246 pos., 56.9%]; Test = 432 h [214 pos., 49.5%]). BlightManager (Wallin 1962) obtiene ROC-AUC = 1.0000 y PR-AUC = 1.0000 porque evalúa directamente blight_units_7d, variable con la cual se definió la etiqueta objetivo (riesgo_infeccion_gt = 1 si blight_units_7d >= 14.0; concordancia = 100.0%). Los modelos de aprendizaje automático (Random Forest, XGBoost, SVM RBF y LSTM) predicen el riesgo usando exclusivamente 24 variables de telemetría y ventanas móviles (sin incluir blight_units_7d). Entre los modelos ML, XGBoost (calibración isotónica) obtiene el menor Brier Score (0.1878) con latencia de 0.038 ms en CPU, mientras SVM RBF logra mayor discriminación ROC-AUC (0.7358) y PR-AUC (0.8089).
