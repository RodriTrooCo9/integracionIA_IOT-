# Contrato de Invariantes y Línea Base de la Tesis (`00_contrato_tesis.md`)

**Proyecto:** Sistema prototipo integrado de IoT, control PID e inteligencia artificial para la regulación microclimática y detección temprana de plagas en el cultivo de papa bajo invernadero (La Paz, Bolivia)  
**Repositorio:** `/home/rodrigo/Desktop/IOTtesis`  
**Rama activa al congelamiento:** `fix/endpoints,django`  
**Commit base (`HEAD`):** `b898902fb90c9a02a7aec37fd5aa0b33cd8c392e` (`b898902`)  
**Tag Git inmutable:** `tesis-v1` (apuntando exactamente a `b898902fb90c9a02a7aec37fd5aa0b33cd8c392e`)  
**Fecha de congelamiento:** 2026-11-13  

---

## 1. Reglas de Intangibilidad y Artefactos Congelados

1. **Solo lectura absoluta en `/tesis/*` y `/thesis/*`:** Ninguna mejora de ingeniería puede editar, mover, renombrar ni sobrescribir archivos de [`tesis/`](file:///home/rodrigo/Desktop/IOTtesis/tesis/), [`Tesis_Capitulos_I_II_III_APA7.docx`](file:///home/rodrigo/Desktop/IOTtesis/tesis/Tesis_Capitulos_I_II_III_APA7.docx), capítulos, tablas (`tesis/tablas/`), figuras (`tesis/figuras/`, `thesis/figuras/`) ni borradores (`thesis/borrador/`).
2. **Modo tesis preservado por defecto:** Cualquier optimización, refactorización o endurecimiento de seguridad en `server/`, `web/`, `scripts/`, `firmware/` o `docker-compose.yml` debe mantener exactamente intactos los contratos, constantes, semillas, métricas reportadas y resultados por defecto documentados en este contrato. Cualquier modo nuevo (por ejemplo, caché, inferencia ONNX, heurísticas extendidas o nuevos endpoints) debe ser **opt-in** o **estrictamente compatible hacia atrás**.
3. **Respaldo inmutable y manifiesto SHA-256:**
   - Respaldo en [`tesis_snapshot/`](file:///home/rodrigo/Desktop/IOTtesis/mejoras/_baseline/tesis_snapshot/) (permisos de solo lectura `0444`/`0555`) con el `.docx`, los `.md` principales (`00_auditoria.md` a `04_revision_apa7.md`, `cap1_introduccion.md` a `cap3_diseno_metodologico.md`, `anexos_instrumentos.md`, `referencias_apa7.md`, `pendientes.md`, `registro_evidencias.md`), `tesis/tablas/` y `tesis/figuras/`.
   - Manifiesto criptográfico en [`baseline_sha256.json`](file:///home/rodrigo/Desktop/IOTtesis/mejoras/_baseline/baseline_sha256.json) con **77 archivos** verificados (`tesis/`, `thesis/`, `data/models/entrenados_colab/`, `data/processed/*/report.json`, `data/synthetic/*.csv`, y `firmware/esp32_control/.pio/build/esp32dev/firmware.bin`).

---

## 2. Inventario Exacto de Invariantes de la Tesis

### 2.1 Visión por Computadora — Pilotos Reales Google Colab (`data/models/entrenados_colab/`)

Fuentes verificadas: [`verificacion.json`](file:///home/rodrigo/Desktop/IOTtesis/data/models/entrenados_colab/verificacion.json), [`resumen_evaluacion_final.csv`](file:///home/rodrigo/Desktop/IOTtesis/data/models/entrenados_colab/resumen_evaluacion_final.csv), [`seleccion_por_validacion.json`](file:///home/rodrigo/Desktop/IOTtesis/data/models/entrenados_colab/seleccion_por_validacion.json) y `experiment.json` de cada corrida (`2026-11-04`, `seed=42`).

| Modelo / Corrida | Tarea / Config | Clases | Validación | Test Independiente | SHA-256 (`best.pt`) / Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `yolo26n_plantvillage_classify` | `classify`, `yolo26n-cls.pt`, `imgsz=224`, `batch=16`, `epochs_planned=50`, `epochs_csv=25` | `0: hoja_sana`, `1: tizon_tardio`, `2: tizon_temprano` | `accuracy_top1 = 1.0`, `accuracy_top5 = 1.0`, `fitness = 1.0` (`n=323`) | `accuracy_top1 = 1.0`, `accuracy_top5 = 1.0`, `fitness = 1.0` (`n=323`) | `d148b59f0a691f144faf6469c082cee36615112908f5f29e1ed33cb908db90ab` (`severidad_disponible = false`) |
| `yolo26n_plantdoc_detect` (**Seleccionado**) | `detect`, `yolo26n.pt`, `imgsz=640`, `batch=8`, `epochs_planned=50`, `epochs_csv=40` | `0: tizon_tardio`, `1: tizon_temprano` | `Precision = 0.46896933071887736` (`0.4690`), `Recall = 0.7453365715454467` (`0.7453`), `mAP50 = 0.6343364049747451` (`0.6343`), `mAP50-95 = 0.46993872016654403` (`0.4699`) | `Precision = 0.45514925484750995` (`0.4551`), `Recall = 0.5985442329227324` (`0.5985`), `mAP50 = 0.4925604439342057` (`0.4926`), `mAP50-95 = 0.3216350406506016` (`0.3216`) (`n=33`) | `24e18b2f9fd3e3aabf834b409b7bdf0eea763061633e41e2022f71ad8038b57b` (`box_semantics = "whole_leaf"`, `severidad_disponible = false`) |
| `yolo11n_plantdoc_detect` | `detect`, `yolo11n.pt`, `imgsz=640`, `batch=8`, `epochs_planned=50`, `epochs_csv=43` | `0: tizon_tardio`, `1: tizon_temprano` | `Precision = 0.5566497474851205` (`0.5566`), `Recall = 0.5807532831131691` (`0.5808`), `mAP50 = 0.5917793372665938` (`0.5918`), `mAP50-95 = 0.3981353638936549` (`0.3981`) | `null` (no evaluado como modelo final en test) | `9dff00d5be2e226434ec9ae18683f38efff05ad7cbaeb89324f656d79f8d4508` |

Invariantes de inferencia visual ([`vision_service.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/services/vision_service.py)):
- Dominio cerrado `CLASES_PAPA`: `{0: 'tizon_tardio', 1: 'tizon_temprano', 2: 'hoja_sana', 3: 'mosca_minadora', 4: 'pulgon', 5: 'polilla_papa'}`.
- Prohibido cargar o reetiquetar pesos COCO genéricos; con `VISION_DEMO_MODE = False` y sin pesos válidos, responder `HTTP 503`.
- Validación estricta de `.metadata.json` (`task`, `names`, `weights_sha256`, `box_semantics`).
- Si `box_semantics` es `"whole_leaf"` o `"unknown"`, o si `task == "classify"`, mantener `severidad_disponible = false` y `apto_supervision = false` (nunca calcular severidad % sobre cajas de hoja completa).
- Parámetros por defecto de `SAHI` (`0.12.8`): ventanas `320 × 320 px`, `overlap_height_ratio = 0.2`, `overlap_width_ratio = 0.2`, `confidence_threshold = 0.25`, `device = 'cpu'`.

### 2.2 Conjuntos de Datos Curados (`data/processed/*/report.json` y `data/dataset_yolo/`)

- **PlantVillage** ([`papa_plantvillage_clasificacion/report.json`](file:///home/rodrigo/Desktop/IOTtesis/data/processed/papa_plantvillage_clasificacion/report.json)):
  - **2.152 imágenes únicas** (`exact_duplicate_leakage: false`, `seed=42`, revisión `7f7ecc7e1eaca78107e3affe7cb5abd9427e139a`, `manifest_sha256_training: 24d34da90308cd3a2cbc213d91c3179094dfe9ee4363d6cd94d4208b8f957ebb`).
  - Particiones: `train = 1.506` (`tizon_tardio: 700`, `tizon_temprano: 700`, `hoja_sana: 106`), `val = 323` (`150 / 150 / 23`), `test = 323` (`150 / 150 / 23`). Total por clase: `1.000 / 1.000 / 152` (razón de desbalance `6,579:1`).
- **PlantDoc** ([`papa_plantdoc_yolo/report.json`](file:///home/rodrigo/Desktop/IOTtesis/data/processed/papa_plantdoc_yolo/report.json)):
  - **219 imágenes únicas / 569 cajas** (`whole_leaf`, `exact_duplicate_leakage: false`, `seed=42`, revisión `4730a233a555b30ee98e0879c63ad25d82407455`, `manifest_sha256_training: f1b6cf93b29d295ef5ff654d9b0e507a588a2e942515664af440947f92dd9d25`).
  - Particiones de imágenes: `train = 153` (presencias por clase: `tizon_tardio: 74`, `tizon_temprano: 81`; **2 imágenes** contienen ambas clases), `val = 33` (`16 / 17`), `test = 33` (`16 / 17`).
  - Particiones de cajas (`569`): `train = 403` (`167 / 236`), `val = 81` (`45 / 36`), `test = 85` (`38 / 47`). Total cajas: `tizon_tardio = 250`, `tizon_temprano = 319` (razón `1,276:1`; `2,598` cajas/imagen). Excluye clase ambigua `Potato leaf`.
- **Dataset sintético YOLO (`data/dataset_yolo/`):** `864` muestras sintéticas (`756 train / 54 val / 54 test`, 6 clases), restringido a pruebas de integración de software.

### 2.3 Dinámica Térmica FOPDT y Control PID Optuna vs. On/Off (`data/synthetic/`, `scripts/ejecutar_fase2_identificacion_pid.py`)

- **Generador escalón** ([`generar_datos_escalon.py`](file:///home/rodrigo/Desktop/IOTtesis/data/synthetic/generar_datos_escalon.py)): `random.seed(42)`, `N = 1.800 s` (`1 Hz`, `dt = 1.0 s`), `T_amb = 8.2 °C`, `T_0 = 8.5 °C`, `K_real = 0.165 °C/%`, `tau_real = 240.0 s`, `theta_real = 35.0 s`, escalón `Δu = 70%` en `t = 120.0 s`.
- **Modelo FOPDT identificado (`curve_fit`):**
  - $K = 0{,}1639\,^\circ\text{C}/\%$, $\tau = 242{,}96\text{ s}$, $\theta = 33{,}33\text{ s}$ ($\theta/\tau = 0{,}137$).
  - Bondad de ajuste y residuos: $R^2 = 0{,}9990$ (`0.998989`), $\text{RMSE} = 0{,}1178\,^\circ\text{C}$, $\text{MAE} = 0{,}0962\,^\circ\text{C}$, $\text{DW} = 0{,}9601$, $r_1 = 0{,}5196$.
- **Función de costo Optuna (`TPESampler(seed=42)`):** $J = \text{IAE} + 50{,}0 \cdot \max(0, M_p - 5{,}0)^2 + 0{,}01 \cdot TV_u$.
- **Métricas comparativas congeladas** ([`metricas_comparativa_pid_onoff.csv`](file:///home/rodrigo/Desktop/IOTtesis/data/synthetic/metricas_comparativa_pid_onoff.csv)):
  - **Optuna (Óptimo):** $K_p = 15{,}9337$, $K_i = 0{,}13589$, $K_d = 1{,}5706$, $t_r = 230{,}0\text{ s}$, $t_s = 346{,}0\text{ s}$, $M_p = 1{,}61\,\%$ (`1.6096%`), $e_{ss} = 6{,}48 \times 10^{-5}\,^\circ\text{C}$, $\text{IAE} = 1800{,}35$, $\text{ITAE} = 197188{,}98$, $TV_u = 152{,}87$.
  - **Control On/Off ($\pm 0{,}5\,^\circ\text{C}$):** $t_r = 225{,}0\text{ s}$, $t_s = \text{nan}$, $M_p = 9{,}27\,\%$ (`9.2732%`), $e_{ss} = 0{,}7837\,^\circ\text{C}$, $\text{IAE} = 2566{,}79$, $\text{ITAE} = 883677{,}68$, $TV_u = 1900{,}0$ (Optuna logra $\Delta\text{IAE} = -29{,}86\,\%$ y $\Delta TV_u = -91{,}95\,\%$).
  - **Referencias clásicas preservadas:** `Ziegler-Nichols` ($\text{IAE} = 1756{,}14$, $TV_u = 210{,}74$), `Cohen-Coon` ($\text{IAE} = 1752{,}41$, $TV_u = 211{,}74$), `IMC` ($\text{IAE} = 2094{,}20$, $t_s = 733{,}0\text{ s}$, $TV_u = 149{,}48$).

### 2.4 Simulación Agroclimática (`2160 h`) y Riesgo/Fusión Multimodal (`XGBoost`)

- **Serie agroclimática** ([`generar_dataset_agroclimatico.py`](file:///home/rodrigo/Desktop/IOTtesis/scripts/generar_dataset_agroclimatico.py), `dataset_agroclimatico_invernadero.csv`):
  - `dias = 90`, **`2.160` registros horarios**, `seed = 42`, 16 variables.
  - Estratos `riesgo_infeccion_gt`: `0` (`1.238 h`, `57,31%`) y `1` (`922 h`, `42,69%`), determinístico con `blight_units_7d >= 14.0`.
  - Partición temporal estricta (sin *shuffle*): `train = 1.296 h` (`60%`), `val = 432 h` (`20%`), `test = 432 h` (`20%`).
- **Modelos de riesgo Fase 5** ([`ejecutar_fase5_riesgo_fusion.py`](file:///home/rodrigo/Desktop/IOTtesis/scripts/ejecutar_fase5_riesgo_fusion.py), [`metricas_experimentos_fase5_riesgo.csv`](file:///home/rodrigo/Desktop/IOTtesis/data/synthetic/metricas_experimentos_fase5_riesgo.csv)):
  - `SEED = 42` (`np.random.seed(42)`, `torch.manual_seed(42)`), **24 características causales** (18 derivadas temporales + 6 base, excluyendo `blight_units_7d`).
  - **`XGBoost (Calibrado)` (Ganador por menor Brier):** `ROC-AUC = 0.7123`, `PR-AUC = 0.7641`, **`Brier Score = 0.1878`**, `F1-Score = 0.6497`, latencia CPU `0.038 ms`, variable principal SHAP `lwh_suma_48h` (`|SHAP| = 1.3257`).
  - Comparativas congeladas: `BlightManager (Wallin 1962)` (`ROC-AUC = 1.0`, `Brier = 0.0105`, `F1 = 0.9712`), `Support Vector Machine (RBF)` (`ROC-AUC = 0.7358`, `PR-AUC = 0.8089`, `Brier = 0.2037`), `Random Forest (Calibrado)` (`ROC-AUC = 0.6856`, `Brier = 0.2099`), `Bioclimatic LSTM (PyTorch)` (`ROC-AUC = 0.6656`, `Brier = 0.2649`).
- **Lazo supervisor en cascada** ([`worker.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/worker.py)):
  - Ecuación de fusión: $S_{\text{riesgo}} = \operatorname{clip}(0{,}45 \cdot P_{\text{clima}} + 0{,}35 \cdot S_{\text{visión}} + 0{,}20 \cdot T_{48\text{h}},\, 0{,}0,\, 1{,}0)$, con $S_{\text{visión}} = \min(1{,}0,\, (\text{sev}/20{,}0)\cdot 0{,}65 + (\text{conteo}/25{,}0)\cdot 0{,}35)$.
  - Ventana `deque(maxlen=48)`, `asyncio.sleep(15)` (intervalo nominal 30 s).
  - Umbrales y *setpoints* comandados: `BAJO` (`< 0.30`: `18.0 °C / 75.0%`), `MEDIO` (`0.30–0.55`: `18.5 °C / 70.0%`), `ALTO` (`0.55–0.75`: `19.5 °C / 65.0%`), `CRÍTICO` (`>= 0.75`: `20.0 °C / 60.0%`).

### 2.5 Firmware ESP32 (`firmware/esp32_control/`)

- **Binario compilado:** [`firmware.bin`](file:///home/rodrigo/Desktop/IOTtesis/firmware/esp32_control/.pio/build/esp32dev/firmware.bin) — **`818.992 bytes`** (`799,80 KiB`), SHA-256: `147bffa7da79f5ed974305b2b4b3c4efb06a1681c994c9f4f04c9f5cc1011379`.
- **Constantes de hardware y lazo de borde** ([`config_invernadero.h`](file:///home/rodrigo/Desktop/IOTtesis/firmware/esp32_control/include/config_invernadero.h)):
  - Pines GPIO: `SDA=21`, `SCL=22`, `DS18B20=4`, `ADC_SUELO=34`, `FLOTADOR=35`, `SSR_CALEFACTOR=23`, `PWM_EXTRACTOR=19`, `RELE_HUMIDIF=18`, `RELE_BOMBA=26`, `LED=2`.
  - Temporización y PWM: `PERIODO_PID_MS = 100` (`10 Hz`), `PERIODO_TELEMETRIA_MS = 1000` (`1 Hz`), `WDT_TIMEOUT_SECONDS = 10`, `SSR_VENTANA_TIEMPO_MS = 2000`, `PWM_LEDC_FREQ_HZ = 25000` (`8 bits`).
  - Control por defecto: `DEFAULT_SETPOINT_TEMP = 20.0f`, `DEFAULT_SETPOINT_HUM = 75.0f`, `DEFAULT_KP = 6.5f`, `DEFAULT_KI = 0.08f`, `DEFAULT_KD = 1.2f`, `PID_DEADBAND_TEMP = 0.25f`, `PID_CV_MIN = -100.0f`, `PID_CV_MAX = 100.0f`, `ADC_SUELO_AIRE_SECO = 3100`, `ADC_SUELO_AGUA_SAT = 1450`.

### 2.6 Protocolo Experimental `E1–E8` (`572 h`)

Definido en [`seed_experiments.py`](file:///home/rodrigo/Desktop/IOTtesis/scripts/seed_experiments.py) y alineado 1:1 con Capítulo I (`OE1–OE5`) y Capítulo III (`Tabla 12`, `Anexo A`):
- `E1`: `58.0 h` (Metrológico/repetibilidad `OE1`)
- `E2`: `4.0 h` (Identificación FOPDT `OE2`)
- `E3`: `72.0 h` (Sintonización comparativa PID `OE2`)
- `E4`: `60.0 h` (Control psicrométrico HR/VPD `OE2/OE5`)
- `E5`: `32.0 h` (Detección fitosanitaria foliar `OE3`)
- `E6`: `34.0 h` (Trampas cromáticas amarillas con SAHI `OE1/OE3`)
- `E7`: `120.0 h` (Riesgo bioclimático y SHAP `OE4`)
- `E8`: `192.0 h` (Ensayo integrado 24/7 ante helada `OE1/OE2/OE4/OE5`)
- **Total acumulado invariante:** **`572,0 horas`** (`58 + 4 + 72 + 60 + 32 + 34 + 120 + 192`).

### 2.7 Contrato FastAPI / MQTT / SQLite / Django

- **FastAPI** ([`main.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/main.py), [`endpoints.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/api/endpoints.py)):
  - Prefijo `API_V1_STR = "/api/v1"`, ruta raíz `GET /` más **7 endpoints**: `GET /api/v1/health`, `GET /api/v1/vision/modelos`, `POST /api/v1/vision/inferir`, `POST /api/v1/control/setpoints`, `GET /api/v1/vision/historial`, `GET /api/v1/alertas`, `POST /api/v1/telegram/notificar`.
  - Rangos Pydantic `SetpointsRequest`: `sp_temperatura ∈ [5.0, 35.0]`, `sp_humedad ∈ [30.0, 95.0]`.
- **MQTT** ([`config.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/core/config.py), [`config_invernadero.h`](file:///home/rodrigo/Desktop/IOTtesis/firmware/esp32_control/include/config_invernadero.h)):
  - Tópicos servidor/Docker: `invernadero/telemetria/microclima`, `invernadero/telemetria/pid`, `invernadero/control/setpoints`, `invernadero/vision/detecciones`, `invernadero/riesgo/indice`, `invernadero/alarmas/eventos` (`QoS 1`, Mosquitto `2.0.18` autenticado).
  - Tópicos firmware ESP32: `invernadero/control/setpoint`, `invernadero/control/ganancias`, `invernadero/control/modo`, `invernadero/alerta` (no renombrar ni romper compatibilidad).
- **SQLite WAL** ([`schemas.sql`](file:///home/rodrigo/Desktop/IOTtesis/server/app/models/schemas.sql), [`data/invernadero_relacional.db`](file:///home/rodrigo/Desktop/IOTtesis/data/invernadero_relacional.db)):
  - `PRAGMA journal_mode = wal`, `PRAGMA foreign_keys = ON`.
  - **5 tablas operativas nucleares** y filas semilla base verificadas: `nodos_sensores` (`4`), `detecciones_vision` (`5`), `eventos_alarmas` (`11`), `auditoria_control_pid` (`41`), `experimentos_ensayos` (`8`), junto con tablas internas de Django (`auth_*`, `django_*`, `control_publicado`, `seed_fixtures`).
- **Django** ([`web/invernadero_web/settings.py`](file:///home/rodrigo/Desktop/IOTtesis/web/invernadero_web/settings.py), [`web/dashboard/urls.py`](file:///home/rodrigo/Desktop/IOTtesis/web/dashboard/urls.py)):
  - Versión **`Django 6.1.2`**, `LANGUAGE_CODE = "es-bo"`, `TIME_ZONE = "America/La_Paz"`, **15 rutas URL** en `dashboard` y **6 plantillas HTML**.

### 2.8 Versiones de Dependencias y Línea Base de Pytest

- **Especificado en [`requirements.txt`](file:///home/rodrigo/Desktop/IOTtesis/requirements.txt):** `paho-mqtt==1.6.1`, `influxdb-client==1.41.0`, `aiosqlite==0.20.0`, `django>=5.0,<=6.1.2`, `fastapi==0.110.0`, `uvicorn[standard]==0.28.0`, `pydantic==2.6.4`, `pydantic-settings==2.2.1`, `httpx<0.28.0,>=0.27.0`, `numpy==1.26.4`, `scipy==1.12.0`, `control>=0.10.0`, `pytest==8.1.1`, `pytest-asyncio==0.23.6`, `flake8>=7.0.0`.
- **Entorno local verificado (`.venv`, Python `3.14.4`):** `django==6.1.2`, `fastapi==0.157.0`, `uvicorn==0.54.0`, `pydantic==2.14.1`, `pydantic-settings==2.16.1`, `aiosqlite==0.22.1`, `paho-mqtt==2.1.0`, `httpx==0.28.1`, `numpy==2.5.4`, `pandas==3.0.6`, `scipy==1.18.1`, `matplotlib==3.11.2`, `optuna==5.0.0`, `xgboost==3.4.1`, `scikit-learn==1.9.1`, `shap==0.54.1`, `torch==2.14.1+cpu`, `ultralytics==8.4.183`, `sahi==0.12.8`, `opencv-python-headless==5.0.0.93`, `pytest==9.1.1`, `pytest-asyncio==1.4.0`, `flake8==7.4.1` (`influxdb-client` y `control` no están instalados en `.venv`).
- **Entorno Colab registrado en `experiment.json`:** `ultralytics 8.4.201`, `torch 2.11.0+cu130`.
- **Línea base Pytest (`.venv/bin/pytest -q`):** **`117 passed, 1 warning in 4.73s`** (`StarletteDeprecationWarning` por `httpx` en `fastapi/testclient.py`).

---

## 3. Procedimiento Reproducible de Verificación de Integridad

Al finalizar cualquier fase o cambio en el repositorio, ejecutar los tres comandos siguientes para comprobar que la tesis y sus artefactos base siguen **100 % íntegros**:

### 3.1 Verificación automática integral (script Python dedicado)
```bash
.venv/bin/python mejoras/_baseline/verificar_integridad.py
```
Este script verifica:
1. Que el tag Git `tesis-v1` apunta al commit `b898902fb90c9a02a7aec37fd5aa0b33cd8c392e`.
2. Que los **77 archivos** registrados en [`baseline_sha256.json`](file:///home/rodrigo/Desktop/IOTtesis/mejoras/_baseline/baseline_sha256.json) mantienen exactamente su tamaño en bytes y su digest `SHA-256`.
3. Que no se agregaron, eliminaron ni modificaron archivos dentro de `/tesis/`.
4. Que el contenido de `/tesis/` es idéntico byte a byte al respaldo inmutable [`tesis_snapshot/`](file:///home/rodrigo/Desktop/IOTtesis/mejoras/_baseline/tesis_snapshot/).

### 3.2 Verificación rápida con `sha256sum` y `git` (sin scripts externos)
```bash
git rev-parse --verify tesis-v1 && \
.venv/bin/python -c "import json,hashlib; d=json.load(open('mejoras/_baseline/baseline_sha256.json')); bad=[k for k,v in d['files'].items() if hashlib.sha256(open(k,'rb').read()).hexdigest()!=v['sha256']]; print('OK' if not bad else f'MODIFICADOS: {bad}'); assert not bad" && \
.venv/bin/pytest -q
```
Criterio de aceptación de cierre: `verificar_integridad.py` devuelve código `0` (`77/77`), `git diff tesis-v1 -- tesis/` está vacío (y `/tesis/` sigue intacto fuera de tracking) y `.venv/bin/pytest -q` mantiene `>= 117` pruebas aprobadas sin fallos ni regresiones sobre los invariantes del contrato.
