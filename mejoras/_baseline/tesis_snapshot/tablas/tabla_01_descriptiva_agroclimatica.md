**Tabla 1**  
*Estadística descriptiva, verificación de supuestos y comparación no paramétrica de variables agroclimáticas simuladas según riesgo de tizón tardío (n = 2160 horas)*

| Variable | Sin riesgo (n=1238) M ± DE | Sin riesgo Mdn (RIQ) [Min–Max] | Con riesgo (n=922) M ± DE | Con riesgo Mdn (RIQ) [Min–Max] | Levene F (p) | Mann-Whitney U (Z) | p | r_rb / |r| |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Temperatura exterior (°C) | 10.64 ± 5.51 | 10.50 (10.51) [-0.98–21.17] | 10.89 ± 5.45 | 11.16 (10.38) [0.23–22.01] | 0.78 (.3768) | 586,521 (1.10) | .2704 | 0.028 / 0.024 |
| Temperatura interior (°C) | 18.08 ± 3.89 | 17.24 (7.46) [12.51–26.01] | 18.20 ± 3.93 | 17.54 (7.54) [12.49–26.36] | 0.15 (.7014) | 581,542 (0.75) | .4503 | 0.019 / 0.016 |
| Humedad relativa interior (%) | 66.93 ± 16.99 | 59.36 (33.71) [42.40–99.00] | 74.35 ± 18.90 | 83.90 (37.85) [41.80–99.00] | 15.47 (< .0001) | 716,170 (10.15) | < .0001 | 0.255 / 0.218 |
| Déficit de presión de vapor, VPD (kPa) | 0.78 ± 0.53 | 0.77 (1.03) [0.02–1.92] | 0.60 ± 0.54 | 0.27 (0.89) [0.02–1.98] | 2.84 (.0919) | 442,176 (-8.97) | < .0001 | -0.225 / 0.193 |
| Humedad volumétrica del suelo (%) | 28.54 ± 3.60 | 29.11 (6.74) [20.77–34.68] | 27.31 ± 3.55 | 26.83 (6.29) [20.40–35.48] | 1.34 (.2465) | 458,492 (-7.83) | < .0001 | -0.197 / 0.168 |
| Hoja húmeda continua, LWH (h) | 0.38 ± 1.92 | 0.00 (0.00) [0.00–15.00] | 7.56 ± 15.01 | 0.00 (6.00) [0.00–72.00] | 276.95 (< .0001) | 721,276 (16.33) | < .0001 | 0.264 / 0.351 |
| Unidades de tizón 7 días, BU (pts) | 0.19 ± 1.30 | 0.00 (0.00) [0.00–13.00] | 155.54 ± 73.17 | 164.00 (106.75) [14.00–264.00] | 2241.74 (< .0001) | 1,141,436 (43.78) | < .0001 | 1.000 / 0.942 |

*Nota.* Datos simulados horarios (N = 2160, 90 días; scripts/generar_dataset_agroclimatico.py). Ninguna variable cumplió normalidad conjunta en Shapiro-Wilk (todos p <= .020) y/o homocedasticidad en Levene (excepto temp_exterior_c en Levene p = 0.3768, pero no normal en Shapiro-Wilk p < .001), por lo que se aplicó la prueba U de Mann-Whitney bilateral (N = 2160). M = media; DE = desviación estándar muestral; Mdn = mediana; RIQ = rango intercuartílico; r_rb = correlación biserial de rangos (positivo indica valores mayores en riesgo = 1); |r| = tamaño de efecto de Rosenthal (|Z|/sqrt(N)). Correlaciones de Spearman (N = 2160): VPD vs. HR rho = -0.9887 (p < .001); VPD vs. LWH rho = -0.5970 (p < .001); VPD vs. Blight Units rho = -0.1390 (p = 8.643e-11); LWH vs. Blight Units rho = 0.2622 (p < .001); Blight Units vs. Riesgo GT rho = 0.9421 (p < .001).
