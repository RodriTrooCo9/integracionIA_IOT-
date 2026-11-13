# Informe de Análisis Estadístico y Validación Cuantitativa (Agente 5 – Analista de Datos)

**Repositorio:** `/home/rodrigo/Desktop/IOTtesis`  
**Script reproducible:** `/home/rodrigo/Desktop/IOTtesis/tesis/scripts/analisis_estadistico_tesis.py`  
**Entorno de ejecución:** `.venv/bin/python` (Python 3.14, `numpy 2.5.4`, `pandas 3.0.6`, `scipy 1.18.1`, `matplotlib 3.11.2`)  
**Fecha de ejecución verificada:** 2026-11-13  

> [ADVERTENCIA] **Principio de transparencia metodológica:** En este informe se distinguen de manera estricta tres planos probatorios:  
> 1. **Pilotos reales entrenados en Google Colab GPU sobre datasets públicos curados** (`data/models/entrenados_colab/*`, `data/processed/*`).  
> 2. **Simulaciones físicas y matemáticas reproducibles** (`data/synthetic/prueba_escalon_fopdt.csv`, `metricas_comparativa_pid_onoff.csv`, `dataset_agroclimatico_invernadero.csv`, `metricas_experimentos_fase5_riesgo.csv`).  
> 3. **Datos de referencia/diseño y verificación de artefactos de software/firmware** (`data/synthetic/metricas_experimentos_e1_e2_e3.csv`, `data/dataset_yolo/`, `firmware.bin`, SQLite WAL, API/Web y suite Pytest), los cuales **no** constituyen mediciones físicas en invernadero real de La Paz.

---

## 1. Análisis de Datos Agroclimáticos Simulados (n = 2160 horas)

**Fuente analizada:** `data/synthetic/dataset_agroclimatico_invernadero.csv` (2160 registros horarios equivalentes a 90 días; generador biofísico en `scripts/generar_dataset_agroclimatico.py`).  
**Estratificación por variable objetivo:** `riesgo_infeccion_gt = 0` (riesgo bajo/moderado: $n_0 = 1238$ horas; $57.31\%$) frente a `riesgo_infeccion_gt = 1` (riesgo alto/crítico: $n_1 = 922$ horas; $42.69\%$).

### 1.1 Verificación de supuestos estadísticos (normalidad y homocedasticidad)

Se evaluó la normalidad univariada en ambos estratos mediante la prueba de **Shapiro-Wilk** ($W$) y la prueba ómnibus de **D'Agostino-Pearson** ($K^2$), y la homogeneidad de varianzas mediante la prueba robusta de **Levene** centrada en la mediana (Brown-Forsythe).

- **Normalidad:** Ninguna de las 7 variables cumplió el supuesto de normalidad conjunta en ambos estratos (Shapiro-Wilk $p \le 1.503 \times 10^{-18}$ en todos los casos; D'Agostino-Pearson $p \le 1.339 \times 10^{-55}$). En particular, `lwh_continuo_horas` ($W_0 = 0.2017$, $W_1 = 0.5797$) y `blight_units_7d` ($W_0 = 0.1310$, $W_1 = 0.9421$) presentan fuerte asimetría positiva e inflación de ceros en el estrato sin riesgo, mientras las variables térmicas e higrométricas muestran multimodalidad diurna/nocturna.
- **Homocedasticidad:** Se rechazó la igualdad de varianzas en `hum_interior_pct` ($F(1, 2158) = 15.47, p = 8.666 \times 10^{-5}$), `lwh_continuo_horas` ($F(1, 2158) = 276.95, p = 1.331 \times 10^{-58}$) y `blight_units_7d` ($F(1, 2158) = 2241.74, p < .0001$). Aunque `temp_exterior_c` ($F = 0.78, p = .3768$), `temp_interior_c` ($F = 0.15, p = .7014$), `vpd_kpa` ($F = 2.84, p = .0919$) y `hum_suelo_pct` ($F = 1.34, p = .2465$) mostraron varianzas comparables entre estratos, la violación sistemática de la normalidad justificó la selección uniforme de la prueba no paramétrica **U de Mann-Whitney bilateral** ($N = 2160$), complementada con la correlación biserial de rangos ($r_{rb}$) y el tamaño de efecto de Rosenthal ($|r| = |Z|/\sqrt{N}$).

### 1.2 Estadística descriptiva global, estratificada y contraste comparativo

La **Tabla 1** completa se exportó en `/home/rodrigo/Desktop/IOTtesis/tesis/tablas/tabla_01_descriptiva_agroclimatica.csv` y `/home/rodrigo/Desktop/IOTtesis/tesis/tablas/tabla_01_descriptiva_agroclimatica.md`. El resumen cuantitativo exacto es el siguiente:

1. **`temp_exterior_c` (°C):** Global $M = 10.75 \pm 5.49$, $\text{Mdn} = 10.89$ ($\text{RIQ} = 10.46$, rango $[-0.98, 22.01]$). Sin riesgo: $M = 10.64 \pm 5.51$, $\text{Mdn} = 10.51$ ($\text{RIQ} = 10.51$); con riesgo: $M = 10.89 \pm 5.45$, $\text{Mdn} = 11.17$ ($\text{RIQ} = 10.38$). Sin diferencia estadísticamente significativa ($U = 586{,}521.0, Z = 1.10, p = .2704, r_{rb} = 0.028, |r| = 0.024$).
2. **`temp_interior_c` (°C):** Global $M = 18.13 \pm 3.91$, $\text{Mdn} = 17.38$ ($\text{RIQ} = 7.50$, rango $[12.49, 26.36]$). Sin riesgo: $M = 18.08 \pm 3.89$, $\text{Mdn} = 17.25$ ($\text{RIQ} = 7.46$); con riesgo: $M = 18.20 \pm 3.93$, $\text{Mdn} = 17.54$ ($\text{RIQ} = 7.54$). Sin diferencia significativa ($U = 581{,}542.0, Z = 0.75, p = .4503, r_{rb} = 0.019, |r| = 0.016$).
3. **`hum_interior_pct` (%):** Global $M = 70.10 \pm 18.20$, $\text{Mdn} = 62.43$ ($\text{RIQ} = 34.54$, rango $[41.80, 99.00]$). El estrato con riesgo presenta humedad significativamente mayor ($\text{Mdn} = 83.90, \text{RIQ} = 37.85; M = 74.35 \pm 18.90$) frente al estrato sin riesgo ($\text{Mdn} = 59.37, \text{RIQ} = 33.72; M = 66.93 \pm 16.99$), con $U = 716{,}169.5, Z = 10.15, p = 3.486 \times 10^{-24}$ y tamaño de efecto pequeño-moderado ($r_{rb} = 0.255, |r| = 0.218$; Welch $t = 9.42, p = 1.285 \times 10^{-20}$).
4. **`vpd_kpa` (kPa):** Global $M = 0.70 \pm 0.54$, $\text{Mdn} = 0.66$ ($\text{RIQ} = 0.99$, rango $[0.016, 1.975]$). Durante las horas de riesgo, el VPD desciende significativamente ($\text{Mdn} = 0.27, \text{RIQ} = 0.89; M = 0.60 \pm 0.54$) respecto a las horas sin riesgo ($\text{Mdn} = 0.77, \text{RIQ} = 1.03; M = 0.78 \pm 0.53$), $U = 442{,}175.5, Z = -8.97, p = 3.084 \times 10^{-19}, r_{rb} = -0.225, |r| = 0.193$.
5. **`hum_suelo_pct` (%):** Global $M = 28.02 \pm 3.63$, $\text{Mdn} = 28.05$ ($\text{RIQ} = 6.90$, rango $[20.40, 35.48]$). Se observa menor humedad edáfica en el estrato de riesgo ($\text{Mdn} = 26.83, \text{RIQ} = 6.29; M = 27.31 \pm 3.55$) frente al estrato sin riesgo ($\text{Mdn} = 29.11, \text{RIQ} = 6.74; M = 28.54 \pm 3.60$), $U = 458{,}492.0, Z = -7.83, p = 4.972 \times 10^{-15}, r_{rb} = -0.197, |r| = 0.168$. [NOTA] Este desfase obedece a la fase sinusoidal del riego semanal de 7 días frente a los 4 temporales sintéticos definidos en los días 18–22, 38–41, 58–62 y 75–78 del generador.
6. **`lwh_continuo_horas` (h):** Global $M = 3.45 \pm 10.53$, $\text{Mdn} = 0.00$ ($\text{RIQ} = 0.00$, rango $[0.00, 72.00]$). En el estrato con riesgo el percentil 75 asciende a $6.00\text{ h}$ ($M = 7.56 \pm 15.01$, máx. $72.00\text{ h}$) frente a $M = 0.38 \pm 1.92$ (máx. $15.00\text{ h}$) en el estrato sin riesgo ($U = 721{,}276.5, Z = 16.33, p = 6.054 \times 10^{-60}, r_{rb} = 0.264, |r| = 0.351$, efecto moderado).
7. **`blight_units_7d` (pts):** Global $M = 66.50 \pm 90.51$, $\text{Mdn} = 0.00$ ($\text{RIQ} = 160.00$, rango $[0.00, 264.00]$). Separa de forma determinística ambos estratos ($U = 1{,}141{,}436.0, Z = 43.78, p < .0001, r_{rb} = 1.000, |r| = 0.942$), con $\text{Mdn} = 0.00$ (máx. $13.00$) en riesgo $0$ y $\text{Mdn} = 164.00$ ($\text{RIQ} = 106.75$, mín. $14.00$) en riesgo $1$.

### 1.3 Correlaciones de Spearman ($N = 2160$)

Las correlaciones monotónicas no paramétricas de Spearman ($\rho$, $N = 2160$) evidencian el acoplamiento psicrométrico del modelo:
- `vpd_kpa` vs. `hum_interior_pct`: $\rho = -0.9887$ ($p < .0001$; relación casi determinística inversa a temperatura regulada).
- `vpd_kpa` vs. `lwh_continuo_horas`: $\rho = -0.5970$ ($p = 8.956 \times 10^{-209}$).
- `hum_interior_pct` vs. `lwh_continuo_horas`: $\rho = 0.6368$ ($p = 5.441 \times 10^{-246}$).
- `lwh_continuo_horas` vs. `blight_units_7d`: $\rho = 0.2622$ ($p = 2.694 \times 10^{-35}$); vs. `riesgo_infeccion_gt`: $\rho = 0.3514$ ($p = 8.123 \times 10^{-64}$).
- `hum_interior_pct` vs. `blight_units_7d`: $\rho = 0.1592$ ($p = 1.007 \times 10^{-13}$); vs. `riesgo_infeccion_gt`: $\rho = 0.2183$ ($p = 1.006 \times 10^{-24}$).
- `vpd_kpa` vs. `blight_units_7d`: $\rho = -0.1390$ ($p = 8.643 \times 10^{-11}$); vs. `riesgo_infeccion_gt`: $\rho = -0.1930$ ($p = 1.459 \times 10^{-19}$).
- `blight_units_7d` vs. `riesgo_infeccion_gt`: $\rho = 0.9421$ ($p < .0001$).

La distribución comparativa por estratos se ilustra en `/home/rodrigo/Desktop/IOTtesis/tesis/figuras/fig_est_boxplots_vpd_riesgo.png`.

---

## 2. Análisis del Modelo FOPDT y Comparativa PID vs. On/Off (Simulación)

**Fuentes analizadas:** `data/synthetic/prueba_escalon_fopdt.csv` ($N = 1800$ muestras a $1\text{ Hz}$, $0$–$1799\text{ s}$) y `data/synthetic/metricas_comparativa_pid_onoff.csv` (reproducido por `scripts/ejecutar_fase2_identificacion_pid.py`).

### 2.1 Identificación FOPDT y diagnóstico estadístico de residuos

Al replicar el ajuste por mínimos cuadrados no lineales (`scipy.optimize.curve_fit`) con escalón $\Delta u = 70\%$ en $t = 120\text{ s}$ ($T_0 = 8.498^\circ\text{C}$ promedio pre-escalón):
- **Parámetros identificados ($\pm$ error estándar asintótico):** $K = 0.1639 \pm 0.00006\,^\circ\text{C}/\%$, $\tau = 242.96 \pm 0.59\text{ s}$ ($4.05\text{ min}$) y $\theta = 33.33 \pm 0.33\text{ s}$ (relación $\theta/\tau = 0.137$, proceso dominado por retardo moderado-bajo controlable por PID). Estos valores recuperan con alta fidelidad los parámetros teóricos de `generar_datos_escalon.py` ($K_{\text{real}} = 0.165$, $\tau_{\text{real}} = 240.0\text{ s}$, $\theta_{\text{real}} = 35.0\text{ s}$), con desviación frente a `temperatura_ideal_c` de $\text{RMSE} = 0.0324\,^\circ\text{C}$ y $\text{MAE} = 0.0231\,^\circ\text{C}$.
- **Bondad de ajuste global frente a `temperatura_medida_c`:** $R^2 = 0.998989$ ($0.9990$), $\text{RMSE} = 0.1178\,^\circ\text{C}$, $\text{MAE} = 0.0962\,^\circ\text{C}$ y error absoluto máximo $\text{MaxAE} = 0.3467\,^\circ\text{C}$.
- **Análisis de residuos ($e_i = y_i - \hat{y}_i$, $N = 1800$):** Media $M = 0.00087\,^\circ\text{C}$, $\text{DE} = 0.1179\,^\circ\text{C}$, $\text{Mdn} = -0.0002\,^\circ\text{C}$, $\text{RIQ} = 0.1732\,^\circ\text{C}$ (rango $[-0.326, 0.347]\,^\circ\text{C}$).
- **Supuestos de los residuos:**
  - *Normalidad:* Aunque visualmente simétricos y centrados en cero, Shapiro-Wilk ($W = 0.9967, p = .0007$) y D'Agostino-Pearson ($K^2 = 21.47, p < .0001$) detectan desviación leve por colas ligeramente platicúrticas al superponer una onda determinística a ruido gaussiano ($\sigma = 0.08\,^\circ\text{C}$).
  - *Independencia:* El estadístico de Durbin-Watson fue $\text{DW} = 0.9601$ (muy inferior a $2.0$) y la autocorrelación de primer orden alcanzó $r_1 = 0.5196$ ($p = 5.553 \times 10^{-125}$). Esto confirma autocorrelación positiva estructurada, explicada directamente por la perturbación sinusoidal de viento ($T = 600\text{ s} = 10\text{ min}$) incorporada en `generar_datos_escalon.py`.

El diagnóstico completo en cuatro paneles (serie temporal, histograma, gráfico Q-Q normal y ACF lags 1–30 s) se encuentra en `/home/rodrigo/Desktop/IOTtesis/tesis/figuras/fig_est_residuos_fopdt.png`.

### 2.2 Comparativa cuantitativa de Optuna frente a controladores clásicos y On/Off

De `metricas_comparativa_pid_onoff.csv` y `/home/rodrigo/Desktop/IOTtesis/tesis/tablas/tabla_02_fopdt_pid_comparativa.csv` / `.md`:

- **Optuna (Óptimo) vs. Control On/Off ($\pm 0.5\,^\circ\text{C}$):** Optuna ($K_p = 15.9337, K_i = 0.13589, K_d = 1.5706$) reduce el error integral absoluto ($\text{IAE}$) en **$-29.86\%$** ($1800.35$ vs. $2566.79\,^\circ\text{C}\cdot\text{s}$), el $\text{ITAE}$ en **$-77.69\%$** ($197{,}188.98$ vs. $883{,}677.68\,^\circ\text{C}\cdot\text{s}^2$), el sobrepaso ($M_p$) en **$-82.64\%$** ($1.61\%$ vs. $9.27\%$) y la variación total de control ($TV_u$) en **$-91.95\%$** ($152.87$ vs. $1900.00\%$), eliminando el ciclo límite del control On/Off (donde $t_s$ no asienta y $e_{ss} = 0.7837\,^\circ\text{C}$, frente a $t_s = 346.0\text{ s}$ y $e_{ss} = 6.48 \times 10^{-5}\,^\circ\text{C}$ con Optuna), con una diferencia marginal de $+2.22\%$ en tiempo de subida ($t_r = 230.0\text{ s}$ vs. $225.0\text{ s}$).
- **Optuna vs. Ziegler-Nichols:** Optuna reduce el esfuerzo de actuación $TV_u$ en **$-27.46\%$** ($152.87$ vs. $210.74\%$) con ganancias mucho menos agresivas ($K_p = 15.93$ vs. $53.37$; $K_d = 1.57$ vs. $889.53$), a costa de un leve incremento en $\text{IAE}$ ($+2.52\%$: $1800.35$ vs. $1756.14$), $\text{ITAE}$ ($+11.13\%$), $t_s$ ($+9.15\%$: $346.0$ vs. $317.0\text{ s}$) y $M_p$ ($+25.75\%$: $1.61\%$ vs. $1.28\%$).
- **Optuna vs. Cohen-Coon:** Optuna reduce $TV_u$ en **$-27.80\%$** ($152.87$ vs. $211.74\%$), con incremento de $+2.74\%$ en $\text{IAE}$, $+12.40\%$ en $\text{ITAE}$ y $+6.79\%$ en $t_s$ ($346.0$ vs. $324.0\text{ s}$; $M_p = 1.61\%$ vs. $0.21\%$, diferencia relativa de $+674.47\%$ sobre un valor base cercano a cero).
- **Optuna vs. IMC:** Optuna mejora sustancialmente la rapidez y el seguimiento respecto a IMC: reduce $\text{IAE}$ en **$-14.03\%$** ($1800.35$ vs. $2094.20$), $\text{ITAE}$ en **$-44.14\%$** ($197{,}188.98$ vs. $353{,}032.53$), $t_s$ en **$-52.80\%$** ($346.0$ vs. $733.0\text{ s}$) y $t_r$ en **$-22.56\%$** ($230.0$ vs. $297.0\text{ s}$), con apenas $+2.26\%$ más de $TV_u$ ($152.87$ vs. $149.48\%$) y un sobrepaso acotado ($1.61\%$ vs. $0.00\%$).

---

## 3. Análisis de Convergencia y Comparación de Visión por Computadora en Colab Real

**Fuentes reales analizadas:** `data/models/entrenados_colab/verificacion.json`, `resumen_evaluacion_final.csv`, `seleccion_por_validacion.json`, `results.csv` y `experiment.json` de los tres entrenamientos ejecutados en Google Colab GPU (2026-11-04).

### 3.1 Clasificación foliar en PlantVillage (`yolo26n_plantvillage_classify`)

- **Cobertura de entrenamiento:** Se ejecutaron $25$ épocas efectivas registradas en `results.csv` de $50$ planificadas (detención temprana por convergencia/paciencia; `best.pt` = $3.19\text{ MB}$ / $3.04\text{ MiB}$).
- **Trayectoria global (épocas 1–25):** `metrics/accuracy_top1` osciló entre $0.80186$ (época 4) y $1.0000$ (alcanzado por primera vez en la época 10 y repetido en la época 18), con promedio global $M = 0.9786 \pm 0.0457$. El mínimo `val/loss` ocurrió en la época 18 ($0.00481$).
- **Últimas 5 épocas (21–25):** `accuracy_top1` alcanzó $M = 0.9944 \pm 0.0034$ ($\text{Mdn} = 0.9969, \text{RIQ} = 0.0062$), `train/loss` $M = 0.0476 \pm 0.0177$ y `val/loss` $M = 0.0149 \pm 0.0090$.
- **Métricas puntuales verificadas (`verificacion.json`):** En validación (`n = 323`) y test independiente (`n = 323`), `accuracy_top1 = 1.0000` y `accuracy_top5 = 1.0000` (`fitness = 1.0`). [NOTA] Este desempeño perfecto refleja la homogeneidad de laboratorio de PlantVillage (hojas aisladas sobre fondo uniforme) y no es extrapolable directamente al follaje superpuesto de invernadero en La Paz.

### 3.2 Detección foliar en PlantDoc (`yolo26n_plantdoc_detect` vs. `yolo11n_plantdoc_detect`)

- **Horizonte ejecutado:** `yolo26n_plantdoc_detect` completó $40$ épocas en `results.csv` (`best.pt` = $5.43\text{ MB}$ / $5.18\text{ MiB}$; mejor época en `mAP50-95(B)` = época 25 en CSV con $0.46615$, evaluado finalmente en `verificacion.json` con $0.4699$), mientras `yolo11n_plantdoc_detect` completó $43$ épocas (`best.pt` = $5.48\text{ MB}$ / $5.23\text{ MiB}$; mejor época en `mAP50-95(B)` = época 28 con $0.39888$, `verificacion.json` = $0.3981$).
- **Dinámica en las últimas 10 épocas comunes (épocas 31–40):**
  - `yolo26n`: `mAP50(B)` $M = 0.5597 \pm 0.0089$; `mAP50-95(B)` $M = 0.4151 \pm 0.0118$; `Precision(B)` $M = 0.5967 \pm 0.0394$; `Recall(B)` $M = 0.5318 \pm 0.0219$.
  - `yolo11n`: `mAP50(B)` $M = 0.5045 \pm 0.0208$; `mAP50-95(B)` $M = 0.3543 \pm 0.0194$; `Precision(B)` $M = 0.4379 \pm 0.0396$; `Recall(B)` $M = 0.6077 \pm 0.0692$. (En sus últimas 10 épocas propias 34–43, `yolo11n` registró `mAP50(B)` $M = 0.4963 \pm 0.0289$ y `mAP50-95(B)` $M = 0.3511 \pm 0.0225$).
- **Comparativa estadística pareada sobre 40 épocas comunes (épocas 1–40):**
  > [NOTA] Esta prueba pareada compara la **dinámica de aprendizaje por época en el conjunto de validación** entre dos arquitecturas entrenadas sobre la misma partición (40 pares de épocas); no equivale a una prueba de inferencia sobre imágenes individuales del conjunto de prueba.

  La normalidad de las diferencias por época ($d_t = \text{YOLO26n}_t - \text{YOLO11n}_t$) fue rechazada por Shapiro-Wilk para `mAP50(B)` ($W = 0.9066, p = .0030$), `mAP50-95(B)` ($W = 0.8840, p = .0007$) y `Precision(B)` ($W = 0.8507, p = .0001$), cumpliéndose solo en `Recall(B)` ($W = 0.9846, p = .8524$). En consecuencia, se aplicó la prueba no paramétrica pareada de **Wilcoxon de rangos con signo** ($N = 40$ pares), reportando además la prueba de Mann-Whitney U ($n_1 = 40, n_2 = 40$) como referencia de distribución marginal:
  1. **`mAP@0.50`:** YOLO26n ($\text{Mdn} = 0.5623, \text{RIQ} = 0.1274$) superó significativamente a YOLO11n ($\text{Mdn} = 0.4449, \text{RIQ} = 0.1358$), $\text{Mdn}(\Delta) = +0.0828$, $W = 104.0, Z = 4.11, p = 3.905 \times 10^{-5}$, tamaño de efecto grande ($r = 0.650$; Mann-Whitney $U = 1235.0, p = 2.903 \times 10^{-5}$).
  2. **`mAP@0.50:0.95`:** YOLO26n ($\text{Mdn} = 0.4107, \text{RIQ} = 0.1231$) superó significativamente a YOLO11n ($\text{Mdn} = 0.2948, \text{RIQ} = 0.1060$), $\text{Mdn}(\Delta) = +0.0808$, $W = 93.0, Z = 4.26, p = 2.036 \times 10^{-5}$, tamaño de efecto grande ($r = 0.674$; Mann-Whitney $U = 1227.0, p = 4.061 \times 10^{-5}$).
  3. **`Precision(B)`:** YOLO26n ($\text{Mdn} = 0.5290, \text{RIQ} = 0.1539$) superó a YOLO11n ($\text{Mdn} = 0.4256, \text{RIQ} = 0.0973$), $\text{Mdn}(\Delta) = +0.0977$, $W = 195.0, Z = 2.89, p = .0039$, efecto moderado-grande ($r = 0.457$; Mann-Whitney $U = 1071.0, p = .0092$).
  4. **`Recall(B)`:** YOLO26n ($\text{Mdn} = 0.5698, \text{RIQ} = 0.1233$) superó moderadamente a YOLO11n ($\text{Mdn} = 0.5569, \text{RIQ} = 0.1201$), $\text{Mdn}(\Delta) = +0.0537$, $W = 236.0, Z = 2.34, p = .0193$, efecto moderado ($r = 0.370$; referencia pareada $t(39) = 2.61, p = .0129$; Mann-Whitney no pareado $U = 1003.5, p = .0507$).
- **Evaluación única en conjunto de prueba independiente (`yolo26n_plantdoc_detect`):** En `resumen_evaluacion_final.csv` y `verificacion.json` ($n = 33$ imágenes de test), el modelo seleccionado (`seleccion_por_validacion.json`) obtuvo **`mAP50 = 0.4926`** ($0.49256$), **`mAP50-95 = 0.3216`** ($0.32164$), **`Precision = 0.4551`** ($0.45515$) y **`Recall = 0.5985`** ($0.59854$), mientras `yolo11n_plantdoc_detect` registra `test: null`. La caída entre validación ($\text{mAP50} = 0.6343$) y test ($\text{mAP50} = 0.4926$) refleja alta varianza muestral esperada en $n = 33$ imágenes de prueba. Las curvas por época y el contraste frente al test único se grafican en `/home/rodrigo/Desktop/IOTtesis/tesis/figuras/fig_est_curvas_colab_plantdoc.png`, y el resumen consolidado obra en `/home/rodrigo/Desktop/IOTtesis/tesis/tablas/tabla_03_modelos_vision_colab.csv` y `.md`.

### 3.3 Balance de los datasets públicos reales curados

Calculado directamente desde `data/processed/papa_plantvillage_clasificacion/report.json` y `data/processed/papa_plantdoc_yolo/report.json` (ambos con `exact_duplicate_leakage: false`):
- **PlantVillage (`2152` imágenes únicas, `3` clases):** `train = 1506` ($70.0\%$), `val = 323` ($15.0\%$), `test = 323` ($15.0\%$). Distribución por clase: `tizon_tardio = 1000` ($46.47\%$), `tizon_temprano = 1000` ($46.47\%$) y `hoja_sana = 152` ($7.06\%$; $106$ train, $23$ val, $23$ test). Presenta un **desbalance severo de `6.579:1`** entre clases enfermas y sanas (entropía normalizada de Shannon $H_{\text{norm}} = 0.8187$).
- **PlantDoc (`219` imágenes únicas, `569` cajas de hoja completa, `2` clases):** `train = 153` imágenes únicas (`verificacion.json`; la suma de presencias por clase en `report.json` da $74 + 81 = 155$ porque **2 imágenes de entrenamiento contienen cajas de ambas clases**), `val = 33` ($16$ `tizon_tardio`, $17$ `tizon_temprano`), `test = 33` ($16$ `tizon_tardio`, $17$ `tizon_temprano`). Presencias en imagen: $106$ `tizon_tardio` y $115$ `tizon_temprano` (razón $1.085:1$, $H_{\text{norm}} = 0.9988$). Distribución exacta de cajas (`569` en total): `tizon_tardio = 250` ($43.94\%$: $167$ train, $45$ val, $38$ test) y `tizon_temprano = 319` ($56.06\%$: $236$ train, $36$ val, $47$ test), con razón de desbalance de cajas **`1.276:1`** y densidad promedio de **`2.598` cajas por imagen**. [NOTA] Las cajas de PlantDoc delimitan hojas completas, no lesiones individuales, por lo que no permiten estimar porcentaje de severidad de lesión.

El balance completo por clase y partición se visualiza en `/home/rodrigo/Desktop/IOTtesis/tesis/figuras/fig_est_distribucion_datasets_reales.png`.

---

## 4. Análisis de Modelos de Riesgo Fitopatológico (Fase 5) y Verificación de Artefactos Reales

### 4.1 Evaluación comparativa de modelos de riesgo (`metricas_experimentos_fase5_riesgo.csv`)

La partición temporal estricta ejecutada en `scripts/ejecutar_fase5_riesgo_fusion.py` sobre `dataset_agroclimatico_invernadero.csv` comprende:
- **Train:** $1296\text{ h}$ ($60.0\%$; $462$ positivos, $35.65\%$).
- **Val:** $432\text{ h}$ ($20.0\%$; $246$ positivos, $56.94\%$).
- **Test:** $432\text{ h}$ ($20.0\%$; $214$ positivos, $49.54\%$).

Sobre el conjunto de prueba ($n = 432\text{ h}$), la **Tabla 4** (`/home/rodrigo/Desktop/IOTtesis/tesis/tablas/tabla_04_riesgo_fitopatologico.csv` y `.md`) revela una distinción metodológica crítica:
1. **`BlightManager (Wallin 1962)`** obtiene $\text{ROC-AUC} = 1.0000$, $\text{PR-AUC} = 1.0000$, $\text{Brier Score} = 0.0105$ y $\text{F1-Score} = 0.9712$. Esto ocurre porque la línea base evalúa directamente la variable `blight_units_7d`, la cual define de manera determinística la etiqueta objetivo (`blight_units_7d >= 14.0` coincide en el $100.00\%$ de las $2160$ horas con `riesgo_infeccion_gt`).
2. **Modelos de aprendizaje automático (24 variables de telemetría y ventanas móviles, excluyendo `blight_units_7d`):**
   - **`XGBoost (Calibrado isotónicamente)`** [Seleccionado]: $\text{ROC-AUC} = 0.7123$, $\text{PR-AUC} = 0.7641$, **menor Brier Score entre los modelos ML ($0.1878$)**, $\text{F1-Score} = 0.6497$, latencia CPU = $0.038\text{ ms}$ por predicción.
   - **`Support Vector Machine (RBF)`:** Mayor $\text{ROC-AUC}$ ($0.7358$; $+0.0235$ sobre XGBoost) y mayor $\text{PR-AUC}$ ($0.8089$), con $\text{Brier Score} = 0.2037$ ($+0.0159$ peor calibración que XGBoost), $\text{F1} = 0.6402$, latencia = $0.026\text{ ms}$.
   - **`Random Forest (Calibrado Platt)`:** $\text{ROC-AUC} = 0.6856$, $\text{PR-AUC} = 0.7783$, $\text{Brier Score} = 0.2099$, $\text{F1} = 0.6320$, latencia = $0.013\text{ ms}$.
   - **`Bioclimatic LSTM (PyTorch)`:** $\text{ROC-AUC} = 0.6656$, $\text{PR-AUC} = 0.7931$, mayor $\text{F1-Score}$ ($0.6629$), pero peor calibración probabilística ($\text{Brier Score} = 0.2649$, $+0.0771$ frente a XGBoost), latencia = $0.019\text{ ms}$ sobre ventanas de $24\text{ h}$.

En consecuencia, la selección de `XGBoost (Calibrado)` se sustenta estadísticamente en la minimización del **Brier Score** ($0.1878$), métrica clave cuando la probabilidad predicha alimenta directamente la función de fusión multimodal ($0.45\,P_{\text{clima}} + 0.35\,S_{\text{visión}} + 0.20\,T_{48\text{h}}$).

### 4.2 Verificación de artefactos de software, firmware y datos de referencia

Mediante inspección directa del código y ejecutables en `/home/rodrigo/Desktop/IOTtesis`:
- **Firmware ESP32 compilado:** `firmware/esp32_control/.pio/build/esp32dev/firmware.bin` = **$818{,}992\text{ bytes}$ ($799.80\text{ KiB}$)**.
- **Base de datos relacional SQLite (`data/invernadero_relacional.db`):** $5$ tablas operativas definidas en `server/app/models/schemas.sql` con registros semilla verificados: `nodos_sensores` ($4$), `detecciones_vision` ($5$), `eventos_alarmas` ($11$), `auditoria_control_pid` ($41$) y `experimentos_ensayos` ($8$).
- **API y Plataforma Web:** $7$ endpoints en `server/app/api/endpoints.py` (`/health`, `/vision/modelos`, `/vision/inferir`, `/control/setpoints`, `/vision/historial`, `/alertas`, `/telegram/notificar`); $15$ rutas URL en `web/dashboard/urls.py` y $6$ plantillas HTML en `web/dashboard/templates/dashboard/`.
- **Pruebas automatizadas:** `.venv/bin/pytest -q` ejecutado sobre el repositorio completo aprobó **`117 passed`** en $4.69\text{ s}$.
- **Datos de referencia/diseño excluidos de métricas reales:** `data/synthetic/metricas_experimentos_e1_e2_e3.csv` ($6$ filas con métricas de diseño E1–E3 como `mAP50 = 0.884` o `MobileNetV3 = 0.942`) y `data/dataset_yolo/` ($864$ imágenes sintéticas) corresponden exclusivamente a prototipado de diseño/pipeline y **no deben reportarse** como desempeño empírico de los modelos reales de Colab ni de campo.

---

## 5. Inventario de Entregables Generados por el Agente 5

- **Script estadístico:** `/home/rodrigo/Desktop/IOTtesis/tesis/scripts/analisis_estadistico_tesis.py`
- **Tablas (CSV y Markdown APA 7):**
  - `/home/rodrigo/Desktop/IOTtesis/tesis/tablas/tabla_01_descriptiva_agroclimatica.csv` y `.md`
  - `/home/rodrigo/Desktop/IOTtesis/tesis/tablas/tabla_02_fopdt_pid_comparativa.csv` y `.md`
  - `/home/rodrigo/Desktop/IOTtesis/tesis/tablas/tabla_03_modelos_vision_colab.csv` y `.md`
  - `/home/rodrigo/Desktop/IOTtesis/tesis/tablas/tabla_04_riesgo_fitopatologico.csv` y `.md`
- **Figuras científicas (300 dpi):**
  - `/home/rodrigo/Desktop/IOTtesis/tesis/figuras/fig_est_boxplots_vpd_riesgo.png`
  - `/home/rodrigo/Desktop/IOTtesis/tesis/figuras/fig_est_residuos_fopdt.png`
  - `/home/rodrigo/Desktop/IOTtesis/tesis/figuras/fig_est_curvas_colab_plantdoc.png`
  - `/home/rodrigo/Desktop/IOTtesis/tesis/figuras/fig_est_distribucion_datasets_reales.png`
- **Informe consolidado:** `/home/rodrigo/Desktop/IOTtesis/tesis/02_analisis_datos.md`
