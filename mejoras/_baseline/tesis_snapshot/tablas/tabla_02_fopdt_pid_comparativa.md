**Tabla 2**  
*Desempeño comparativo de sintonizaciones PID frente al control On/Off y ajuste del modelo FOPDT simulado*

| Controlador / Método | Kp / Ki / Kd | tr (s) | ts (s) | Mp (%) | e_ss (°C) | IAE (°C·s) | ITAE (°C·s²) | TV_u (%) | Delta Optuna (IAE / ITAE / TV_u) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Ziegler-Nichols | 53.37 / 0.8006 / 889.53 | 225.0 | 317.0 | 1.28 | 2.63e-08 | 1756.14 | 177,436.2 | 210.74 | +2.52% / +11.13% / -27.46% |
| Cohen-Coon | 60.83 / 0.7838 / 719.36 | 225.0 | 324.0 | 0.21 | 4.57e-07 | 1752.41 | 175,436.4 | 211.74 | +2.74% / +12.40% / -27.80% |
| IMC | 29.83 / 0.1149 / 465.23 | 297.0 | 733.0 | 0.00 | 0.0183 | 2094.20 | 353,032.5 | 149.48 | -14.03% / -44.14% / +2.26% |
| Optuna (Óptimo) | 15.93 / 0.1359 / 1.57 | 230.0 | 346.0 | 1.61 | 6.48e-05 | 1800.35 | 197,189.0 | 152.87 | Ref. / Ref. / Ref. |
| Control On/Off (±0.5°C) | 0.00 / 0.0000 / 0.00 | 225.0 | No asienta | 9.27 | 0.7837 | 2566.79 | 883,677.7 | 1900.00 | -29.86% / -77.69% / -91.95% |

*Nota.* Datos provenientes de simulación física/matemática reproducible (scripts/ejecutar_fase2_identificacion_pid.py sobre data/synthetic/prueba_escalon_fopdt.csv y data/synthetic/metricas_comparativa_pid_onoff.csv). Identificación FOPDT (N = 1800, escalón u = 70% en t = 120 s): K = 0.1639 ± 0.00006 °C/%, tau = 242.96 ± 0.59 s, theta = 33.33 ± 0.33 s; R² = 0.9990, RMSE = 0.1178 °C, MAE = 0.0962 °C. Diagnóstico de residuos (e = y - y_hat): M = 0.00087 °C, DE = 0.1179 °C, Shapiro-Wilk W = 0.9967 (p = 0.0007), Durbin-Watson = 0.9601 (autocorrelación lag-1 r = 0.5196, explicada por la componente sinusoidal de viento T = 600 s). Delta Optuna = ((Optuna - Método) / Método) × 100; valores negativos indican reducción de error o esfuerzo respecto al método comparado. Control On/Off (±0.5 °C) presenta ciclo límite sostenido (ts no asienta; Mp = 9.27%, ess = 0.7837 °C).
