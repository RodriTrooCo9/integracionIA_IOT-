# Diagnóstico Técnico y Línea Base de Ingeniería (`01_diagnostico.md`)

**Proyecto:** Sistema Integrado IoT–PID–IA para Invernadero de Papa (La Paz, Bolivia — ~3600 msnm)  
**Rama / Commit base:** `fix/endpoints,django` @ `b898902` (tag `tesis-v1`)  
**Contrato de referencia:** [`00_contrato_tesis.md`](file:///home/rodrigo/Desktop/IOTtesis/mejoras/00_contrato_tesis.md)  
**Datos crudos de medición:** [`diagnostico_baseline.json`](file:///home/rodrigo/Desktop/IOTtesis/mejoras/benchmarks/diagnostico_baseline.json) y script reproducible [`run_baseline_audit.py`](file:///home/rodrigo/Desktop/IOTtesis/mejoras/benchmarks/run_baseline_audit.py)

---

## 1. Deducción del Proyecto, Stack Real y Recursos Medidos

### 1.1 Tipo de proyecto y arquitectura real
El repositorio combina dos planos acoplados:
1. **Plano científico/experimental (offline, congelado para la tesis):** generación de serie sintética agroclimática (`2160 h`), identificación FOPDT + sintonía PID con Optuna, evaluación comparativa de riesgo bioclimático (XGBoost + calibración isotónica + SHAP), curaduría de datasets reales (`PlantVillage` 2152 imgs, `PlantDoc` 219 imgs / 569 cajas) y entrenamiento de visión en Google Colab (`YOLO26n` / `YOLO11n`), más generación de tablas/figuras en `thesis/` y `tesis/`.
2. **Plano operativo multi-servicio:** firmware embebido ESP32 (`firmware/esp32_control/`), broker MQTT (`Mosquitto 2.0.18`), ingesta `Telegraf -> InfluxDB v2 -> Grafana`, API de inferencia (`FastAPI` en `server/`), worker supervisor en cascada (`server/app/worker.py`) y panel web monolítico (`Django 6.1.2` en `web/`) compartiendo una base SQLite (`data/invernadero_relacional.db`).

### 1.2 Stack real vs. declarado y recursos disponibles
Medición directa sobre el entorno de ejecución (13-nov-2026):

| Dimensión | Valor medido en entorno actual (`.venv`) | Especificado en `requirements.txt` / `ci.yml` | Brecha observada |
| :--- | :--- | :--- | :--- |
| **Hardware CPU / RAM** | `12th Gen Intel Core i5-12450H` (12 hilos), **6.92 GiB RAM total** (**1.3–1.6 GiB disponibles**, 11 GiB swap usado), sin GPU CUDA | — | Memoria muy ajustada para coexistencia Docker + PyTorch + Django |
| **Disco** | `177 GiB` libres; `data/` = **330.88 MB** (`processed/` 188.36 MB, `raw/` 117.83 MB, `models/` 15.57 MB, `synthetic/` 0.235 MB); `backups/` = **58.96 MB** | — | Aceptable en disco; `data/` no está versionado |
| **Python / Core** | `Python 3.14.4`, `Django 6.1.2`, `FastAPI 0.157.0`, `Pydantic 2.14.1`, `httpx 0.28.1`, `paho-mqtt 2.1.0`, `numpy 2.5.4`, `scipy 1.18.1`, `pytest 9.1.1` | CI usa `Python 3.11`, `fastapi==0.110.0`, `pydantic==2.6.4`, `httpx<0.28`, `paho-mqtt==1.6.1`, `numpy==1.26.4` | **Deriva severa de versiones**; además `influxdb-client`, `control` y `python-telegram-bot` faltan en `.venv` |
| **Stack IA / Visión** | `torch 2.14.1+cpu`, `ultralytics 8.4.183`, `sahi 0.12.8`, `opencv-python-headless 5.0.0.93`, `xgboost 3.4.1`, `shap 0.54.1`, `optuna 5.0.0` | `server/requirements.txt` omite `ultralytics`, `sahi`, `torch`, `opencv-python-headless`, `python-multipart` y pide `python-control==0.10.1` | **Imagen Docker del servidor (`server/Dockerfile`) inutilizable** en runtime para visión/upload |

### 1.3 Métricas de línea base medidas (sin suposiciones)
- **Pruebas y verificación estática:**
  - `.venv/bin/pytest tests/ -q`: **`117 passed, 1 warning in 3.33s`** (real wall `5.37s`; warning de deprecación `httpx`/`Starlette`).
  - `web/manage.py check`: **0 issues** (`0.26s`).
  - `docker compose config --quiet`: **válido**.
  - `flake8` crítico (`E9,F63,F7,F82`): **0 errores**.
  - `flake8` estilo/complejidad (`--max-complexity=15 --max-line-length=127`): **595 avisos** (`175 E501`, `132 W293`, `83 E302`, `46 F401`, `17 E402`, `10 F811`, etc.). Con umbral `C901 > 10` aparecen **17 funciones** complejas (hasta `29` en `iniciar_colab`, `22` en `repair_dataset`, `19` en `VisionInferenceService.procesar_imagen` y `generar_dataset_invernadero`, `17` en `api_subir_imagen_vision`).
  - Integridad de tesis: `verificar_integridad.py` -> **`77/77` archivos verificados**.
- **Tamaño de código (`server`, `web`, `scripts`, `firmware`, `tests`, `config`):** `74` archivos relevantes (`12,453` líneas totales / `11,096` no vacías).
- **Latencias CPU medidas (promedio / p95):**
  - `yolo26n_plantvillage_classify` (`3.04 MB`, carga fría `11.79 ms`): **`9.28 ms`** (`p95 = 9.65 ms`).
  - `yolo26n_plantdoc_detect` (`5.18 MB`, carga fría `31.46 ms`): **`44.92 ms`** (`p95 = 47.41 ms`); con **SAHI 320×320**: **`249.78 ms`** (`máx = 301.40 ms`).
  - `yolo11n_plantdoc_detect` (`5.23 MB`, carga fría `34.17 ms`): **`48.25 ms`** (`p95 = 50.21 ms`).
  - `heuristica_trampa_hsv`: **`3.75 ms`** (`p95 = 7.26 ms`).
  - **Huella RAM RSS pico del proceso Python** al cargar PyTorch + Ultralytics + catálogo de modelos: **`881.18 MB`** (en un host con solo `1.6 GiB` libres).
  - Endpoints FastAPI (`TestClient`): `GET /api/v1/health` **`2.30 ms`**, `POST /api/v1/control/setpoints` **`2.75 ms`**, `POST /api/v1/vision/inferir` (YOLO26n detect real) **`98.60 ms`** (`p95 = 109.67 ms`).
  - Endpoints Django (`Client`): `GET /` **`5.74 ms`**, `GET /experimentos/` **`2.36 ms`**, `GET /api/telemetria/` **`0.26 ms`**.
  - Pipeline Fase 5 (en memoria, `2160` filas): generación sintética `13.17 ms`, ingeniería de 24 features `5.23 ms`, entrenamiento + calibración XGBoost `232.62 ms`, inferencia batch 432 filas **`0.629 ms`**, SHAP `31.34 ms` (`ROC-AUC = 0.7123`, `Brier = 0.1878`).
- **Base de datos SQLite (`data/invernadero_relacional.db`, `0.223 MB`):** ya opera en modo `wal` (`synchronous = 2`), `5` tablas operativas (`nodos_sensores: 4`, `detecciones_vision: 5`, `eventos_alarmas: 11`, `auditoria_control_pid: 41`, `experimentos_ensayos: 8` sin duplicados) + tablas internas Django (`18` migraciones).

---

## 2. Hallazgos Principales y Cuellos de Botella por Área

### 2.1 Arquitectura y Calidad de Código
1. **Acoplamiento y duplicación entre Django (`web/`) y FastAPI (`server/`):** [`web/dashboard/views.py`](file:///home/rodrigo/Desktop/IOTtesis/web/dashboard/views.py) importa directamente `vision_service`, `mqtt_service` y `server_settings` en el mismo proceso WSGI que Django (`Backend` + `Web` cargan por separado PyTorch/YOLO en RAM ~880 MB c/u y abren clientes MQTT independientes). Además, la lógica de inferencia/guardado en [`api_subir_imagen_vision`](file:///home/rodrigo/Desktop/IOTtesis/web/dashboard/views.py#L390-L517) (`128` líneas, complejidad `C901=17`) duplica [`inferir_imagen`](file:///home/rodrigo/Desktop/IOTtesis/server/app/api/endpoints.py#L81-L194) (`114` líneas).
2. **Incompatibilidad silenciosa MQTT entre Firmware ESP32, Servidor y Django:**
   - [`config_invernadero.h`](file:///home/rodrigo/Desktop/IOTtesis/firmware/esp32_control/include/config_invernadero.h#L60-L61) suscribe a `invernadero/control/setpoint` (singular) y `invernadero/control/ganancias`, esperando llaves JSON `"sp_temp"` y `"sp_hum"` ([`main.cpp`](file:///home/rodrigo/Desktop/IOTtesis/firmware/esp32_control/src/main.cpp#L250-L262)), y llama a `mqttClient.connect(MQTT_CLIENT_ID)` sin usuario/contraseña ([`main.cpp`](file:///home/rodrigo/Desktop/IOTtesis/firmware/esp32_control/src/main.cpp#L288)) contra un Mosquitto con `allow_anonymous false`.
   - En contraste, FastAPI/Worker/Simulador publican en `invernadero/control/setpoints` (plural) con llaves `"sp_temperatura"` y `"sp_humedad"`, y Django publica ganancias en `invernadero/control/pid_tuning`. *(Nota: `firmware.bin` está congelado por SHA-256 en el contrato, por lo que la interoperabilidad debe resolverse desde el lado servidor/puente o modo dual compatible sin recompilar `firmware.bin`).*
3. **Bug de callback `paho-mqtt` v2 en simulador:** [`simulador_esp32_mqtt.py`](file:///home/rodrigo/Desktop/IOTtesis/scripts/simulador_esp32_mqtt.py#L61-L95) instancia `CallbackAPIVersion.VERSION2` pero define `on_connect(client, userdata, flags, rc)` con 4 argumentos en vez de 5 (`reason_code, properties`), lo que falla con `TypeError` bajo `paho-mqtt 2.1.0`.
4. **Rutas absolutas fijas (`/home/rodrigo/Desktop/IOTtesis`) y funciones monolíticas:** 5 ocurrencias en [`ejecutar_fase5_riesgo_fusion.py`](file:///home/rodrigo/Desktop/IOTtesis/scripts/ejecutar_fase5_riesgo_fusion.py#L212), [`generar_dataset_agroclimatico.py`](file:///home/rodrigo/Desktop/IOTtesis/scripts/generar_dataset_agroclimatico.py#L214) y [`backup_sistema_iot.sh`](file:///home/rodrigo/Desktop/IOTtesis/scripts/backup_sistema_iot.sh#L10). La función `main()` de Fase 5 tiene `373` líneas.

### 2.2 Pipelines IA (Entrenamiento e Inferencia)
1. **Brecha entre Fase 5 (XGBoost + SHAP) y el Worker en producción ([`worker.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/worker.py#L84-L120)):** [`ejecutar_fase5_riesgo_fusion.py`](file:///home/rodrigo/Desktop/IOTtesis/scripts/ejecutar_fase5_riesgo_fusion.py) entrena y calibra `XGBoost` (`0.629 ms` batch / `<0.05 ms` por muestra) pero **no exporta ni serializa el modelo** (`scaler`, `xgb_base`, `iso_xgb`). Como resultado, `worker.py` usa una regla heurística fija (`if lwh_max >= 10: p_clima += 0.50`) y [`web/dashboard/services.py`](file:///home/rodrigo/Desktop/IOTtesis/web/dashboard/services.py#L383-L441) simula la "explicabilidad SHAP" con umbrales `if/elif` estáticos.
2. **Condición de carrera y estado en memoria en `worker.py`:** `_on_message` corre en el hilo de `paho-mqtt` y muta `self.buffer_clima` (`deque`) sin `threading.Lock` mientras `calcular_fusion_multimodal()` itera sobre él en el bucle `asyncio` (`RuntimeError: deque mutated during iteration` bajo carga). Además, el log anuncia `30 segundos` pero duerme `15 s`, y `sp_anterior=18.0` está hardcodeado en [`worker.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/worker.py#L182) y [`endpoints.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/api/endpoints.py#L211).
3. **Carga ansiosa y memoria de Visión (`vision_service.py`):** Importar [`vision_service.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/services/vision_service.py#L352) carga de inmediato PyTorch + modelo por defecto (~`880 MB` RSS), incluso en procesos que solo consultan APIs o corren pruebas. Cachear múltiples modelos (`_SERVICIOS_CACHE`) en el mismo proceso con solo `1.3–1.6 GiB` RAM disponibles empuja al sistema a swap. Tampoco existe exportación/inferencia opcional en **ONNX Runtime** (aunque `onnx 1.23.2` está instalado) para reducir RAM y latencia CPU de SAHI (`250 ms`).
4. **Script Fase 4 con métricas fijas y notebooks desalineados:** [`ejecutar_fase4_evaluacion_vision.py`](file:///home/rodrigo/Desktop/IOTtesis/scripts/ejecutar_fase4_evaluacion_vision.py#L38-L76) usa valores hardcodeados pre-Colab (`mAP50=0.884`) en vez de leer [`verificacion.json`](file:///home/rodrigo/Desktop/IOTtesis/data/models/entrenados_colab/verificacion.json), y `X_val_seq` en [`ejecutar_fase5_riesgo_fusion.py`](file:///home/rodrigo/Desktop/IOTtesis/scripts/ejecutar_fase5_riesgo_fusion.py#L347) se construye pero nunca se usa (el LSTM entrena 25 épocas fijas sin validación ni early stopping).

### 2.3 Datos, SQLite y Almacenamiento
1. **Concurrencia SQLite multi-proceso sin `busy_timeout`:** Aunque `data/invernadero_relacional.db` ya está en modo `WAL`, ni [`database.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/services/database.py#L20-L27) (`aiosqlite` abriendo conexión nueva por cada query) ni [`settings.py`](file:///home/rodrigo/Desktop/IOTtesis/web/invernadero_web/settings.py#L73-L78) configuran `PRAGMA busy_timeout = 5000` / `timeout: 20` ni reutilizan pool/conexión, arriesgando `database is locked` cuando FastAPI, Worker y Django escriben simultáneamente.
2. **Almacenamiento de imágenes subidas sin cuota ni limpieza:** `data/raw/uploads` crece indefinidamente con cada inferencia (`original` + `anotada_`), sin límite de tamaño en `UploadFile` (`inferir_imagen` ni `api_subir_imagen_vision`), ni política de retención.

### 2.4 Escalabilidad, Configuración, Docker y Seguridad
1. **Credenciales y secretos en el repositorio:**
   - [`config/mosquitto/passwd`](file:///home/rodrigo/Desktop/IOTtesis/config/mosquitto/passwd) está **trackeado en Git**.
   - Claves y tokens por defecto embebidos en [`web/invernadero_web/settings.py`](file:///home/rodrigo/Desktop/IOTtesis/web/invernadero_web/settings.py#L23) (`SECRET_KEY` + `DEBUG = True` + `ALLOWED_HOSTS = ["*"]`), [`server/app/core/config.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/core/config.py#L27-L51), [`docker-compose.yml`](file:///home/rodrigo/Desktop/IOTtesis/docker-compose.yml#L43-L156), [`.env.example`](file:///home/rodrigo/Desktop/IOTtesis/.env.example) y [`config_invernadero.h`](file:///home/rodrigo/Desktop/IOTtesis/firmware/esp32_control/include/config_invernadero.h#L52).
2. **Endpoints críticos totalmente abiertos (sin autenticación ni límites):**
   - Los 5 POST mutantes de Django tienen `@csrf_exempt` ([`views.py`](file:///home/rodrigo/Desktop/IOTtesis/web/dashboard/views.py#L227-L389)) y están expuestos al exterior cuando se levanta `make run` (Cloudflare Tunnel). `api_actualizar_pid` ni siquiera valida rangos finitos/no-negativos de `Kp, Ki, Kd`.
   - En FastAPI, [`endpoints.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/api/endpoints.py#L250) expone `POST /api/v1/telegram/notificar` sin auth y acepta un `ruta_foto` arbitrario en el sistema de archivos local (**riesgo de LFI / exfiltración de archivos vía Telegram** si `TELEGRAM_BOT_TOKEN` está activo).
   - [`main.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/main.py#L46-L52) configura `CORSMiddleware` con `allow_origins=["*"]` + `allow_credentials=True` (combinación insegura/inválida según especificación CORS).
3. **Bloqueo del event loop en FastAPI:** [`inferir_imagen`](file:///home/rodrigo/Desktop/IOTtesis/server/app/api/endpoints.py#L103-L117) realiza `open()` + `shutil.copyfileobj()` síncrono en un `async def`, y si recibe un `modelo_id` no cacheado ejecuta `obtener_servicio_modelo(modelo_id)` (carga de pesos YOLO + SAHI) en el event loop en lugar de `asyncio.to_thread`. Igual [`telegram_bot.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/services/telegram_bot.py#L93) abre archivos síncronamente dentro de `async def` y su heurística `"token" in token_str` ([L26](file:///home/rodrigo/Desktop/IOTtesis/server/app/services/telegram_bot.py#L26)) puede invalidar tokens reales que contengan la subcadena `"token"` o `"tu_"`.
4. **`server/Dockerfile` y `server/requirements.txt` rotos para build limpio:**
   - [`server/Dockerfile`](file:///home/rodrigo/Desktop/IOTtesis/server/Dockerfile#L31) ejecuta `COPY data/invernadero_relacional.db ...` (falla en CI si la BD local no existe, e incrusta datos de runtime en la imagen), no define `USER` no-root, no tiene `.dockerignore`.
   - [`server/requirements.txt`](file:///home/rodrigo/Desktop/IOTtesis/server/requirements.txt) falla al instalar `python-control==0.10.1` (paquete inexistente en PyPI; es `control`), y omite `opencv-python-headless`, `ultralytics`, `sahi` y `python-multipart` necesarios para arrancar `server.app.main`.

### 2.5 Calidad, Tooling y CI/CD
- `ci.yml` ejecuta `flake8 --select=E9,F63,F7,F82` y `--exit-zero` en estilo, por lo que los `595` avisos y `17` funciones `C901 > 10` pasan inadvertidos; no ejecuta `mypy`, `bandit`/`pip-audit` ni cobertura de tests (`pytest --cov`).
- `requirements.txt` raíz tiene versiones fijadas incompatibles con `.venv` (`Python 3.14.4` + `FastAPI 0.157` + `Pydantic 2.14` + `NumPy 2.5`), generando riesgo de "funciona en mi máquina, falla en CI (Python 3.11)" o viceversa.

---

## 3. Matriz Priorizada de Hallazgos (Impacto vs. Esfuerzo vs. Riesgo para "Modo Tesis")

| ID | Hallazgo | Área | Impacto | Esfuerzo | Riesgo Modo Tesis |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **H1** | `server/Dockerfile` + `server/requirements.txt` rotos (`COPY .db`, `python-control`, falta `cv2`/`ultralytics`/`python-multipart`) + falta `.dockerignore` | Docker / Deploy | **Crítico** | Bajo | **Nulo** |
| **H2** | Riesgo LFI en `/api/v1/telegram/notificar` (`ruta_foto` sin restringir), CORS `*`+credentials, y falta validación de tamaño/tipo en uploads + rangos PID | Seguridad | **Crítico** | Bajo | **Nulo** (si defaults test siguen pasando) |
| **H3** | Race condition en `worker.py` (`buffer_clima` sin `Lock`), `sp_anterior=18.0` hardcodeado y fallo `on_connect` v2 en `simulador_esp32_mqtt.py` | Concurrencia / IoT | **Alto** | Bajo | **Nulo** |
| **H4** | Concurrencia SQLite multi-proceso sin `busy_timeout`, ni WAL explícito al conectar en `database.py` y Django `settings.py` | Datos / BD | **Alto** | Bajo | **Nulo** |
| **H5** | Bloqueos síncronos en `async def` (`shutil.copyfileobj`, `obtener_servicio_modelo` en event loop, `open()` en `telegram_bot.py`) y lazy-load ausente en `vision_service` | Rendimiento / RAM | **Alto** | Medio | **Bajo** |
| **H6** | Desacople MQTT entre Servidor (`setpoints`, `sp_temperatura`) y Firmware ESP32 (`setpoint`, `sp_temp`) sin tocar `firmware.bin` | Interoperabilidad | **Alto** | Bajo | **Nulo** (dual-publish opt-in/aditivo) |
| **H7** | Secretos/configuración insegura (`DEBUG=True`, `SECRET_KEY` fijo en Django, `ALLOWED_HOSTS`, `passwd` trackeado) sin soporte completo `.env` | Seguridad / Config | **Alto** | Medio | **Bajo** (preservando fallbacks dev/test) |
| **H8** | Rutas absolutas `/home/rodrigo/...` en scripts (`fase5`, `generar_dataset`, `backup_sistema_iot.sh`) y desalineación de dependencias `.venv` vs `requirements.txt` | Portabilidad / CI | **Medio** | Bajo | **Nulo** |
| **H9** | Exportar artefactos entrenados de Fase 5 (`XGBoost + Isotonic + Scaler`) como puente opt-in para `worker.py` y SHAP real | IA / MLOps | **Medio** | Medio | **Bajo** (regla heurística intacta por defecto) |
| **H10** | Reducir complejidad (`C901 > 15` en `api_subir_imagen_vision`, `procesar_imagen`, `actualizar_gemelo_digital`), limpiar imports muertos (`46 F401`) y activar cobertura/seguridad en CI | Calidad / Mantenimiento | **Medio** | Medio | **Nulo** |

---

## 4. Top 10 de Mejoras de Mayor Valor y Menor Riesgo (Para Aprobación)

Cada mejora respeta estrictamente [`00_contrato_tesis.md`](file:///home/rodrigo/Desktop/IOTtesis/mejoras/00_contrato_tesis.md): **cero ediciones en `/tesis/*`, `/thesis/*`, datasets, modelos Colab o `firmware.bin`**.

### 1. Reparar `server/Dockerfile`, `server/requirements.txt` y añadir `.dockerignore`
- **Qué toca:** [`server/Dockerfile`](file:///home/rodrigo/Desktop/IOTtesis/server/Dockerfile), [`server/requirements.txt`](file:///home/rodrigo/Desktop/IOTtesis/server/requirements.txt), nuevo `.dockerignore` (opcionalmente ajuste de `docker-compose.yml` para no depender de `.db` horneado).
- **Métrica que mejora:** `docker build -f server/Dockerfile .` pasa de **fallo garantizado (`0%` build / `ModuleNotFoundError: cv2`)** a **100% build reproducible**, eliminando ~330 MB de contexto innecesario (`data/`, `.venv/`, `tesis/`, `backups/`) y ejecutando como usuario no-root.
- **Por qué no rompe el modo tesis:** Solo corrige el empaquetado del contenedor (`control` en vez de `python-control`, incluir `opencv-python-headless`, `ultralytics`, `sahi`, `python-multipart` y quitar `COPY data/invernadero_relacional.db`); no altera lógica, métricas ni endpoints.
- **Commit / Fase:** Fase 2 — Commit `C1` (Infraestructura, Contenedores y Portabilidad).

### 2. Endurecer seguridad de endpoints sin romper pruebas ni modo demo (Path traversal, CORS, Upload limit, Rangos PID y Auth opt-in)
- **Qué toca:** [`server/app/api/endpoints.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/api/endpoints.py), [`server/app/services/telegram_bot.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/services/telegram_bot.py), [`server/app/main.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/main.py), [`web/dashboard/views.py`](file:///home/rodrigo/Desktop/IOTtesis/web/dashboard/views.py).
- **Métrica que mejora:** Hallazgos críticos de seguridad de **5 a 0**: (a) restringir `ruta_foto` en `/telegram/notificar` a `UPLOAD_DIR` / `BASE_DIR/data` (bloquea LFI); (b) corregir `esta_configurado` en `telegram_bot.py` para no rechazar tokens válidos con `"token"`; (c) limitar tamaño de imagen subida (ej. `MAX_UPLOAD_MB=10`) y validar magic bytes/extensiones; (d) validar rangos físicos de `Kp/Ki/Kd` (`>= 0`, finitos) en Django `api_actualizar_pid`; (e) corregir CORS (`ALLOWED_ORIGINS` configurable, sin `*` + `allow_credentials=True` simultáneo) y añadir soporte **opt-in** de `API_AUTH_TOKEN` (desactivado por defecto en modo tesis/pytest, activable para Cloudflare Tunnel).
- **Por qué no rompe el modo tesis:** Los rangos Pydantic `SetpointsRequest` (`5..35`, `30..95`) y las `117` pruebas de `pytest` sin token siguen funcionando idénticas por defecto; los modos seguros se activan vía variables de entorno.
- **Commit / Fase:** Fase 2 — Commit `C2` (Hardening de Seguridad y Configuración).

### 3. Configuración segura por entorno en Django/FastAPI y limpieza de rutas absolutas fijas
- **Qué toca:** [`web/invernadero_web/settings.py`](file:///home/rodrigo/Desktop/IOTtesis/web/invernadero_web/settings.py), [`server/app/core/config.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/core/config.py), [`scripts/ejecutar_fase5_riesgo_fusion.py`](file:///home/rodrigo/Desktop/IOTtesis/scripts/ejecutar_fase5_riesgo_fusion.py), [`scripts/generar_dataset_agroclimatico.py`](file:///home/rodrigo/Desktop/IOTtesis/scripts/generar_dataset_agroclimatico.py), [`scripts/backup_sistema_iot.sh`](file:///home/rodrigo/Desktop/IOTtesis/scripts/backup_sistema_iot.sh).
- **Métrica que mejora:** `hardcoded_home_paths` de **`5` a `0`**; Django `DEBUG`, `SECRET_KEY` y `ALLOWED_HOSTS` leídos desde `os.getenv` (usando `BASE_DIR` relativo en scripts); `backup_sistema_iot.sh` con `BASE_DIR` dinámico y exclusión opcional de `.env` en backups sin cifrar.
- **Por qué no rompe el modo tesis:** Se mantienen exactamente los mismos valores fallback cuando no existen variables de entorno, y los scripts Fase 5 / generador siguen produciendo exactamente los mismos CSV (`seed=42`, `Brier=0.1878`, `ROC-AUC=0.7123`) desde cualquier ruta/usuario (incluido CI).
- **Commit / Fase:** Fase 2 — Commit `C1` / `C2`.

### 4. Robustez SQLite WAL multi-proceso y trazabilidad real de `sp_anterior`
- **Qué toca:** [`server/app/services/database.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/services/database.py), [`web/invernadero_web/settings.py`](file:///home/rodrigo/Desktop/IOTtesis/web/invernadero_web/settings.py), [`server/app/api/endpoints.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/api/endpoints.py), [`server/app/worker.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/worker.py).
- **Métrica que mejora:** Elimina errores `database is locked` bajo acceso concurrente FastAPI+Worker+Django (`PRAGMA busy_timeout = 5000`, `PRAGMA journal_mode = WAL`, `PRAGMA synchronous = NORMAL` en `aiosqlite` y `OPTIONS: {"timeout": 20}` en Django) y reemplaza `sp_anterior=18.0` hardcodeado por consulta del último setpoint registrado en `auditoria_control_pid` (con fallback `18.0`).
- **Por qué no rompe el modo tesis:** Conserva intactas las 5 tablas de `schemas.sql`, todas las filas semilla y la firma de los endpoints; si la tabla está vacía, el fallback sigue siendo `18.0`.
- **Commit / Fase:** Fase 3 — Commit `C3` (Concurrencia, BD y Estabilidad IoT).

### 5. Corregir thread-safety en `SupervisorWorker` y callback MQTT v2 en `simulador_esp32_mqtt.py`
- **Qué toca:** [`server/app/worker.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/worker.py), [`scripts/simulador_esp32_mqtt.py`](file:///home/rodrigo/Desktop/IOTtesis/scripts/simulador_esp32_mqtt.py).
- **Métrica que mejora:** `0` excepciones `RuntimeError` por mutación concurrente de `buffer_clima` (`threading.Lock` al leer/escribir buffer y última detección); `simulador_esp32_mqtt.py` pasa de **fallo inmediato con `paho-mqtt>=2.0`** a **conexión funcional** (firma compatible v1/v2 en `on_connect`); consistencia de log/intervalo configurable (`WORKER_INTERVAL_S`, default `15s` preservado).
- **Por qué no rompe el modo tesis:** La ecuación exacta de fusión (`0.45*clima + 0.35*vision + 0.20*tend`), umbrales (`0.30/0.55/0.75`), `deque(maxlen=48)` y setpoints comandados no cambian en absoluto.
- **Commit / Fase:** Fase 3 — Commit `C3`.

### 6. Puente MQTT aditivo (dual-publish opt-in) entre Servidor y Firmware ESP32 congelado
- **Qué toca:** [`server/app/core/config.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/core/config.py), [`server/app/api/endpoints.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/api/endpoints.py), [`server/app/worker.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/worker.py), [`web/dashboard/views.py`](file:///home/rodrigo/Desktop/IOTtesis/web/dashboard/views.py).
- **Métrica que mejora:** Tasa de entrega efectiva de comandos de setpoint/PID desde FastAPI/Worker/Django hacia el firmware ESP32 pasa de **`0%` (tópico y llaves JSON distintas) a `100%`**, añadiendo publicación espejo configurable (`MQTT_COMPAT_ESP32_LEGACY=true` o publicación secundaria en `invernadero/control/setpoint` con `sp_temp`/`sp_hum` y `invernadero/control/ganancias`) sin modificar ni recompilar `firmware/esp32_control/`.
- **Por qué no rompe el modo tesis:** Los tópicos primarios del servidor (`invernadero/control/setpoints`), sus payloads y el binario `firmware.bin` (`818.992 bytes`, SHA-256 congelado) permanecen **100% intactos**.
- **Commit / Fase:** Fase 3 — Commit `C3`.

### 7. Eliminar bloqueos síncronos en FastAPI `async` y carga perezosa (lazy-load) de modelos de Visión
- **Qué toca:** [`server/app/api/endpoints.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/api/endpoints.py), [`server/app/services/vision_service.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/services/vision_service.py), [`server/app/services/telegram_bot.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/services/telegram_bot.py).
- **Métrica que mejora:** Reduce el **RSS base al importar `vision_service`** (actualmente ~`881 MB` incluso si no se infiere) mediante inicialización diferida opcional (`VISION_LAZY_LOAD`) + límite LRU (`max_cached_models`) acorde a `6.9 GiB` RAM, y mueve la escritura de uploads, lectura de foto Telegram y `obtener_servicio_modelo(modelo_id)` fuera del event loop (`asyncio.to_thread`), evitando bloqueos de `30–300 ms` sobre `/health` y `/control/setpoints`.
- **Por qué no rompe el modo tesis:** Los resultados de inferencia, `CLASES_PAPA`, validación de `.metadata.json`, `VISION_DEMO_MODE=false` y estado de `/health` (`vision.disponible`) pueden preservarse en `app` startup o bajo `VISION_LAZY_LOAD=false` por defecto.
- **Commit / Fase:** Fase 3 — Commit `C4` (Rendimiento CPU/RAM y Pipeline IA).

### 8. Aceleración CPU opcional (opt-in) de Visión mediante exportación/inferencia ONNX Runtime
- **Qué toca:** [`server/app/services/vision_service.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/services/vision_service.py), [`scripts/`](file:///home/rodrigo/Desktop/IOTtesis/scripts/) (script auxiliar de benchmark/exportación hacia `mejoras/` o `runs/`).
- **Métrica que mejora:** Sobre la línea base medida en CPU (`yolo26n_plantdoc_detect` = **`44.92 ms`**, SAHI 320×320 = **`249.78 ms`**, RAM pico `881 MB`), permite habilitar `VISION_BACKEND=onnx` (opt-in) para reducir latencia por frame/mosaico SAHI y evitar dependencia de PyTorch completo en inferencia edge. *(Se medirá ganancia real tras exportar en Fase 3).*
- **Por qué no rompe el modo tesis:** El backend por defecto sigue siendo PyTorch (`best.pt` original congelado), manteniendo idénticos SHA-256, `mAP50=0.6343` y salidas por defecto; ONNX es estrictamente opt-in y verificable contra las salidas `.pt`.
- **Commit / Fase:** Fase 3 — Commit `C4`.

### 9. Puente MLOps opt-in de Fase 5 (XGBoost calibrado + SHAP real) hacia `worker.py` y Django
- **Qué toca:** [`scripts/ejecutar_fase5_riesgo_fusion.py`](file:///home/rodrigo/Desktop/IOTtesis/scripts/ejecutar_fase5_riesgo_fusion.py) (guardado opcional `--export-model` fuera de archivos congelados), [`server/app/worker.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/worker.py), [`web/dashboard/services.py`](file:///home/rodrigo/Desktop/IOTtesis/web/dashboard/services.py).
- **Métrica que mejora:** Permite que el lazo supervisor y el dashboard usen el modelo real **`XGBoost Calibrado` (`Brier 0.1878`, `ROC-AUC 0.7123`, `0.63 ms` batch)** y valores **SHAP reales** (con `WORKER_USE_XGBOOST=true`), en vez de reglas estáticas `if/elif`, cuando exista historial suficiente en el buffer.
- **Por qué no rompe el modo tesis:** Por defecto (`WORKER_USE_XGBOOST=false` o sin artefacto exportado), `worker.py` ejecuta la heurística exacta documentada en [`00_contrato_tesis.md`](file:///home/rodrigo/Desktop/IOTtesis/mejoras/00_contrato_tesis.md#L74-L77), y Fase 5 sigue generando idénticos `Brier=0.1878` y `ROC-AUC=0.7123` con `SEED=42`.
- **Commit / Fase:** Fase 3 — Commit `C4`.

### 10. Refactorización de complejidad (`C901`), higiene `flake8` y fortalecimiento de CI/Makefile
- **Qué toca:** [`web/dashboard/views.py`](file:///home/rodrigo/Desktop/IOTtesis/web/dashboard/views.py), [`web/dashboard/services.py`](file:///home/rodrigo/Desktop/IOTtesis/web/dashboard/services.py), [`server/app/services/vision_service.py`](file:///home/rodrigo/Desktop/IOTtesis/server/app/services/vision_service.py), [`.github/workflows/ci.yml`](file:///home/rodrigo/Desktop/IOTtesis/.github/workflows/ci.yml), [`Makefile`](file:///home/rodrigo/Desktop/IOTtesis/Makefile), [`requirements.txt`](file:///home/rodrigo/Desktop/IOTtesis/requirements.txt).
- **Métrica que mejora:** Reduce avisos `flake8` de **`595` a `< 50`** (eliminando `46 F401`, `132 W293`, `175 E501`), baja la complejidad ciclomática máxima en `server/` y `web/` de **`C901=19` a `<= 10`**, alinea `requirements.txt` / `ci.yml` con las versiones probadas, añade verificación automática de `mejoras/_baseline/verificar_integridad.py` y pruebas unitarias nuevas en CI.
- **Por qué no rompe el modo tesis:** Refactorización puramente estructural con comportamiento externo idéntico, validada al final de cada commit con `pytest` (`>= 117` tests) + `verificar_integridad.py` (`77/77` SHA-256 intactos).
- **Commit / Fase:** Fase 4 — Commit `C5` (Calidad, Limpieza, Tests de Regresión y CI).
