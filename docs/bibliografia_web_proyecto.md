# Bibliografía web y herramientas del proyecto IoT–PID–IA para papa

Fecha de revisión y consulta web: 28 de octubre de 2026.

Se interpretó «biografías» como bibliografía. Este documento relaciona fuentes académicas y documentación oficial con la implementación encontrada en el repositorio. Las referencias de artículos incluyen autores y año; las páginas de documentación sin fecha editorial identificable se registran como «s. f.». La numeración sirve para relacionar las fuentes con las herramientas, no constituye un orden de citación IEEE definitivo.

## 1. Alcance de la revisión

Se revisaron la estructura del repositorio, README, documentación técnica, manifiestos de dependencias, Docker Compose, firmware y configuración PlatformIO, servicios principales del backend, supervisor, panel Django, scripts de simulación e investigación, cuadernos, protocolos experimentales y flujos de integración continua. Es una revisión documental y de código para seleccionar bibliografía: no demuestra que el hardware esté instalado ni que todos los servicios estén ejecutándose. No se ejecutaron entrenamientos, ensayos físicos ni pruebas de funcionamiento para este informe.

El proyecto propone regular el microclima de un invernadero de papa en La Paz y detectar indicios visuales de enfermedades e insectos. El firmware implementa control local y el servidor publica consignas mediante MQTT. La infraestructura declarada conecta Mosquitto, Telegraf, InfluxDB y Grafana; FastAPI, SQLite y Django cubren operaciones, almacenamiento de eventos y panel web.

## 2. Herramientas y evidencia local

| Área | Herramientas y versiones declaradas | Evidencia | Estado observado |
|---|---|---|---|
| Nodo embebido | ESP32, C++, Arduino, PlatformIO; plataforma espressif32 6.6.0 | `firmware/esp32_control/platformio.ini`, `src/main.cpp` | Firmware implementado; despliegue físico no verificado. |
| Sensores | SHT31, DS18B20, BH1750, sensor capacitivo y flotador | `firmware/esp32_control/src/main.cpp`, `include/config_invernadero.h` | Interfaces y pines implementados. |
| Bibliotecas del nodo | ArduinoJson 7.0.4, PubSubClient 2.8, OneWire 2.3.8, DallasTemperature 3.11.0, BH1750 1.3.0; SHT31 fijada a un commit | `firmware/esp32_control/platformio.ini` | Dependencias declaradas. |
| Control | PID discreto, anti-windup, split-range, ventana SSR y PWM | `firmware/esp32_control/src/main.cpp` | Algoritmo propio; no depende de una biblioteca PID externa. |
| Mensajería | MQTT, Mosquitto 2.0.18, Paho MQTT 2.1.0 | `docker-compose.yml`, `server/requirements.txt`, `server/app/services/mqtt_client.py` | Configuración y cliente implementados. |
| Telemetría | Telegraf 1.30.0, InfluxDB 2.7.5, Grafana 10.4.1 | `docker-compose.yml`, `config/` | Servicios declarados y aprovisionamiento incluido. |
| API | FastAPI 0.110.0, Uvicorn 0.28.0, Pydantic 2.6.4 | `server/requirements.txt`, `server/app/` | Backend implementado. |
| Datos relacionales | SQLite, aiosqlite 0.20.0 | `server/app/services/database.py`, `server/app/models/schemas.sql` | Persistencia implementada. |
| Panel | Django >=5.2,<5.3, Tailwind CSS, Chart.js y Lucide | `requirements.txt`, `web/dashboard/` | Interfaz implementada; las gráficas de simulación deben distinguirse de telemetría real. |
| Visión | OpenCV 4.10.0.84, Pillow; Ultralytics >=8.3,<9 y SAHI >=0.11,<0.12 opcionales | `server/requirements*.txt`, `server/app/services/vision_service.py` | Integración disponible; inferencia real requiere pesos compatibles entrenados. |
| Identificación y sintonía | NumPy 1.26.4, SciPy 1.12.0, Optuna; python-control 0.10.1 declarado | `server/requirements.txt`, `scripts/ejecutar_fase2_identificacion_pid.py`, cuaderno 01 | Investigación y simulación; declarar una dependencia no prueba su uso en cada cálculo. |
| Curaduría | Albumentations, PyYAML, PlantVillage; PlantDoc e IP102 mencionados en protocolos | `scripts/preparar_dataset_vision.py`, `scripts/descargar_filtrar_datasets_abiertos.py`, cuaderno 02 | Preparación de datos; no se verificó la composición final del conjunto de entrenamiento. |
| Entrenamiento y exportación | Jupyter/Colab, TensorBoard, ONNX y ONNX Runtime | `notebooks/03_entrenamiento_comparativa_yolo.ipynb` | Código experimental; no implica que ONNX Runtime sea el motor activo del backend. |
| Riesgo experimental | scikit-learn, Random Forest, SVM, XGBoost, SHAP y PyTorch LSTM | `scripts/ejecutar_fase5_riesgo_fusion.py`, cuaderno 04 | Modelos presentes en investigación; no se encontró su carga en el supervisor operativo revisado. |
| Supervisor | Reglas de clima, visión y tendencia con ponderaciones | `server/app/worker.py` | La decisión actual es heurística; su puntuación no equivale automáticamente a una probabilidad calibrada. |
| Alertas | Telegram Bot API mediante HTTPX | `server/app/services/telegram_bot.py` | Integración implementada, condicionada a configuración. |
| Despliegue y calidad | Docker Compose, Make, systemd, GitHub Actions, pytest, pytest-asyncio y Flake8 | `Makefile`, `config/systemd/`, `.github/workflows/`, `tests/` | Automatización declarada; no ejecutada en esta revisión. |
| Simulación y demostración | Wokwi, modelo FOPDT y cloudflared | `firmware/wokwi/`, `scripts/simulador_esp32_mqtt.py`, `Makefile` | Archivos y tareas disponibles; no se verificó una sesión activa. |

## 3. Bibliografía académica y agronómica

**[1] Agricultura e IoT.** Ayaz, M., Ammad-Uddin, M., Sharif, Z., Mansour, A., y Aggoune, E. H. M. (2019). *Internet-of-Things (IoT)-based smart agriculture: Toward making the fields talk*. IEEE Access, 7, 129551–129583. https://doi.org/10.1109/ACCESS.2019.2932609. [Registro institucional consultado](https://researchportal.ip-paris.fr/fr/publications/internet-of-things-iot-based-smart-agriculture-toward-making-the-/).

Aplicación: antecedentes de sensores, conectividad y arquitectura IoT agrícola. No valida por sí mismo el prototipo local.

**[2] Control PID y FOPDT.** Skogestad, S. (2003). *Simple analytic rules for model reduction and PID controller tuning*. Journal of Process Control, 13, 291–309. https://doi.org/10.1016/S0959-1524(02)00062-8. [Artículo del editor](https://www.sciencedirect.com/science/article/pii/S0959152402000628).

Aplicación: reducción de modelos, retardo y sintonización SIMC/IMC; pertinente para el ajuste FOPDT y las comparativas de control.

**[3] Optimización de hiperparámetros.** Akiba, T., Sano, S., Yanase, T., Ohta, T., y Koyama, M. (2019). *Optuna: A next-generation hyperparameter optimization framework*. [Prepublicación de los autores](https://arxiv.org/abs/1907.10902).

Aplicación: justificar la búsqueda de ganancias PID mediante Optuna. La función objetivo y sus límites deben describirse a partir del experimento propio.

**[4] Diagnóstico visual de enfermedades.** Mohanty, S. P., Hughes, D. P., y Salathé, M. (2016). *Using deep learning for image-based plant disease detection*. Frontiers in Plant Science, 7, 1419. [Artículo abierto](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2016.01419/full). DOI: 10.3389/fpls.2016.01419.

Aplicación: antecedentes de clasificación de hojas y transferencia de aprendizaje. Los resultados publicados no son métricas del modelo de esta tesis.

**[5] Detección de objetos pequeños.** Akyon, F. C., Altinuc, S. O., y Temizel, A. (2022). *Slicing aided hyper inference and fine-tuning for small object detection*. IEEE International Conference on Image Processing. DOI: 10.1109/ICIP46576.2022.9897990. [Texto de los autores](https://arxiv.org/abs/2202.06934).

Aplicación: fundamento de SAHI para dividir imágenes en ventanas y detectar insectos pequeños. El artículo evalúa otros conjuntos; su mejora no se puede trasladar como resultado demostrado sobre trampas de papa.

**[6] Datos de enfermedades en condiciones variables.** Singh, D., Jain, N., Jain, P., Kayal, P., Kumawat, S., y Batra, N. (2019). *PlantDoc: A dataset for visual plant disease detection*. [Prepublicación consultada](https://arxiv.org/abs/1911.10317).

Aplicación: motivar imágenes de campo y variación de fondos. Se cita aquí la versión arXiv de 2019; si se usa la publicación en congreso, debe ajustarse su año y ficha editorial.

**[7] Reconocimiento de insectos.** Wu, X., Zhan, C., Lai, Y.-K., Cheng, M.-M., y Yang, J. (2019). *IP102: A large-scale benchmark dataset for insect pest recognition*. Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. [Publicación oficial CVF](https://openaccess.thecvf.com/content_CVPR_2019/html/Wu_IP102_A_Large-Scale_Benchmark_Dataset_for_Insect_Pest_Recognition_CVPR_2019_paper.html).

Aplicación: antecedentes de datasets de insectos y clases desbalanceadas. Mencionarlo en el protocolo no acredita haberlo descargado o usado; comprobar especies y anotaciones antes de integrarlo.

**[8] Modelo XGBoost.** Chen, T., y Guestrin, C. (2016). *XGBoost: A scalable tree boosting system*. DOI: 10.1145/2939672.2939785. [Texto de los autores](https://arxiv.org/abs/1603.02754).

Aplicación: modelo tabular de riesgo del script experimental de fase 5.

**[9] Explicabilidad SHAP.** Lundberg, S. M., y Lee, S.-I. (2017). *A unified approach to interpreting model predictions*. [Texto de los autores](https://arxiv.org/abs/1705.07874).

Aplicación: explicación de contribuciones de variables en los modelos experimentales; no demuestra causalidad agronómica.

**[10] Riesgo de tizón tardío.** Agriculture and Horticulture Development Board. (s. f.). *Development and implementation of a new national warning system for potato late blight in Great Britain (Hutton Criteria).* [Informe institucional](https://horticulture.ahdb.org.uk/development-and-implementation-of-a-new-national-warning-system-for-potato-late-blight-in-great-britain-hutton-criteria).

Aplicación: antecedente de alerta basada en condiciones ambientales de infección. Hutton, Wallin y el código denominado BlightManager no son nombres intercambiables. Esta fuente no acredita la sigmoide ni los umbrales específicos programados en fase 5; se requiere una fuente primaria y una comparación formal para atribuirlos a Wallin.

## 4. Documentación oficial de las herramientas

Las entradas de documentación siguientes tienen fecha «s. f.» y fueron consultadas el 28 de octubre de 2026. Algunas páginas siguen la versión más reciente del producto; para reproducibilidad se deben conservar las versiones del repositorio indicadas en la tabla anterior.

| Ref. | Autor o entidad y título | Enlace oficial | Utilidad en este proyecto |
|---|---|---|---|
| [11] | OASIS. (2014). *MQTT Version 3.1.1* | [Especificación](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html) | Publicación/suscripción, QoS y mensajes retenidos. |
| [12] | Eclipse Foundation. *Eclipse Mosquitto documentation* | [Documentación](https://mosquitto.org/documentation/) | Broker y autenticación. |
| [13] | Eclipse Foundation. *Paho MQTT Python client* | [Documentación](https://eclipse.dev/paho/files/paho.mqtt.python/html/) | Cliente MQTT del servidor. |
| [14] | InfluxData. *Telegraf MQTT Consumer input plugin* | [Documentación](https://docs.influxdata.com/telegraf/v1/input-plugins/mqtt_consumer/) | Consumo de telemetría MQTT. |
| [15] | InfluxData. *InfluxDB OSS v2 documentation* | [Documentación](https://docs.influxdata.com/influxdb/v2/) | Series temporales, buckets y consultas. |
| [16] | Grafana Labs. *Grafana documentation* | [Documentación](https://grafana.com/docs/grafana/latest/) | Tableros y fuentes de datos; contrastar con Grafana 10.4.1. |
| [17] | Docker. *Docker Compose* | [Documentación](https://docs.docker.com/compose/) | Servicios, redes y volúmenes. |
| [18] | Proyecto FastAPI. *FastAPI* | [Documentación](https://fastapi.tiangolo.com/) | API, validación e integración de servicios. |
| [19] | Django Software Foundation. *Django 5.2 documentation* | [Documentación 5.2](https://docs.djangoproject.com/en/5.2/) | Panel, autenticación, vistas y protección CSRF. |
| [20] | Proyecto SQLite. *SQLite documentation* | [Documentación](https://www.sqlite.org/docs.html) | Eventos, auditoría y almacenamiento relacional. |
| [21] | Espressif Systems. *Arduino ESP32 documentation* | [Documentación](https://docs.espressif.com/projects/arduino-esp32/en/latest/) | Wi-Fi, GPIO y periféricos; la página actual corresponde a un core más reciente que el entorno fijado. |
| [22] | PlatformIO. *Espressif 32* | [Documentación](https://docs.platformio.org/en/latest/platforms/espressif32.html) | Compilación y gestión del entorno ESP32. |
| [23] | Ultralytics. *Ultralytics YOLO11* | [Documentación del modelo](https://docs.ultralytics.com/models/yolo11/) | Arquitectura, entrenamiento y exportación de la familia utilizada. |
| [24] | Proyecto SAHI. *SAHI* | [Repositorio oficial](https://github.com/obss/sahi) | Integración de inferencia por ventanas. |
| [25] | Proyecto OpenCV. *OpenCV documentation* | [Documentación](https://docs.opencv.org/4.x/) | Lectura, transformación y anotación de imágenes; la página actual redirige a una versión posterior a 4.10. |
| [26] | Proyecto SciPy. *scipy.optimize.curve_fit* | [Referencia](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html) | Ajuste por mínimos cuadrados del FOPDT. |
| [27] | Proyecto python-control. *Python Control Systems Library 0.10.1* | [Documentación 0.10.1](https://python-control.readthedocs.io/en/0.10.1/) | Análisis de sistemas de control; dependencia declarada. |
| [28] | Proyecto scikit-learn. *Probability calibration* | [Guía](https://scikit-learn.org/stable/modules/calibration.html) | Calibración y evaluación de probabilidades en investigación. |
| [29] | Proyecto ONNX Runtime. *ONNX Runtime documentation* | [Documentación](https://onnxruntime.ai/docs/) | Exportación y comparación de inferencia del cuaderno 03. |
| [30] | Telegram. *Telegram Bot API* | [API oficial](https://core.telegram.org/bots/api) | Alertas y fotografías. |
| [31] | Tailwind Labs. *Try Tailwind CSS using the Play CDN* | [Documentación v3](https://v3.tailwindcss.com/docs/installation/play-cdn) | Estilos de las plantillas; el código usa Play CDN. |
| [32] | Proyecto Chart.js. *Chart.js documentation* | [Documentación](https://www.chartjs.org/docs/latest/) | Gráficos del panel. |
| [33] | Proyecto Lucide. *What is Lucide?* | [Guía](https://lucide.dev/guide/) | Iconografía de la interfaz. |
| [34] | Proyecto pytest. *pytest documentation* | [Documentación](https://docs.pytest.org/en/stable/) | Pruebas del backend y panel. |
| [35] | GitHub. *GitHub Actions documentation* | [Documentación](https://docs.github.com/en/actions) | Validación y compilación automatizadas. |
| [36] | Wokwi. *Wokwi documentation* | [Documentación](https://docs.wokwi.com/) | Simulación de componentes y diagramas. |
| [37] | Sensirion. *SHT31-DIS-B* | [Ficha y documentación](https://sensirion.com/products/catalog/SHT31-DIS-B) | Sensor de temperatura y humedad del aire. |
| [38] | Analog Devices/Maxim. (2019). *DS18B20: Programmable Resolution 1-Wire Digital Thermometer* | [Hoja de datos](https://www.analog.com/media/en/technical-documentation/data-sheets/ds18b20.pdf) | Sensor de temperatura del suelo y comunicación 1-Wire. |
| [39] | Mohanty, S. P., y colaboradores. *PlantVillage-Dataset* | [Repositorio de datos](https://github.com/spMohanty/PlantVillage-Dataset) | Procedencia de imágenes públicas referenciadas por el descargador. |
| [40] | Proyecto Albumentations. *Albumentations documentation* | [Documentación](https://albumentations.ai/docs/) | Aumentos de datos en curaduría; la documentación actual también presenta AlbumentationsX y no identifica la versión usada localmente. |

## 5. Observaciones para redactar la tesis con estas fuentes

1. **Versión de Django:** citar Django 5.2 para la implementación actual. `sugerenciasHerramintas.md` menciona Django 6, pero contradice `requirements.txt`.
2. **Resultados de visión:** `scripts/ejecutar_fase4_evaluacion_vision.py` construye tablas con métricas literales, y el cuaderno 03 también contiene valores y extrapolaciones de comparación. Esos archivos no bastan para demostrar un benchmark medido. Conservar salidas reales de validación, pesos, particiones, hardware y tiempos antes de presentarlos como resultados experimentales.
3. **IA del supervisor:** `server/app/worker.py` combina reglas y ponderaciones; no carga XGBoost ni LSTM. Presentar esos modelos como investigación disponible hasta acreditar su integración operativa.
4. **Riesgo epidemiológico:** `BlightManagerBaseline` convierte unidades acumuladas mediante una sigmoide. No se verificó una fuente primaria que respalde su equivalencia con un modelo Wallin completo. Documentar la adaptación y validarla; no atribuirla al artículo de Hutton.
5. **Humedad foliar:** el supervisor acumula tiempo con humedad relativa alta; ese indicador es una aproximación y no una medición directa de mojado de hoja.
6. **Dependencias experimentales:** Optuna, pandas, Matplotlib, scikit-learn, XGBoost, SHAP y PyTorch aparecen en scripts/cuadernos, pero no todas están incluidas en los manifiestos base revisados. El cuaderno 01 conserva errores por falta de Optuna. La presencia de código no demuestra ejecución completa.
7. **Herramientas propuestas:** Roboflow, AutoDistill/Grounding DINO y Ngrok aparecen en sugerencias, pero no se identificó una integración ejecutable en los archivos revisados. ONNX Runtime, Albumentations y cloudflared sí tienen evidencia en cuadernos, scripts o Makefile, con alcance distinto del backend operativo.
8. **Control jerárquico:** describir la relación entre supervisor y PID local con precisión. Ajustar consignas según riesgo no acredita por sí solo una cascada clásica de dos controladores PID.
9. **Agronomía local:** las fuentes generales y los criterios británicos de tizón no validan automáticamente consignas, variedades ni desempeño a la altitud de La Paz. La memoria necesita además registros y validación agronómica local; no se inventaron referencias de INIAF, PROINPA o CIP.

## 6. Selección para la memoria

Para antecedentes y marco teórico: [1], [2], [4], [5] y [10]. Para metodología de optimización y riesgo: [3], [8], [9] y [28]. Para datasets: [6], [7] y [39], únicamente cuando se confirme su uso. Para implementación: [11]–[27] y [29]–[38], seleccionando las herramientas efectivamente empleadas.

Ejemplo de redacción: «La comunicación entre el nodo de control y los servicios del servidor utiliza el patrón publicación/suscripción de MQTT (OASIS, 2014). Para abordar objetos pequeños, el módulo de visión integra inferencia por ventanas basada en SAHI (Akyon et al., 2022)». Las mejoras de precisión y control deben respaldarse con los ensayos propios, además de la bibliografía.
