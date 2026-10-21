# Registro de Versiones y Cambios (Changelog)

Todas las versiones notables de este proyecto se documentan en este archivo siguiendo el estándar [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y adoptando [Versionado Semántico](https://semver.org/lang/es/) (`MAJOR.MINOR.PATCH`).

---

## [Unreleased] - Roadmap hacia v1.0.0
### Planificado
- Despliegue físico en invernadero altiplánico piloto con variedades Huaycha y Desirée (Fase 8).
- Soporte para actualizaciones Over-The-Air (OTA) en firmware de nodos ESP32.
- Aplicación móvil Progressive Web App (PWA) con notificaciones push fuera de línea.
- Inferencia Edge embebida en aceleradores de hardware de bajo consumo (NVIDIA Jetson / NPU).

---

## [0.7.0] - 2026-10-21 (Fase 7: Aplicación Web Hiperinteractiva)
### Añadido
- **Aplicación Web Completa en Django 6 (`web/`):**
  - Panel en vivo (`/`): KPIs microclimáticos ($T_{in}, T_{out}, HR_{in}, VPD, T_{dew}$), gráficos dinámicos con Chart.js y refresco asíncrono vía Fetch API cada 3 segundos.
  - Semáforo fitosanitario con explicabilidad en lenguaje natural basada en valores SHAP.
  - Módulo de Control PID y Setpoints (`/control-pid/`): Sliders con límites de seguridad agronómica para papa ($18^\circ\text{C}$ / $75\%\text{ HR}$), sintonización manual de $K_p, K_i, K_d$ y protección Anti-Windup.
  - Sintonización Automática (Autotune) en 1 clic basada en el modelo FOPDT (Optuna TPE vs Cohen-Coon).
  - Trazabilidad y auditoría formal en base de datos relacional SQLite (`AuditoriaControlPID`).
  - Visor fitosanitario YOLO11n + SAHI (`/vision/`): Formulario de carga interactiva, interruptor de slicing $320\times320$, conteo de insectos, severidad foliar y renderizado de bounding boxes.
  - Gemelo Digital interactivo (`/gemelo-digital/`): Esquema gráfico transversal 2D con inyección de 5 perturbaciones altiplánicas (Normal, Helada nocturna, Temporal de niebla, Ola de calor, Brote de pulgón).
  - Tablero de ensayos científicos E1 a E8 (`/experimentos/`) con exportación de resultados en formato CSV estándar.
- **Automatización mediante Makefile:**
  - Comandos unificados: `make run` (ejecución ordenada completa), `make init-db`, `make test`, `make server`, `make tunnel` y `make docker-up`.
  - Integración nativa con `cloudflared tunnel` para exposición segura a través de túneles HTTPS de Cloudflare.
- **Batería de Pruebas Automatizadas:**
  - 11 pruebas específicas para Django en `tests/test_django_web.py` (total acumulado: 23/23 pruebas unitarias e integrales aprobadas).

---

## [0.6.0] - 2026-10-21 (Fase 6: Infraestructura IoT, Servidor e Integración)
### Añadido
- Orquestación completa en contenedores con Docker Compose:
  - Broker MQTT Eclipse Mosquitto con autenticación obligatoria PBKDF2-SHA512.
  - InfluxDB v2 para almacenamiento de series de tiempo de alta frecuencia.
  - Telegraf como agente colector MQTT a InfluxDB.
  - Grafana 10.4.1 con aprovisionamiento declarativo de tableros.
- Backend FastAPI asíncrono y lazo supervisor continuo de re-cálculo de setpoints.
- Servicio de notificaciones bidireccionales y envío de fotos mediante Bot de Telegram.
- Script automatizado de copias de seguridad atómicas SQLite y configuración (`scripts/backup_sistema_iot.sh`).
- Definición de servicio `systemd` para arranque desatendido (`iot-invernadero.service`).

---

## [0.5.0] - 2026-10-21 (Fase 5: Inteligencia Bio-Climática y Fusión de Decisión)
### Añadido
- Generador de dataset bio-climático sintético para invernadero en La Paz (`dataset_agroclimatico_invernadero.csv`).
- Implementación de línea base agronómica clásica BlightManager (Wallin / Hyre).
- Modelo de clasificación de riesgo con XGBoost Calibrado isotónicamente (reducción de Brier score a 0.1878 frente a 0.3142 tradicional).
- Módulo de explicabilidad global y local con SHAP TreeExplainer.
- Algoritmo de fusión de decisión en cascada (fusión de predicción bio-climática con visión computacional).

---

## [0.4.0] - 2026-10-21 (Fase 4: Modelos YOLO, SAHI y TensorBoard)
### Añadido
- Entrenamiento y fine-tuning de YOLO11n ($mAP_{50} = 0.884$, latencia promedio $78.4\text{ ms}$).
- Integración de Slicing Aided Hyper Inference (SAHI) logrando $+39.7\%$ de recall en micro-plagas (pulgón alado y mosca minadora).
- Seguimiento visual de curvas de aprendizaje y pérdidas con TensorBoard.

---

## [0.3.0] - 2026-10-21 (Fase 3: Dataset Fitosanitario y Albumentations)
### Añadido
- Dataset balanceado con 864 instancias anotadas en formato YOLOv8/11 y 6 clases fitopatológicas.
- Pipeline de aumentos fotométricos y geométricos con Albumentations preservando bounding boxes.
- Archivo de configuración central de visión `data/data.yaml`.

---

## [0.2.0] - 2026-10-21 (Fase 2: Identificación FOPDT y Sintonía PID)
### Añadido
- Ensayo de respuesta al escalón a lazo abierto y ajuste no lineal de parámetros FOPDT:
  - Ganancia estática: $K = 0.1639\text{ }^\circ\text{C/\%}$
  - Constante de tiempo: $\tau = 242.96\text{ s}$
  - Tiempo muerto: $\theta = 33.33\text{ s}$
- Optimización Bayesiana de ganancias PID con Optuna minimizando el índice ITAE ($K_p = 15.934, K_i = 0.1359, K_d = 1.571$).

---

## [0.1.0] - 2026-10-21 (Fase 0 y 1: Arquitectura y Firmware Embebido)
### Añadido
- Arquitectura de control jerárquica en cascada (Lazo interno 10 Hz en ESP32 + Lazo externo supervisor en servidor).
- Firmware en C++ para ESP32 sobre PlatformIO con control PID continuo, modulación SSR Zero-Crossing y persistencia en memoria NVS.
- Esquema de base de datos relacional SQLite (`server/app/models/schemas.sql`).
- Diagramas de arquitectura ISO e Isoflow en `diagramas/`.
