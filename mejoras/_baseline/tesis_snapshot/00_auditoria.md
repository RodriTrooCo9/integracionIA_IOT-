# Auditoría Integral del Proyecto (FASE 1 – Agente 1)

**Proyecto:** Sistema prototipo integrado de IoT, control PID e inteligencia artificial para la regulación microclimática y detección temprana de plagas en el cultivo de papa bajo invernadero  
**Repositorio auditado:** `/home/rodrigo/Desktop/IOTtesis` (`https://github.com/RodriTrooCo9/integracionIA_IOT-.git`)  
**Carrera / Institución:** Ingeniería de Sistemas, Universidad Salesiana de Bolivia  
**Postulante:** Alvaro Rodrigo De La Barra Velasco (según borrador en `thesis/borrador/TG-I Tesis alvaro rodrigo de la barra velasco 1.2.docx`)  
**Docente Guía:** Lic. / Ing. Freddy Cosme Garnica Carrasco (según borrador)  
**Ubicación declarada:** La Paz, Bolivia (~3.600 m s. n. m.)  
**Fecha de auditoría:** 2026-11-13  

> [ADVERTENCIA] **Regla de integridad probatoria:** En esta auditoría se separa estrictamente la evidencia **verificada en código, datasets públicos, modelos entrenados y pruebas de software** de los resultados **simulados/sintéticos**, de lo **redactado en el borrador** y de los elementos **físicos pendientes (`[DATO FALTANTE]`)**.

---

## 1. Estructura de Archivos del Proyecto

El repositorio presenta una arquitectura modular dividida en los siguientes directorios principales:

- **`firmware/`**: Código fuente embebido C++/PlatformIO para ESP32 DevKit V1 (`firmware/esp32_control/src/main.cpp`, `include/config_invernadero.h`, `platformio.ini`, compilado en `.pio/build/esp32dev/firmware.bin`), alternativa declarativa (`firmware/esphome_invernadero.yaml`) y simulación virtual (`firmware/wokwi/diagram.json`, `wokwi.toml`).
- **`server/`**: Backend FastAPI (`server/app/api/endpoints.py`, `core/config.py`, `worker.py`, `models/schemas.sql`, servicios `database.py`, `mqtt_client.py`, `vision_service.py`, `telegram_bot.py`) y pruebas de contenedor.
- **`web/`**: Plataforma web full-stack en Django (`web/invernadero_web/`, `web/dashboard/models.py`, `views.py`, `services.py`, `urls.py`, 6 plantillas HTML en `templates/dashboard/` y pruebas integradas).
- **`config/`**: Configuración declarativa para Docker (`mosquitto/mosquitto.conf`, `mosquitto/passwd`, `telegraf/telegraf.conf`, `grafana/provisioning/`, `systemd/iot-invernadero.service`).
- **`data/`**:
  - `data/raw/fuentes_reales/` (PlantVillage y PlantDoc descargados), `follaje/` (11 archivos), `trampas/` (12 archivos), `uploads/` (36 archivos de prueba).
  - `data/processed/`: Datasets curados y comprimidos para Colab (`papa_plantvillage_clasificacion/`, `papa_plantdoc_yolo/`, `colab_yolo26_listo.zip`, `vista_previa_datasets_reales.jpg`).
  - `data/models/entrenados_colab/`: Pesos reales entrenados en Colab (`yolo26n_plantvillage_classify`, `yolo26n_plantdoc_detect`, `yolo11n_plantdoc_detect`), sus `results.csv`, `experiment.json`, `verificacion.json`, `seleccion_por_validacion.json`, `resumen_evaluacion_final.csv`.
  - `data/synthetic/`: Series y métricas generadas por simulación (`dataset_agroclimatico_invernadero.csv`, `prueba_escalon_fopdt.csv`, `metricas_comparativa_pid_onoff.csv`, `metricas_experimentos_e1_e2_e3.csv`, `metricas_experimentos_fase5_riesgo.csv`).
  - `data/dataset_yolo/`: 864 muestras/etiquetas sintéticas (756/54/54) generadas por `scripts/preparar_dataset_vision.py`.
  - `data/invernadero_relacional.db`: Base SQLite WAL inicializada con registros semilla (`nodos_sensores`: 4; `detecciones_vision`: 5; `eventos_alarmas`: 11; `auditoria_control_pid`: 41; `experimentos_ensayos`: 8).
- **`notebooks/`**: 5 cuadernos activos (`00_inicio_y_datasets.ipynb` a `04_evaluacion_y_exportacion.ipynb`) y subcarpetas `control/`, `riesgo/`, `archivo/`.
- **`scripts/`**: 24 scripts Python/Bash para inicialización SQLite, simulación ESP32 MQTT, identificación FOPDT/PID, evaluación de riesgo/visión, curaduría de datasets reales, empaquetado Colab y respaldo WAL.
- **`diagramas/`**: Especificación electrónica (`circuito_esp32_invernadero.json`), esquema Wokwi (`wokwi_diagram.json`), guía (`diagrama_conexiones_hardware.md`) y diagrama isométrico (`DIAisoflow.json`, `DIAisoflow.isoflow`).
- **`docs/` y `fases/`**: Documentación técnica de protocolos, hardware, datasets reales, verificación de entrenamiento del 2026-11-04, bibliografía web, orden de cuadernos y bitácora interna (`fases/resumen_fases_ejecutadas.md`).
- **`experiments/`**: Carpetas `e1_deteccion/`, `e2_trampas/`, `e3_clasificacion/` (contienen únicamente archivos `README.md` con diseño/métricas de referencia) y `e4_control_temperatura/` a `e8_robustez/` (actualmente vacías).
- **`tests/`**: Suite Pytest que valida API FastAPI, Django web, MQTT/fusión, Telegram, YOLO26 y flujo Colab (117 pruebas ejecutadas y aprobadas tras los cambios más recientes).
- **`thesis/`**:
  - `thesis/borrador/TG-I Tesis alvaro rodrigo de la barra velasco 1.2.docx`: Borrador que contiene Portada, Resumen, Índices, **Capítulo I (Marco de Referencia)** y **Capítulo II (Marco Teórico)** (926 párrafos). Carece de Capítulos III, IV y V.
  - `thesis/figuras/`: 12 gráficos PNG generados por scripts de simulación/evaluación de Fases 2, 4 y 5.
  - `thesis/bibliografia/`: Carpeta vacía.
- **Raíz y CI/CD**: `docker-compose.yml`, `Makefile`, `requirements*.txt`, `.env*`, `.github/workflows/` (`ci.yml`, `docker-build.yml`, `release.yml`), `VERSION` (`0.7.0`), `CHANGELOG.md`, `agents.md`, `README.md`.

---

## 2. Objetivo Real del Proyecto y Problema que Resuelve

### 2.1 Objetivo real inferido del sistema implementado
Diseñar, construir y validar un **prototipo ciberfísico en arquitectura jerárquica en cascada** para invernadero de papa (*Solanum tuberosum*) a escala de laboratorio en La Paz (~3.600 m s. n. m.), integrando:
1. **Lazo interno autónomo (10 Hz en ESP32):** Adquisición ambiental/edáfica con filtrado Hampel + EMA, psicrometría en borde (VPD y punto de rocío por Tetens/Magnus) y control PID en rango partido (*split-range*) para calefactor SSR 220 V y extractor PWM 12 V, con banda muerta y persistencia ante fallos de red/servidor.
2. **Lazo externo supervisor e infraestructura IoT:** Bus MQTT autenticado (Mosquitto), ingesta a series temporales (Telegraf → InfluxDB v2 → Grafana), backend FastAPI + worker supervisor asíncrono (fusión ponderada `0.45*Clima + 0.35*Visión + 0.20*Tendencia`) y plataforma web Django sobre SQLite WAL.
3. **Vigilancia fitosanitaria por visión artificial:** Detección/clasificación con YOLO26n / YOLO11n + SAHI y notificación mediante bot de Telegram.

### 2.2 Problema que resuelve
Atiende tres brechas críticas en invernaderos de papa en el Altiplano paceño:
1. Ausencia de telemetría continua trazable de temperatura, humedad relativa, VPD y humedad edáfica.
2. Regulación manual o On/Off con oscilaciones térmicas severas y sobreimpulsos que inducen estrés estomático (VPD > 1,5 kPa) o riesgo epidémico por condensación/alta humedad (VPD < 0,4 kPa, HR >= 85–90 %).
3. Detección visual tardía y reactiva de patógenos foliares (principalmente *Phytophthora infestans* y *Alternaria solani*) y plagas diminutas en trampas amarillas.

### 2.3 Tipo de estudio deducido
De acuerdo con el proyecto real y el borrador (`TG-I...1.2.docx`), corresponde a una **investigación tecnológica aplicada de diseño, desarrollo e ingeniería experimental** (enfoque cuantitativo, diseño cuasiexperimental o de validación comparativa en bloques entre manejo manual Nivel 0 y prototipo automatizado Nivel 1, estructurado bajo el **Modelo en V** para sistemas ciberfísicos).

---

## 3. Tecnologías y Materiales Identificados en el Proyecto Real vs. Borrador

### 3.1 Software y servicios verificados en el código
- **Firmware:** C++ / Arduino Framework sobre PlatformIO (`ESP32 DevKit V1`), librerías `Adafruit SHT31`, `DallasTemperature`, `OneWire`, `BH1750`, `PubSubClient`, `ArduinoJson`, `esp_task_wdt`. Alternativa `ESPHome` y modelo `Wokwi`.
- **Contenedores e IoT:** Docker Compose (`docker-compose.yml`) con 6 servicios: Eclipse Mosquitto `2.0.18` (auth PBKDF2-SHA512), InfluxDB `2.7.5-alpine`, Telegraf `1.30.0-alpine`, Grafana `10.4.1`, FastAPI + Uvicorn (Python 3.11) e `inference_worker`.
- **Aplicación Web y Base de Datos:** Django (`web/`) con Tailwind CSS, Chart.js, Lucide Icons; SQLite en modo WAL (`data/invernadero_relacional.db`).
- **IA / Visión / Ciencia de Datos:** Ultralytics (`YOLO26n`, `YOLO26n-cls`, `YOLO11n`), `SAHI 0.12.8`, PyTorch, Albumentations, OpenCV headless, scikit-learn, XGBoost, Optuna, SHAP, `python-control`, `httpx` (Telegram Bot).
- **CI/CD y Pruebas:** GitHub Actions (`flake8`, `docker compose config`, `manage.py check`, `pytest`, compilación PlatformIO).

### 3.2 Hardware y materiales especificados en código/documentación (`docs/README_hardware_infraestructura.md`, `firmware/`, `diagramas/`)
- **Controlador:** ESP32 DevKit V1 (30 pines).
- **Sensores:** SHT31 (I2C `0x44`, T/HR aire), BH1750 (I2C, iluminancia), DS18B20 OneWire (T suelo), sensor capacitivo de humedad de suelo v1.2 (`GPIO 34`, ADC1_CH6), interruptor de flotador de nivel (`GPIO 35`).
- **Actuadores y potencia:** Relé de estado sólido SSR fototriac optoaislado 4000 V (`GPIO 23`, ventana 2000 ms) para calefactor 220 V AC; MOSFET canal-N IRLZ44N (`GPIO 19`, PWM 25 kHz) para extractor axial 12 V DC; módulos relé Active-LOW (`GPIO 18` humidificador, `GPIO 26` bomba de riego con diodo 1N4007); fuente switching 12 V 10 A + reductor Buck LM2596 12 V→5 V; fusibles 5 A / 8 A.
- **Óptica y cómputo:** Cámara USB 1080p y módulo auxiliar ESP32-CAM OV2640 (especificados en protocolo); PC/laptop o VM sin GPU para inferencia; Google Colab GPU para entrenamiento.
- **Discrepancia documental crítica detectada:** El borrador `.docx` (Cap. I y II) menciona *Node-RED*, *PostgreSQL/TimescaleDB*, *DHT22/RHT03*, *nebulización neumática AirWet*, *Raspberry Pi 4/5* y *YOLOv8* en la Tabla 1, además de delimitar las plagas a *tizón tardío* y *mosca blanca (Bemisia tabaci)*. Sin embargo, el sistema real construido usa *Mosquitto + Telegraf + InfluxDB v2 + FastAPI + Django + SQLite*, *SHT31 + DS18B20 + BH1750*, *calefactor SSR + extractor PWM + humidificador/bomba*, y los modelos entrenados detectan/clasifican únicamente patologías foliares (*tizon_tardio*, *tizon_temprano*, *hoja_sana*) sin pesos reales para *Bemisia tabaci* ni insectos en trampa.

---

## 4. Datos Disponibles (Tipo, Tamaño, Variables y Procedencia)

| Conjunto / Archivo | Naturaleza | Tamaño | Variables / Clases | Uso y Limitación Verificada |
| :--- | :--- | :--- | :--- | :--- |
| `data/processed/papa_plantvillage_clasificacion/` | **Real público** (PlantVillage papa) | 2.152 imágenes (`train` 1.506 / `val` 323 / `test` 323) | 3 clases: `tizon_tardio` (1000), `tizon_temprano` (1000), `hoja_sana` (152) | Clasificación de hoja aislada en laboratorio; sin fuga por hash exacto; no representa fondo de invernadero en La Paz. |
| `data/processed/papa_plantdoc_yolo/` | **Real público** (PlantDoc papa) | 219 imágenes (`train` 153 / `val` 33 / `test` 33), 569 cajas | 2 clases: `tizon_tardio` (257 cajas), `tizon_temprano` (312 cajas) | Detección piloto; las cajas delimitan **hojas completas, no lesiones**; no incluye insectos ni clase sana confirmada. |
| `data/dataset_yolo/` | **Sintético / simulado** (`preparar_dataset_vision.py`) | 864 imágenes (`train` 756 / `val` 54 / `test` 54) | 6 clases: `tizon_tardio`, `tizon_temprano`, `hoja_sana`, `mosca_minadora`, `pulgon`, `polilla_papa` | Generado programáticamente para validar pipeline YOLO; no apto para reportar precisión clínica/agronómica real. |
| `data/synthetic/prueba_escalon_fopdt.csv` | **Simulado** (`generar_datos_escalon.py`) | 1.800 filas (1 Hz, 30 min) | `tiempo_segundos`, `control_u_pct`, `temperatura_medida_c`, `temperatura_ideal_c` | Curva escalón al 70 % con modelo teórico de La Paz; aún no reemplazada por escalón del invernadero físico. |
| `data/synthetic/dataset_agroclimatico_invernadero.csv` | **Sintético biofísico** (`generar_dataset_agroclimatico.py`) | 2.160 filas (90 días horarios) | 16 variables (T ext/int, radiación, HR, T/H suelo, VPD, punto rocío, LWH, blight units, visión simulada, riesgo GT) | Simulación de verano andino; base de Fase 5; requiere sustitución por telemetría física de campo. |
| `data/synthetic/metricas_*.csv` | **Simulado / referencia** | 5–6 filas por archivo | Métricas PID (`Kp, Ki, Kd, tr, ts, Mp, ess, IAE, ITAE, TV_u`), E1–E3 y Fase 5 (ROC/PR/Brier/F1) | Provenientes de simulaciones y valores de diseño en scripts; `metricas_experimentos_e1_e2_e3.csv` no corresponde a los pesos Colab reales. |
| `data/invernadero_relacional.db` | **Base operativa semilla** | 5 tablas (4 nodos, 5 det., 11 alarmas, 41 auditorías, 8 ensayos) | Registro relacional IoT/PID/IA/E1–E8 | Inicializada con `init_db.py` y `seed_experiments.py` para pruebas de backend/web. |

---

## 5. Procedimientos Ya Realizados vs. Pendientes

### 5.1 Procedimientos completados y verificados en el repositorio
1. **Ingeniería de software, IoT y contenedores:** Configuración Docker Compose de 6 servicios, esquemas InfluxDB/Telegraf/Grafana, API FastAPI, worker supervisor, bot Telegram, aplicación web Django con 5 vistas + gemelo digital y respaldo WAL SQLite.
2. **Firmware ESP32:** Implementación C++/PlatformIO y compilación verificada (`firmware.bin`), además de definición Wokwi y ESPHome.
3. **Curaduría de datasets públicos reales:** Filtrado, deduplicación por hash de píxeles y partición agrupada 70/15/15 en PlantVillage (2.152 imgs) y PlantDoc (219 imgs) con manifiestos SHA-256 (`data/processed/*/report.json`, `docs/datasets_reales_entrenamiento.md`).
4. **Entrenamiento real en Google Colab (2026-11-04):** Ejecución verificada con pesos `best.pt`, `results.csv` y `verificacion.json` para `yolo26n_plantvillage_classify`, `yolo26n_plantdoc_detect` y `yolo11n_plantdoc_detect`.
5. **Simulaciones matemáticas y scripts reproducibles:** Identificación paramétrica FOPDT, sintonización ZN/Cohen-Coon/IMC/Optuna, simulación biofísica agroclimática de 90 días y modelado de riesgo con BlightManager/XGBoost/SHAP.
6. **Pruebas automatizadas de software:** Suite Pytest (117 pruebas aprobadas), `django manage.py check` sin incidencias, linting `flake8` limpio y workflows CI en GitHub Actions.
7. **Redacción preliminar:** Portada, Resumen, Capítulo I y Capítulo II redactados en `thesis/borrador/TG-I Tesis alvaro rodrigo de la barra velasco 1.2.docx`.

### 5.2 Procedimientos aún NO realizados físicamente
- Adquisición física documentada, ensamblaje eléctrico del prototipo e impermeabilización/protección IP en La Paz.
- Calibración física en laboratorio de sensores (curva gravimétrica en estufa a 105 °C para el sensor capacitivo v1.2, contraste con termohigrómetro patrón).
- Ensayo real de respuesta al escalón en el invernadero prototipo físico (`[DATO FALTANTE]`).
- Captura, anotación agronómica experta (lesiones `<= 5%` y plagas/insectos sobre trampas amarillas) y entrenamiento real de visión en condiciones del invernadero de La Paz.
- Ejecución empírica de campo de los protocolos `E1` a `E8` (comparación Nivel 0 manual vs. Nivel 1 automatizado) con cultivo real de *Solanum tuberosum*.

---

## 6. Resultados Preliminares Verificados

### 6.1 Resultados reales en datasets públicos (Google Colab, verificados en `verificacion.json` y `resumen_evaluacion_final.csv`)
- **Clasificación foliar (`yolo26n_plantvillage_classify`, 25 épocas, 2.152 imgs, 3 clases):** `accuracy_top1 = 1.000` (100 %) en validación y prueba, `best.pt` de 3,19 MB. Limitación: fondo uniforme de laboratorio.
- **Detección foliar (`yolo26n_plantdoc_detect`, 40 épocas, 219 imgs, 2 clases, cajas de hoja completa):**
  - Validación: `Precision = 0.4690`, `Recall = 0.7453`, `mAP@0.50 = 0.6343`, `mAP@0.50:0.95 = 0.4699`.
  - Test final: `Precision = 0.4551`, `Recall = 0.5985`, `mAP@0.50 = 0.4926`, `mAP@0.50:0.95 = 0.3216` (`5.43 MB`).
- **Comparativa validación (`yolo11n_plantdoc_detect`, 43 épocas):** Validación `Precision = 0.5566`, `Recall = 0.5808`, `mAP@0.50 = 0.5918`, `mAP@0.50:0.95 = 0.3981` (`5.48 MB`). Seleccionado `yolo26n` en `seleccion_por_validacion.json`.

### 6.2 Resultados de simulación matemática (FOPDT, PID y Riesgo Fitopatológico)
- **Identificación FOPDT (sobre escalón simulado):** $K = 0,1639\,^\circ\text{C}/\%$, $\tau = 242,96\text{ s}$, $\theta = 33,33\text{ s}$, $R^2 = 0,9990$, $\text{RMSE} = 0,1178\,^\circ\text{C}$.
- **Comparativa PID (simulada):** Optuna ($K_p = 15,934$, $K_i = 0,1359$, $K_d = 1,571$) obtuvo $t_r = 230,0\text{ s}$, $t_s = 346,0\text{ s}$, $M_p = 1,61\%$, $e_{ss} \approx 0,00\,^\circ\text{C}$, $\text{IAE} = 1800,35$, $TV_u = 152,87$, reduciendo el IAE en $29,9\%$ y el esfuerzo de conmutación frente a On/Off ($\text{IAE} = 2566,79$, $M_p = 9,27\%$, $TV_u = 1900,0$).
- **Riesgo fitopatológico (datos sintéticos 90 días, test 432 h):** XGBoost calibrado isotónicamente alcanzó $\text{ROC-AUC} = 0,7123$, $\text{PR-AUC} = 0,7641$, $\text{Brier Score} = 0,1878$, $\text{F1-Score} = 0,6497$ (latencia CPU $0,038\text{ ms}$), siendo la variable `lwh_suma_48h` la de mayor importancia SHAP ($1,3257$).

---

## 7. Imágenes Disponibles

- **Gráficos científicos generados (12 PNG en `thesis/figuras/`):** `fig_fopdt_ajuste_escalon.png`, `fig_comparativa_sintonias_pid.png`, `fig_comparativa_onoff_vs_pid.png`, `fig_optuna_convergencia.png`, `fig_comparativa_map_modelos.png`, `fig_latencia_vs_map_cpu.png`, `fig_sahi_mejora_objetos_pequenos.png`, `fig_matriz_confusion_vision.png`, `fig_blightmanager_vs_ml_roc.png`, `fig_curvas_calibracion_probabilidad.png`, `fig_shap_importancia_bioclimatica.png`, `fig_simulacion_fusion_lazo_externo.png`.
- **Muestra visual de datasets reales:** `data/processed/vista_previa_datasets_reales.jpg`.
- **Imágenes de prueba y uploads:** 36 archivos en `data/raw/uploads/`, 11 en `data/raw/follaje/`, 12 en `data/raw/trampas/`, y muestras sintéticas en `data/dataset_yolo/`.
- **Diagramas vectoriales/JSON:** `diagramas/DIAisoflow.isoflow`, `diagramas/DIAisoflow.json`, `diagramas/circuito_esp32_invernadero.json`, `diagramas/wokwi_diagram.json`.
- **Ausentes:** Fotografías reales del prototipo físico construido, esquemático PCB/cableado fotografiado, capturas del invernadero y mapa geográfico de ubicación.

---

## 8. Fechas de Inicio/Avance y Lugar

- **Inicio del repositorio Git:** 2026-10-16 (commits `37528b2`, `100d381`, `c2df952`).
- **Simulaciones FOPDT/PID, visión sintética, Docker, FastAPI y Django v0.7.0:** 2026-10-21 a 2026-10-22.
- **Auditoría, curaduría de datasets reales y primeras pruebas de seguridad:** 2026-10-28 a 2026-10-29.
- **Reorganización Colab y entrenamiento verificado en GPU (`YOLO26n`/`YOLO11n`):** 2026-11-03 a 2026-11-04.
- **Último commit de desarrollo y corrección de endpoints:** 2026-11-09 (`b898902`).
- **Actualización del borrador Word (`TG-I...1.2.docx`):** 2026-11-12.
- **Lugar:** La Paz, Bolivia (~3.600 m s. n. m.), Universidad Salesiana de Bolivia (`[DATO FALTANTE: dirección exacta, macrodistrito/zona, altitud medida y dimensiones del invernadero/módulo experimental]`).
