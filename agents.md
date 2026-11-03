# Documento de Contexto y Directrices para Agentes: Proyecto Tesis IoT-PID-IA

## 1. Declaracion de Mision y Arquitectura Global

Este repositorio contiene la implementacion formal del proyecto de grado:
"Prototipo de Sistema Integrado IoT-PID-Inteligencia Artificial para la Regulacion Microclimatica y Deteccion Temprana de Plagas en el Cultivo de Papa bajo Invernadero (La Paz, Bolivia)".

El sistema opera bajo una estructura de control jerarquico en cascada de dos niveles:
1. Lazo Inferior (Rapido y Embebido): Ejecutado en microcontrolador ESP32 a 10 Hz para control PID continuo en lazo cerrado de temperatura y humedad, utilizando modulacion por ancho de pulso con rele de estado solido (SSR con cruce por cero) y extraccion forzada por PWM. Dispone de logica de seguridad local (fail-safe) que preserva la operacion autonoma del cultivo si se pierde la conexion de red con el servidor.
2. Lazo Superior (Supervisor e Inteligente): Ejecutado en un servidor local multi-contenedor bajo Docker Compose. Gestiona la ingesta de telemetria via broker MQTT Mosquitto, almacenamiento en base de datos de series temporales InfluxDB v2 a traves de Telegraf, almacenamiento relacional SQLite para vision y alarmas, servicio backend FastAPI para inferencia de vision (YOLO26 / YOLO11 + SAHI) y estimacion fitopatologica de riesgo (algoritmo BlightManager + Machine Learning con explicabilidad SHAP), tablero Grafana y panel web operativo interactivo en Django. Este lazo supervisor ajusta dinamicamente los puntos de consigna (setpoints) comandados al ESP32.

Contexto agroclimatico especifico: Altiplano boliviano (La Paz, altitud media de 3600 msnm), caracterizado por una presion atmosferica reducida (67.5 kPa), noches con heladas recurrentes, amplitudes termicas diurnas de mas de 20 grados Celsius y eventos de alta humedad relativa (nieblas andinas) que activan el desarrollo epidemico del Tizon Tardio (Phytophthora infestans) y plagas asociadas como pulgones (Macrosiphum euphorbiae) y mosca minadora (Liriomyza huidobrensis).

---

## 2. Inventario y Estructura del Repositorio

El arbol de carpetas del proyecto se distribuye de la siguiente manera:

* config/: Archivos de configuracion declarativos del sistema.
  - mosquitto/: Configuracion del broker MQTT Mosquitto (puertos 1883 y 9001 WebSockets) y credenciales de acceso.
  - telegraf/: Configuracion del agente Telegraf para recoleccion de topicos MQTT y escritura en InfluxDB v2.
  - grafana/: Aprovisionamiento automatico de orígenes de datos (datasources) y cuadros de mando (dashboards).
  - systemd/: Definicion de servicio systemd para despliegue en servidor fisico.
* data/: Gestion y almacenamiento local de datos.
  - raw/: Capturas fotograficas sin procesar (ignoradas por git).
  - processed/: Datasets clasificados y procesados (PlantVillage, PlantDoc).
  - synthetic/: Datasets generados mediante modelos biofisicos para simulaciones termicas y agroclimaticas.
  - models/: Checkpoints y pesos entrenados (.pt, .onnx) con sus metadatos JSON adyacentes.
  - invernadero_relacional.db: Base de datos SQLite para registros transaccionales, auditoria PID, eventos de alarma y detecciones de vision.
* docs/: Documentacion tecnica, cientifica y metodologica formal.
  - especificacion_iot_protocolos.md: Contratos de mensajeria MQTT, esquemas JSON y topicos.
  - algoritmos_prototipo_iot_pid_ia_papa.md: Fundamentos matematicos de PID, FOPDT, psicrometria y fusion de riesgo.
  - hardware_prototipo_iot_pid_ia_papa.md: Especificacion electronica de sensores (SHT31, DS18B20, BH1750, VWC) y actuadores.
  - protocolo_captura_y_etiquetado.md: Criterios fitopatologicos para fotografia de hojas y trampas adhesivas amarillas.
  - orden_cuadernos_colab.md: Bitacora de evolucion y ejecucion de cuadernos de computacion en la nube.
  - yolo26.md: Especificacion del flujo de vision con YOLO26n, clasificacion PlantVillage y deteccion PlantDoc.
* experiments/: Protocolos y registros experimentales cientificos E1 a E8.
* firmware/: Codigo fuente de hardware embebido.
  - esp32_control/: Proyecto C++ bajo PlatformIO para ESP32 DevKit V1 (FreeRTOS, PID, filtros EMA/Hampel, cliente MQTT, fail-safe).
  - esphome_invernadero.yaml: Implementacion declarativa alternativa bajo ecosistema ESPHome.
  - wokwi/: Archivos de simulacion virtual de hardware en Wokwi.
* notebooks/: Cuadernos interactivos Jupyter para Google Colab y entrenamiento.
  - 00_inicio_y_datasets.ipynb a 04_evaluacion_y_exportacion.ipynb: Pipeline modular de vision.
  - control/: Cuaderno de identificacion FOPDT y optimizacion Optuna de ganancias PID.
  - riesgo/: Cuaderno de demostracion de modelo de riesgo bioclimatico y fusion.
  - archivo/: Cuadernos de versiones previas preservados para trazabilidad.
* scripts/: Scripts de automatizacion, generacion sintetica, preparacion de datasets, entrenamiento y despliegue.
* server/: Backend FastAPI, orquestador de microservicios, inferencia de vision y bot de Telegram.
* web/: Aplicacion web operativa desarrollada en Django 5.x.
  - dashboard/: Modelos ORM, vistas, servicios de telemetria, gemelo digital y plantillas HTML.
  - invernadero_web/: Configuracion global de Django, middleware de seguridad y enrutamiento principal.
* tests/: Suite de pruebas automatizadas con pytest (54 pruebas unitarias y de integracion).
* thesis/: Documento de tesis, bibliografia en BibTeX y figuras vectoriales generadas.

---

## 3. Parametros Biofisicos y Algoritmicos Validados

### 3.1. Modelo FOPDT de Dinamica Termica (Fase 2)
La funcion de transferencia termica ajustada para el invernadero en La Paz mediante curva de reaccion al escalon corresponde a un modelo de Primer Orden con Tiempo Muerto (FOPDT):
G(s) = (K * exp(-theta * s)) / (tau * s + 1)

Parametros numericos identificados:
* Ganancia estatica (K): 0.1639 grados Celsius por porcentaje de potencia de actuador (% u).
* Constante de tiempo (tau): 242.96 segundos (aproximadamente 4.05 minutos).
* Tiempo muerto / retardo (theta): 33.33 segundos.
* Razon de controlabilidad (theta / tau): 0.137 (sistema con retardo moderado, altamente controlable por PID).
* Bondad de ajuste (R2): 0.9990; RMSE: 0.1178 grados Celsius.

### 3.2. Sintonias PID Validadas
* Ziegler-Nichols Clasico: Kp = 53.37, Ki = 0.8006, Kd = 889.53.
* Cohen-Coon (Rechazo rapido de perturbaciones): Kp = 60.83, Ki = 0.7838, Kd = 719.36.
* Control por Modelo Interno (IMC, conservador): Kp = 29.83, Ki = 0.1149, Kd = 465.23.
* Optuna Bayesiano (TPE, seleccionado para operacion): Kp = 15.934, Ki = 0.1359, Kd = 1.571.
  Métricas en simulacion: Tiempo de asentamiento = 346 s, sobreimpulso Mp = 1.6% (cumple la restriccion agronomica de Mp menor a 5.0%), IAE = 1800.4.

### 3.3. Ecuaciones Psicrometricas a 3600 msnm
* Presion de vapor de saturacion (Tetens):
  es(T) = 0.61078 * exp((17.27 * T) / (T + 237.3))  [en kPa]
* Presion de vapor actual:
  ea = es(T) * (HR / 100.0)  [en kPa]
* Deficit de Presion de Vapor (VPD):
  VPD = max(0.0, es(T) - ea)  [en kPa]
  Banda agronomica optima para papa: 0.5 a 1.2 kPa.
  Condicion critica de condensacion y esporulacion de Tizon: VPD menor a 0.35 kPa.
  Condicion de estres hidrico y proliferacion de pulgones: VPD mayor a 1.4 kPa.
* Punto de Rocio (Tdew):
  alpha = ((17.27 * T) / (237.3 + T)) + ln(HR / 100.0)
  Tdew = (237.3 * alpha) / (17.27 - alpha)  [en grados Celsius]

### 3.4. Modelo de Fusion Multimodal de Riesgo
Indice global de riesgo fitosanitario (Score normalizado entre 0.0 y 1.0):
Score = 0.45 * Score_Clima + 0.35 * Score_Vision + 0.20 * Score_InerciaTemporal

Categorizacion del semaforo:
* BAJO (Score < 0.30): Microclima equilibrado, sin intervencion requerida. Setpoints estandar (18.0 C / 75% HR).
* MEDIO (0.30 <= Score < 0.55): Condicion subcritica. Se recomienda ventilacion preventiva programada de 15 minutos.
* ALTO (0.55 <= Score < 0.75): Alerta fitosanitaria. Ajuste automatico de setpoint a 19.5 C y reduccion de humedad a 65%.
* CRITICO (Score >= 0.75): Peligro inminente de brote. Activacion forzada de extractores, alerta prioritaria por Telegram al operador y recomendacion de aplicacion de biofungicida.

---

## 4. Pipeline de Vision Artificial y Deteccion de Plagas

El modulo de vision admite las arquitecturas YOLO26n (por defecto), YOLO11n y YOLOv8n bajo las siguientes pautas metodologicas:
1. Tarea de Clasificacion Foliar:
   Entrenada con PlantVillage (2,152 imagenes de papa distribuidas en 3 clases: sana, tizon temprano y tizon tardio). Emplea `yolo26n-cls.pt`.
2. Tarea de Deteccion en Campo:
   Entrenada con PlantDoc (219 imagenes, 2 clases de enfermedad). Emplea `yolo26n.pt`. Las cajas delimitadoras corresponden a hojas completas con sintomas, no a micro-lesiones segmentadas.
3. SAHI (Slicing Aided Hyper Inference):
   Aplicado sobre trampas adhesivas amarillas (imagenes generales de 1080p). Divide la toma en mosaicos de 320x320 pixeles con solapamiento del 20% y fusion NMS, incrementando la sensibilidad en pulgones alados y moscas minadoras sin perdida de contexto.
4. Integridad del Checkpoint en Backend:
   El servidor FastAPI (`server/app/services/vision_service.py`) valida la existencia de `best.metadata.json` junto al archivo `.pt` verificado por hash criptografico SHA-256. Rechaza explicitamente pesos preentrenados genericos (COCO de 80 clases) devolviendo HTTP 503 si no hay un modelo propio cargado.

---

## 5. Dashboard Django y Contrato de Interfaces Frontend

El proyecto incluye una aplicacion web interactiva completa en `web/dashboard/`.

### 5.1. Vistas y Rutas
* `/`: Vista principal (`index.html`). KPIs en tiempo real, graficos dinamicos con Chart.js, estado de actuadores split-range y explicabilidad SHAP.
* `/control-pid/`: Vista de control y sintonia (`control_pid.html`). Sliders de consignas con limites de seguridad para papa (8 a 28 C, 40 a 95% HR), entradas manuales de Kp, Ki, Kd, botones de autotuning y tabla de auditoria en SQLite.
* `/vision/`: Visor de detecciones (`vision.html`). Formulario interactivo de inferencia con carga de archivos, alternancia de SAHI y galeria historica.
* `/gemelo-digital/`: Simulador interactivo (`gemelo_digital.html`). Inyeccion de perturbaciones climaticas (Normal, Helada, Temporal de Niebla, Ola de Calor, Brote de Pulgon), esquema transversal 2D y ecuaciones de transferencia.
* `/experimentos/`: Tablero cientifico (`experimentos.html`). Registro de ensayos E1 a E8 y boton de exportacion a CSV.

### 5.2. Endpoints de API Asincronos (Fetch / JSON)
* `GET /api/telemetria/`: Retorna el estado dinamico del microclima y explicabilidad SHAP. Empleado en sondeo de 2 a 3 segundos.
* `POST /api/setpoints/`: Actualiza setpoint_temp y setpoint_hum. Audita en base de datos y publica en MQTT con QoS 1.
* `POST /api/pid/`: Actualiza ganancias Kp, Ki, Kd, audita en base de datos y publica en MQTT.
* `GET /api/autotune/?metodo=OPTUNA`: Calcula parametros recomendados segun FOPDT.
* `POST /api/modo-gemelo/`: Alterna el escenario de perturbacion climatica en memoria.
* `POST /api/subir-imagen/`: Recibe archivo fotografico multipart y devuelve diagnostico, confianza, metricas y ruta anotada.
* `GET /experimentos/exportar-csv/`: Descarga directa del archivo CSV con el historial de ensayos formales.

---

## 6. Estado de Verificacion del Software

Toda la base de codigo se encuentra auditada y verificada:
* Pruebas Automatizadas: 54 pruebas ejecutadas con pytest en entorno Python 3.14 (`tests/test_api_endpoints.py`, `tests/test_datasets_reales.py`, `tests/test_django_web.py`, `tests/test_flujo_colab.py`, `tests/test_mqtt_and_fusion.py`, `tests/test_telegram_bot.py`, `tests/test_yolo26.py`).
* Resultado: 54 pruebas aprobadas (100% de exito).
* Formato de Codigo: Sintaxis limpia sin advertencias de secuencias de escape (raw strings aplicados en f-strings de LaTeX) y con bloques defensivos para ejecucion desacoplada.

---

## 7. Instrucciones Operativas para Agentes de Inteligencia Artificial

Al interactuar o modificar este repositorio, los agentes deben seguir estrictamente estas reglas:

1. Preservacion de Integridad Cientifica:
   Nunca fabricar o inventar metricas de desempeno (mAP, F1-score, precision, recall, IAE). Toda metrica reportada en tablas de experimentos o cuadernos debe provenir de evaluaciones computadas y medidas sobre datasets reales o simulaciones reproducibles.
2. Contratos de Datos y Metadatos:
   Al exportar o entrenar modelos de vision, generar siempre el archivo `<nombre>.metadata.json` con el digest SHA-256 de los pesos, la arquitectura, la tarea (`detect` o `classify`) y la lista ordenada de clases.
3. Seguridad Agronomica en Lazo de Control:
   No permitir que peticiones de API o modificaciones de firmware establezcan consignas fuera del rango seguro para la papa (temperatura minima 5 C, maxima 35 C; humedad minima 30%, maxima 95%).
4. Tolerancia a Fallos y Modo Offline:
   Cualquier cambio en el firmware del ESP32 debe preservar la rutina local de lectura de sensores y calculo PID independiente de la disponibilidad de la red Wi-Fi o del broker MQTT.
5. Compatibilidad Python 3.12 y 3.14:
   Utilizar raw f-strings (`fr'...'` o `rf'...'`) en cadenas que contengan barras invertidas de formato matematico de LaTeX (como `\%` o `\circ`) para evitar advertencias de sintaxis y fallos de ejecucion.
6. Ausencia de Emojis:
   Mantener la documentacion tecnica, logs de consola y archivos Markdown libres de emojis, utilizando en su lugar identificadores textuales legibles entre corchetes como `[OK]`, `[INFO]`, `[NOTA]`, `[ADVERTENCIA]` o `[ERROR]`.
