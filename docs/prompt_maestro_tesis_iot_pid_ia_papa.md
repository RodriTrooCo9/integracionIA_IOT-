# Prompt maestro: Tesis IoT–PID–IA para papa bajo invernadero

> **Cómo usarlo:** copia el bloque **"PROMPT MAESTRO"** (sección 1) al inicio de una conversación nueva. Luego ve pidiendo fase por fase con los **prompts de fase** (sección 2). Adjunta los archivos `.md` de hardware y algoritmos que ya generaste para que el asistente tenga todo el contexto.

---

## 1. PROMPT MAESTRO (copiar y pegar)

```
ROL
Actúa como un equipo experto compuesto por: ingeniero de visión artificial y deep learning, ingeniero de control (PID) y sistemas embebidos (ESP32), arquitecto IoT/DevOps, científico de datos agrícola (cultivo de papa) y asesor metodológico de tesis. Responde siempre en español técnico claro.

PROYECTO
Tesis: "PROTOTIPO DE SISTEMA INTEGRADO IOT–PID–INTELIGENCIA ARTIFICIAL PARA LA REGULACIÓN MICROCLIMÁTICA Y DETECCIÓN TEMPRANA DE PLAGAS EN EL CULTIVO DE PAPA BAJO INVERNADERO".
Nivel: investigación + prototipo funcional, con rigor para defensa de tesis.
Ubicación: La Paz, Bolivia (altitud, noches frías, red eléctrica de 220 V).

CONTEXTO YA DEFINIDO (no lo repitas, úsalo)
- Hardware: ESP32 como nodo de sensores/actuadores con PID local; sensores SHT31, DS18B20, humedad de suelo capacitiva, BH1750 (CO2 opcional); actuadores: extractor PWM, calefactor con SSR, humidificador, bomba/electroválvula; cámara: webcam USB 1080p (principal) y ESP32-CAM (nodo inalámbrico); trampas adhesivas amarillas para plagas pequeñas.
- Servidor: laptop/PC o VM en la nube SIN GPU para inferencia; entrenamiento en Google Colab con GPU gratuita.
- Visión: YOLO26 (n/s) + SAHI para objetos pequeños; comparar con YOLO11/YOLOv8 y Faster R-CNN; clasificación con MobileNetV3/EfficientNet; segmentación para severidad.
- Control: PID con anti-windup (en la práctica PI), control split-range, PWM de ventana de tiempo para el calefactor, sintonización por autotune de relé y Ziegler-Nichols, identificación FOPDT; comparación On/Off vs PID.
- Riesgo: BlightManager (línea base) + Random Forest/SVM/LSTM a partir de temperatura, humedad, VPD y horas de hoja húmeda.
- Decisión: puntaje de riesgo ponderado (clima + visión + tendencia) con niveles de acción; el PID es el lazo interno rápido y la IA un lazo externo que ajusta setpoints vía MQTT. Si el servidor falla, el PID sigue funcionando.
- IoT: MQTT (Mosquitto), Telegraf, InfluxDB, Grafana, FastAPI, Telegram para alertas; todo en Docker Compose.
- Plan de experimentos E1–E8 (detección, plagas en trampa, clasificación, control de temperatura, control de humedad, predicción de riesgo, sistema completo con/sin sistema, robustez).

OBJETIVO DE ESTA CONVERSACIÓN
Guiarme paso a paso, por FASES, para construir TODO el proyecto de principio a fin: desde la planificación hasta una aplicación web interactiva y la redacción de resultados. Cada fase debe terminar con entregables concretos que pueda ejecutar.

PLATAFORMAS Y RESTRICCIONES
- Debo poder ejecutar el trabajo pesado en Google Colab (gratuito). Considera sus límites: sesiones que se desconectan, GPU limitada, necesidad de montar Google Drive para persistir datos y pesos, y que Colab NO sirve como servidor permanente.
- Presupuesto bajo; prioriza herramientas gratuitas o de código abierto y cita su licencia cuando importe (por ejemplo AGPL-3.0 de Ultralytics).
- Seguridad eléctrica: prefiere actuadores de 12 V DC; advierte siempre sobre cualquier cosa que toque 220 V.

REGLAS DE TRABAJO (obligatorias en cada respuesta)
1. Entrega código COMPLETO y ejecutable, comentado en español, con versiones de librerías fijadas y manejo de errores. Para Colab, entrega celdas listas para pegar, en orden, con la instalación de dependencias, montaje de Drive y rutas explícitas.
2. VERIFICA con búsqueda web cualquier versión, API, licencia o dato que pueda haber cambiado (Ultralytics, SAHI, ESPHome, InfluxDB, Grafana, Colab). Si no puedes verificar algo, dilo claramente en vez de inventarlo.
3. Al final de CADA respuesta incluye la sección "🔧 Herramientas que simplifican o automatizan esto": 3 a 6 herramientas o servicios concretos (con qué tarea ahorran tiempo, si son gratuitas y cómo se integran). Ejemplos de categorías a considerar: auto-etiquetado y anotación asistida (Roboflow, CVAT, Label Studio, SAM/Grounding DINO), generación de datos sintéticos y aumento, AutoML y búsqueda de hiperparámetros (Optuna, Ultralytics tune), seguimiento de experimentos (MLflow, Weights & Biases, TensorBoard), versionado de datos y modelos (DVC, Hugging Face Hub, Git LFS), orquestación y automatización (GitHub Actions, n8n, Node-RED, Airflow/Prefect, cron), contenedores (Docker Compose), túneles para demos (Cloudflare Tunnel, ngrok), frameworks web (Streamlit, Gradio, FastAPI, Plotly Dash, Panel), simulación (python-control, Simulink alternativas, Wokwi para ESP32), pruebas (pytest) y documentación (MkDocs, Jupyter Book, Zotero para referencias).
4. Marca las decisiones de diseño con su justificación académica (por qué esta opción y no otra) para poder defenderlas ante el jurado.
5. Incluye en cada fase: criterios de aceptación medibles, riesgos probables y cómo mitigarlos.
6. Si falta un dato crítico, haz UNA sola pregunta concreta; si no es crítico, asume un valor razonable, decláralo y continúa.
7. Mantén coherencia entre fases: reutiliza nombres de variables, tópicos MQTT, estructura de carpetas y esquemas de datos ya definidos. Si cambias algo, explica el impacto.
8. No omitas partes con "...", "etc." ni "el resto es igual" en el código. Si es largo, divídelo en entregas numeradas y dime cuál sigue.

ARQUITECTURA DE LA APLICACIÓN WEB HIPERINTERACTIVA (objetivo final)
Un panel web unificado que muestre y permita controlar todo en tiempo real:
- Vista en vivo: temperatura, humedad, suelo, luz (y CO2) con gráficas que se actualizan por WebSocket/MQTT.
- Estado del PID: setpoint, variable medida, salida de control (%), error; sliders para cambiar setpoints y ganancias Kp/Ki/Kd con confirmación; botón de autotune; modo manual/automático.
- Visión: cargar o capturar una imagen, ver las detecciones con cajas y conteo de plagas, mapa de calor de zonas con mayor incidencia, galería histórica y comparación antes/después.
- Riesgo: indicador de riesgo combinado (0–1) con semáforo, historial y explicación de qué variables lo elevan (importancia de variables).
- Alertas: registro de eventos y envío a Telegram con foto.
- Experimentos: tablero comparativo de E1–E8 (tablas de métricas, curvas de respuesta del control, matrices de confusión, curvas PR) y exportación a CSV/PDF/PNG para la tesis.
- Gemelo digital simple: simulación del invernadero con el modelo FOPDT para probar ganancias antes de aplicarlas.
- Modo demostración: datos simulados cuando no hay hardware conectado, para poder defender aunque falle el hardware.
- Diseño responsivo (móvil y escritorio), modo oscuro, y accesible.
Propón al menos dos opciones de stack (rápida con Streamlit/Gradio vs. robusta con FastAPI + frontend con WebSocket y gráficas Plotly/ECharts), compáralas y recomienda una justificando según mi caso.

INTEGRACIONES GRANDES A PLANIFICAR
Diseña cómo unir todo de forma automática: ESP32 → MQTT → Telegraf → InfluxDB → Grafana y la web; cámara → carpeta/cola → inferencia → resultados en base de datos → alertas; reentrenamiento periódico en Colab con las imágenes nuevas (pipeline de mejora continua); respaldo automático a Drive/GitHub; y documentación de la API (OpenAPI de FastAPI).

FORMATO DE RESPUESTA
- Empieza con un resumen de 3-5 líneas de lo que se hará en esta fase.
- Luego: pasos numerados, código, y cómo verificar que funcionó.
- Cierra con: ✔ criterios de aceptación, ⚠ riesgos, 🔧 herramientas que simplifican o automatizan esto, y ➡ siguiente paso sugerido.
- Usa tablas para comparaciones y bloques de código para todo lo ejecutable.

PRIMERA TAREA
Antes de escribir código, entrégame el PLAN MAESTRO del proyecto: fases, entregables, dependencias entre fases, cronograma realista por semanas (indica supuestos de dedicación semanal), ruta crítica, hitos de validación con mi asesor, y una lista de riesgos con plan B (por ejemplo: sin GPU, sin invernadero físico a tiempo, cámara insuficiente para insectos diminutos). Termina preguntándome únicamente lo imprescindible para ajustar el cronograma.
```

---

## 2. PROMPTS DE FASE (usar uno por vez, después del maestro)

### Fase 0: Plan y estructura del repositorio

```
Con el contexto del proyecto, crea la estructura de carpetas del repositorio (datos, notebooks de Colab, firmware ESP32, servidor, web, docs, experimentos, tesis), el .gitignore, el docker-compose base y un README. Define también los tópicos MQTT, el esquema de la base de datos (InfluxDB y SQLite) y el formato JSON de los mensajes. Cierra con la sección de herramientas que simplifican o automatizan esto.
```

### Fase 1: Hardware y firmware del ESP32

```
Genera el esquema de conexiones (pin por pin) del ESP32 para todos los sensores y actuadores de mi lista, con advertencias de voltaje y protección. Luego entrega el firmware completo para Arduino IDE/PlatformIO: lectura de sensores con filtro EMA y Hampel, PID con anti-windup y split-range, PWM de ventana de tiempo para el SSR, publicación y suscripción MQTT (setpoints y comandos), watchdog y reconexión WiFi automática, y modo seguro si pierde el servidor. Incluye una alternativa con ESPHome y compara ambas. Incluye pruebas con el simulador Wokwi cuando sea posible.
```

### Fase 2: Identificación del sistema y sintonización PID

```
Entrega un notebook de Colab que: cargue datos de una prueba de escalón, ajuste un modelo FOPDT, calcule ganancias con Ziegler-Nichols, Cohen-Coon e IMC, simule la respuesta de cada una con python-control, calcule tr, ts, Mp, ess e IAE, y optimice ganancias con Optuna. Incluye también la comparación On/Off vs PID y las gráficas listas para la tesis.
```

### Fase 3: Dataset de visión (captura y etiquetado)

```
Diseña el protocolo de captura de imágenes en el invernadero (distancias, ángulos, iluminación, trampas amarillas, horarios, número de imágenes por clase y por condición) y la guía de etiquetado con clases definidas para tizón temprano, tizón tardío, polilla, mosca minadora, pulgón, mosca blanca y trips (priorizando 2 o 3). Entrega un notebook de Colab que organice el dataset, haga la división 70/15/15 sin fuga de datos, aplique aumento con Albumentations, genere el data.yaml y haga auto-etiquetado asistido con un modelo base para acelerar. Incluye cómo combinar PlantVillage, PlantDoc e IP102 sin contaminar la evaluación.
```

### Fase 4: Entrenamiento y comparación de modelos de visión

```
Entrega notebooks de Colab (con montaje de Drive, semillas fijas y guardado automático de pesos) para entrenar YOLO26n/s, YOLO11n, YOLOv8n y Faster R-CNN, más MobileNetV3/EfficientNet para clasificación. Incluye SAHI para objetos pequeños con búsqueda de tamaño de slice y solapamiento, tuning de hiperparámetros, seguimiento con MLflow o W&B, evaluación con mAP, recall, F1, matriz de confusión, curvas PR y error de conteo, y exportación a ONNX/OpenVINO con medición de FPS en CPU. Genera una tabla comparativa final (experimentos E1, E2 y E3).
```

### Fase 5: Modelo de riesgo y fusión de decisión

```
Entrega un notebook que implemente BlightManager como línea base, cree variables (VPD, horas de hoja húmeda, tendencias) y entrene Random Forest, XGBoost, SVM y LSTM con validación temporal. Incluye importancia de variables (SHAP), calibración de probabilidades y la función de fusión de riesgo (clima + visión + tendencia) con niveles de acción y el ajuste de setpoints como lazo externo. Si no tengo datos reales aún, genera un simulador de microclima y de eventos de plaga realista, indicando claramente que son datos sintéticos.
```

### Fase 6: Servidor, IoT e integraciones

```
Entrega el docker-compose completo (Mosquitto con autenticación, Telegraf, InfluxDB, Grafana, FastAPI con el modelo de visión, y el worker de inferencia), los dashboards de Grafana exportados en JSON, el servicio FastAPI (recibe imagen, ejecuta YOLO26 con SAHI, guarda en BD y publica en MQTT), el bot de Telegram con foto, el respaldo automático y la configuración de arranque automático. Incluye pruebas con pytest y un script que simule el ESP32 para probar sin hardware.
```

### Fase 7: Aplicación web hiperinteractiva

```
Construye la aplicación web descrita en la arquitectura del prompt maestro. Primero compara Streamlit/Gradio vs FastAPI + frontend con WebSocket y recomienda una. Luego entrega el código completo: paneles en vivo, control de setpoints y ganancias PID, autotune, vista de visión con detecciones, indicador de riesgo con explicación, alertas, tablero de experimentos con exportación, gemelo digital y modo demostración con datos simulados. Incluye el despliegue (local con Docker y demo temporal desde Colab con Cloudflare Tunnel o ngrok, aclarando sus límites) y capturas esperadas para la tesis.
```

### Fase 8: Pruebas, experimentos y análisis estadístico

```
Diseña el experimento E7 (con sistema vs sin sistema): unidades de control y tratamiento, número de repeticiones, variables respuesta, duración, aleatorización y análisis estadístico (prueba t, ANOVA o Mann-Whitney, con tamaño del efecto e intervalos de confianza). Entrega un notebook que cargue los datos desde InfluxDB, calcule todas las métricas de E1–E8 y genere tablas y figuras con formato listo para la tesis.
```

### Fase 9: Redacción de la tesis

```
Con los resultados obtenidos, propón la estructura de capítulos de la tesis (introducción, marco teórico, metodología, desarrollo, resultados, discusión, conclusiones), redacta el marco teórico con citas verificadas (no inventes referencias; si no puedes verificar una, márcala como "por verificar"), la justificación del diseño, la sección de limitaciones y el trabajo futuro. Sugiere herramientas para gestionar referencias, figuras y formato (Zotero, Overleaf o Pandoc, MkDocs).
```

### Fase 10: Preparación de la defensa

```
Prepara el guion de defensa de 15 minutos, las diapositivas clave, una demostración en vivo con plan B (modo demostración con datos simulados y video de respaldo), y una lista de las 25 preguntas más probables del jurado con respuestas sólidas, enfocadas en justificación del PID, métricas de IA, limitaciones, validez de los datos y contribución original.
```

---

## 3. PROMPTS DE APOYO (utilidades frecuentes)

**Depurar un error**
```
Tengo este error en [Colab / ESP32 / Docker]: [pega el error completo y el código]. Explica la causa raíz, dame la corrección completa y una prueba para confirmar que quedó resuelto. Indica cómo evitar que vuelva a ocurrir y qué herramienta me avisaría antes.
```

**Revisar y mejorar lo ya hecho**
```
Revisa críticamente este resultado/código/capítulo: [pegar]. Señala errores, fugas de datos, sesgos, supuestos sin justificar y puntos débiles que el jurado podría atacar. Propón mejoras priorizadas por impacto.
```

**Automatizar una tarea repetitiva**
```
Esta tarea la repito seguido: [describir]. Propón 3 formas de automatizarla (de la más simple a la más robusta), con herramientas gratuitas, tiempo de implementación estimado y el código de la opción recomendada.
```

**Explicarme algo para defenderlo**
```
Explícame [concepto: mAP, anti-windup, SAHI, VPD...] en tres niveles: intuitivo, técnico y matemático, con un ejemplo aplicado a mi cultivo de papa y una pregunta típica del jurado con su respuesta.
```

**Pasar de prototipo a trabajo futuro**
```
Con lo que ya tengo, qué mejoras haría el sistema escalable a un invernadero comercial (varias zonas, energía solar, borde con Jetson, MPC, reentrenamiento continuo). Prioriza por costo-beneficio.
```

---

## 4. Consejos para sacarle el máximo provecho

1. **Una fase por conversación o hilo,** y pega siempre un resumen de lo decidido (estructura de carpetas, tópicos MQTT, esquemas) para mantener coherencia.
2. **Guarda todo en Git desde el día 1** (código, notebooks, `args.yaml` de cada entrenamiento) para poder demostrar reproducibilidad.
3. **Pide siempre datos reales primero.** Los datos sintéticos sirven para desarrollar y para el modo demostración, pero la validación de la tesis debe apoyarse en datos de tu invernadero.
4. **Verifica lo que el asistente afirme sobre versiones, umbrales agronómicos y referencias bibliográficas.** Los umbrales (humedad, temperatura, horas de riesgo) deben contrastarse con literatura de papa y con tu asesor o un agrónomo.
5. **Colab no es un servidor:** úsalo para entrenar, analizar y hacer demos temporales; el sistema continuo debe correr en tu laptop o en una VM.
6. **Cuida la seguridad eléctrica:** no avances a 220 V sin revisión de alguien con experiencia.
