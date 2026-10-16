# Algoritmos posibles del prototipo IoT–PID–IA para papa bajo invernadero

> Documento de apoyo para la tesis. Cada algoritmo indica **qué hace, dónde se usa en el sistema, ventajas/límites y métricas para evaluarlo**. Las opciones marcadas con ⭐ son las recomendadas para el alcance de un prototipo de tesis.

---

## 0. Mapa general: qué algoritmo va en cada capa

```
┌──────────────────────────── ESP32 (tiempo real) ────────────────────────────┐
│ Lectura de sensores → Filtrado (EMA/Kalman) → PID (+anti-windup) → Actuador │
└───────────────┬──────────────────────────────────────────────────────────────┘
                │ MQTT
┌───────────────▼──────────────── Servidor (laptop/VM) ────────────────────────┐
│ Visión: preprocesado → YOLO + SAHI → conteo/clasificación → severidad        │
│ Riesgo: BlightManager / Random Forest / LSTM (a partir de temp-humedad)      │
│ Fusión: reglas / lógica difusa → nivel de alerta → Telegram + ajuste setpoint│
└──────────────────────────────────────────────────────────────────────────────┘
```

| Capa | Algoritmo principal ⭐ | Alternativas / comparación |
|---|---|---|
| Preprocesamiento de imagen | CLAHE + redimensionado + normalización | Balance de blancos, filtros gaussianos |
| Detección de plagas/enfermedad | YOLO26 (n/s) | YOLOv8/11/12, RT-DETR, Faster R-CNN |
| Objetos pequeños (trips, mosca blanca) | YOLO + SAHI | Capa P2 de alta resolución, segmentación HSV |
| Clasificación de hoja (sana/enferma) | MobileNetV3 / EfficientNet (transfer learning) | ResNet50, ViT pequeño |
| Segmentación de lesión (severidad) | YOLO26-seg | U-Net, umbralización HSV/ExG |
| Filtrado de sensores | Media móvil exponencial (EMA) + filtro de Hampel | Filtro de Kalman |
| Control microclima | PID con anti-windup | PI, control difuso, MPC |
| Sintonización PID | Autosintonía por relé / Ziegler-Nichols | Cohen-Coon, IMC, optimización (Optuna) |
| Riesgo de tizón tardío | BlightManager (DRV) + Random Forest | SVM, XGBoost, LSTM, red neuronal |
| Detección de fallas de sensor | Z-score / Hampel / IQR | Isolation Forest |
| Decisión integrada | Reglas ponderadas / lógica difusa | Árbol de decisión |

---

## 1. Algoritmos de visión artificial

### 1.1 Preprocesamiento de imágenes (OpenCV)

| Técnica | Para qué | Nota |
|---|---|---|
| **Redimensionado y letterbox** | Ajustar al tamaño de entrada del modelo (640×640) | Mantener relación de aspecto |
| **Normalización** (0–1) | Estabilizar el entrenamiento | Lo hace YOLO internamente |
| **CLAHE** (ecualización adaptativa del histograma) | Corregir iluminación desigual del invernadero | Aplicar sobre el canal L en espacio LAB |
| **Balance de blancos (Gray World)** | Corregir tinte del agrofilm | Importante con luz bajo plástico |
| **Conversión a HSV** | Segmentar verde/amarillo/marrón de forma robusta | Útil para necrosis y trampas amarillas |
| **Filtro gaussiano / mediana** | Reducir ruido | La mediana conserva bordes |
| **Operaciones morfológicas** (apertura/cierre) | Limpiar máscaras binarias | Para conteo de insectos por contornos |

**Índice de vegetación RGB (ExG)** para separar planta del fondo:

```
ExG = 2G − R − B       (con canales normalizados)
```

### 1.2 Detección de objetos (el núcleo de la tesis)

| Algoritmo | Tipo | Fortalezas | Debilidades | Uso sugerido |
|---|---|---|---|---|
| ⭐ **YOLO26 (n/s/m)** | Una etapa, sin NMS, orientado a edge | Rápido en CPU, API sencilla, detección + segmentación + clasificación | Licencia AGPL-3.0; cifras de velocidad son del fabricante | Modelo principal |
| **YOLO11 / YOLOv12 / YOLOv8** | Una etapa | Muy documentados en literatura de papa | Requieren NMS | Comparativa en el capítulo de resultados |
| **RT-DETR** | Transformer en tiempo real | Sin NMS, buena precisión | Más pesado | Comparativa opcional |
| **Faster R-CNN** | Dos etapas | Precisión alta en objetos pequeños | Lento | Línea base clásica |
| **SSD-MobileNet** | Una etapa ligera | Muy liviano | Menor precisión | Solo si hay restricción de hardware |

**Cómo funciona la detección (resumen para el marco teórico):** una CNN extrae características a distintas escalas; la cabeza de detección predice por cada celda la caja `(x, y, w, h)`, la confianza y la clase. En versiones anteriores un paso de **NMS** (supresión de no máximos) eliminaba cajas duplicadas usando el IoU:

```
IoU = Área(A ∩ B) / Área(A ∪ B)
```

**Función de pérdida típica:** pérdida de caja (CIoU/DFL) + pérdida de clasificación (BCE) + pérdida de objetividad.

**Ejemplo mínimo de entrenamiento:**

```python
from ultralytics import YOLO

model = YOLO("yolo26n.pt")           # pesos preentrenados (transfer learning)
model.train(
    data="papa.yaml",                # rutas y clases
    epochs=100, imgsz=640, batch=16,
    patience=20,                     # early stopping
    augment=True
)
metrics = model.val()
```

### 1.3 Detección de objetos pequeños: SAHI ⭐

- **Problema:** trips (0.5–2 mm) y mosca blanca ocupan pocos píxeles; al redimensionar la imagen completa a 640 px se pierden.
- **Algoritmo SAHI:** divide la imagen en ventanas con solapamiento → corre el detector en cada una → fusiona resultados con NMS global.
- **Parámetros a ajustar:** tamaño de slice (p. ej. 320–640), solapamiento (0.2–0.3), umbral de confianza.
- **Costo:** más tiempo por imagen (aceptable: se fotografía cada pocos minutos).

```python
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction

det = AutoDetectionModel.from_pretrained(
    model_type="ultralytics", model_path="best.pt", confidence_threshold=0.3)
res = get_sliced_prediction("trampa.jpg", det,
    slice_height=512, slice_width=512,
    overlap_height_ratio=0.2, overlap_width_ratio=0.2)
conteo = len(res.object_prediction_list)
```

**Alternativa clásica sin deep learning (línea base):** segmentación por color HSV sobre la trampa amarilla + `cv2.findContours` + filtrado por área. Sirve para comparar contra YOLO y justificar el uso de IA.

### 1.4 Clasificación de hojas (sana / tizón temprano / tizón tardío)

| Algoritmo | Parámetros aprox. | Comentario |
|---|---|---|
| ⭐ **MobileNetV3 (small/large)** | Bajo | Ideal para despliegue ligero |
| **EfficientNet-B0/B2** | Medio | Buen equilibrio precisión/costo |
| **ResNet50** | Alto | Línea base clásica |
| **Vision Transformer pequeño (ViT/DeiT)** | Alto | Opcional, requiere más datos |

**Transfer learning en dos fases:**
1. Congelar la base preentrenada (ImageNet) y entrenar solo el clasificador.
2. Descongelar capas finales (*fine-tuning*) con tasa de aprendizaje baja (1e-5 a 1e-4).

### 1.5 Segmentación y severidad de la lesión

- **YOLO26-seg / U-Net:** generan máscara píxel a píxel de la zona afectada.
- **Índice de severidad:**

```
Severidad (%) = (píxeles de lesión / píxeles de hoja) × 100
```

Se puede mapear a una escala de 0–5 o a niveles (leve, moderado, severo) para decidir la alerta.

### 1.5.1 Aumento de datos (Albumentations)

Rotación, volteo, cambio de brillo/contraste, desenfoque, ruido gaussiano, *mosaic*, *mixup*, recorte aleatorio. **Aplica el aumento solo al conjunto de entrenamiento**, nunca a validación ni prueba.

### 1.6 Métricas de evaluación de visión

| Métrica | Fórmula / significado |
|---|---|
| **Precisión (P)** | TP / (TP + FP) |
| **Recall (R)** | TP / (TP + FN). Crítico en detección temprana: un falso negativo es una plaga que pasa |
| **F1** | 2·P·R / (P + R) |
| **mAP@0.5** | Media de AP con IoU ≥ 0.5 |
| **mAP@0.5:0.95** | Promedio sobre umbrales de IoU de 0.5 a 0.95 |
| **Matriz de confusión** | Errores por clase |
| **FPS / latencia por imagen** | Viabilidad en CPU |
| **Error de conteo (MAE)** | Para trampas: |conteo real − conteo detectado| promedio |

**Buenas prácticas:** división 70/15/15 (entrenamiento/validación/prueba) **sin fuga de datos** (fotos de la misma planta o del mismo día no deben quedar en conjuntos distintos), y validación final con imágenes tomadas en *tu* invernadero.

---

## 2. Algoritmos de procesamiento de señales de sensores

### 2.1 Filtrado

| Algoritmo | Fórmula / idea | Cuándo usarlo |
|---|---|---|
| ⭐ **Media móvil exponencial (EMA)** | `y[k] = α·x[k] + (1−α)·y[k−1]`, con α ≈ 0.1–0.3 | Suavizar temperatura/humedad antes del PID |
| **Media móvil simple** | Promedio de N muestras | Alternativa sencilla |
| ⭐ **Filtro de Hampel** | Reemplaza valores que superan k·MAD respecto a la mediana de una ventana | Eliminar picos espurios del DHT/SHT |
| **Filtro de mediana** | Mediana de una ventana | Ruido impulsivo |
| **Filtro de Kalman 1D** | Estima el estado combinando modelo y medición | Cuando se necesita estimación óptima; más complejo |

```python
class EMA:
    def __init__(self, alpha=0.2): self.a, self.y = alpha, None
    def update(self, x):
        self.y = x if self.y is None else self.a*x + (1-self.a)*self.y
        return self.y
```

### 2.2 Fusión de sensores

- **Promedio ponderado** de dos SHT31 (peso inversamente proporcional a la varianza de cada uno).
- **Validación cruzada entre sensores:** si difieren más de un umbral (p. ej. 2 °C) se marca falla y se usa el sensor sano.

### 2.3 Calibración

- **Regresión lineal** contra el termo-higrómetro de referencia: `valor_real = a·lectura + b`.
- Reportar **RMSE**, **MAE** y **R²** de cada sensor (aporte de rigor en la tesis).

### 2.4 Detección de fallas y anomalías

| Algoritmo | Uso |
|---|---|
| **Z-score** (`|x−μ|/σ > 3`) | Valores atípicos simples |
| **IQR** | Alternativa robusta |
| **Detección de sensor "congelado"** | Varianza ≈ 0 durante N lecturas |
| **Isolation Forest** | Anomalías multivariables (opcional) |

---

## 3. Algoritmos de control (regulación microclimática)

### 3.1 Controlador PID ⭐

**Forma ideal en tiempo continuo:**

```
u(t) = Kp·e(t) + Ki·∫e(t)dt + Kd·de(t)/dt          e(t) = SP − PV
```

**Forma discreta (la que se programa):**

```
u[k] = Kp·e[k] + Ki·Ts·Σe[i] + Kd·(e[k] − e[k−1]) / Ts
```

**Mejoras indispensables en un sistema real:**

| Mejora | Problema que resuelve |
|---|---|
| **Anti-windup** (limitar o "clamping" del integral) | El integral se acumula cuando el actuador está saturado → sobreimpulso enorme |
| **Derivada sobre la medición** (no sobre el error) | Evita picos al cambiar el setpoint |
| **Filtro en el término derivativo** | Reduce amplificación del ruido |
| **Zona muerta (deadband)** | Evita que el actuador oscile por ruido |
| **Saturación de salida (0–100 %)** | Protege el actuador |
| **Transferencia sin golpes (bumpless)** | Cambio suave entre manual y automático |

```python
from simple_pid import PID
pid = PID(Kp=2.0, Ki=0.1, Kd=0.5, setpoint=18.0)  # °C objetivo
pid.output_limits = (0, 100)                       # % PWM
pid.sample_time = 5                                # s
u = pid(temperatura_medida)
```

### 3.2 Esquema de actuadores por variable controlada

| Variable | Actuador de subida | Actuador de bajada | Tipo de salida |
|---|---|---|---|
| **Temperatura** | Calefactor + SSR | Extractor PWM / ventana | PWM lento (calefactor) y PWM rápido (ventilador) |
| **Humedad relativa** | Humidificador / nebulizador | Extractor / calefacción | On/Off con histéresis o PWM |
| **Humedad de suelo** | Bomba / electroválvula | — | Riego por pulsos |
| **CO₂ (opcional)** | — | Ventilación | Control por rango |

**Control de rango dividido (*split-range*):** una sola salida PID de −100 % a +100 %; la parte negativa activa el enfriamiento y la positiva el calentamiento. Evita que calefactor y extractor trabajen a la vez.

**PWM de ventana de tiempo (*time-proportional*) para el SSR:** en un ciclo de 10–30 s, el calefactor está encendido `u %` del ciclo.

### 3.3 Sintonización de ganancias

| Método | Idea | Pasos |
|---|---|---|
| ⭐ **Autosintonía por relé (Åström–Hägglund)** | Un relé hace oscilar la variable; se mide amplitud y periodo crítico | Ejecutar autotune → obtener Ku y Tu → calcular ganancias |
| ⭐ **Ziegler-Nichols (lazo cerrado)** | Subir Kp hasta oscilación sostenida | PID: `Kp = 0.6·Ku`, `Ti = 0.5·Tu`, `Td = 0.125·Tu` |
| **Ziegler-Nichols (curva de reacción)** | Respuesta al escalón: retardo L y constante de tiempo T | `Kp = 1.2·T/(K·L)`, `Ti = 2L`, `Td = 0.5L` |
| **Cohen-Coon** | Mejor para procesos con retardo grande | Útil para invernaderos (inercia térmica) |
| **IMC / Lambda tuning** | Respuesta sin sobreimpulso | Más suave, adecuado para plantas |
| **Optimización numérica** (Optuna, `scipy.optimize`) | Minimiza una función de costo (ISE/ITAE) sobre un modelo | Requiere modelo identificado |

**Nota práctica:** los invernaderos tienen **gran inercia y retardo**, por lo que lo habitual es un **PI** (derivada pequeña o cero) con anti-windup.

### 3.4 Identificación del sistema

Aplicar un escalón al actuador y registrar la respuesta. Ajustar un **modelo de primer orden con retardo (FOPDT)**:

```
G(s) = K · e^(−L·s) / (T·s + 1)
```

Herramientas: `scipy.optimize.curve_fit`, `python-control`. Con el modelo puedes simular antes de probar en físico.

### 3.5 Alternativas avanzadas (para comparar o como trabajo futuro)

| Algoritmo | Ventaja | Complejidad |
|---|---|---|
| **Feedforward** (compensa radiación solar o temperatura exterior) | Anticipa perturbaciones | Baja |
| **Control en cascada** (suelo → riego) | Mejora el rechazo de perturbaciones | Media |
| **Gain scheduling** (ganancias distintas día/noche) | La dinámica cambia con la radiación | Media |
| **Control difuso (Fuzzy)** | No requiere modelo, reglas lingüísticas | Media |
| **MPC (control predictivo)** | Maneja restricciones y múltiples variables | Alta |
| **On/Off con histéresis** | Línea base para demostrar la mejora del PID | Muy baja |

**Comparación recomendada para la tesis:** `On/Off` vs `PID`, medidos con las métricas de la sección 3.6. Es la forma más clara de demostrar el aporte del PID.

### 3.6 Métricas de desempeño del control

| Métrica | Significado |
|---|---|
| **Tiempo de subida (tr)** | De 10 % a 90 % del valor final |
| **Tiempo de establecimiento (ts)** | Entrada y permanencia en la banda del ±2 % |
| **Sobreimpulso máximo (Mp, %)** | Cuánto se pasa del setpoint |
| **Error en estado estable (ess)** | Diferencia final contra el setpoint |
| **IAE / ISE / ITAE** | Integrales del error absoluto, cuadrático o ponderado por tiempo |
| **Esfuerzo de control** | Cuánto trabaja el actuador (desgaste y energía) |
| **Tiempo dentro del rango óptimo (%)** | Porcentaje del tiempo con la variable en rango agronómico |

---

## 4. Algoritmos de predicción de riesgo de plagas y enfermedades

### 4.1 Modelo basado en reglas: BlightManager (valor de riesgo diario) ⭐

Modelo danés que calcula un **valor de riesgo diario (DRV)** a partir de temperatura y humedad relativa horarias. Es transparente, no requiere entrenamiento y sirve de **línea base** para comparar con aprendizaje automático. Verifica la tabla exacta de ponderación en la fuente original antes de implementarla.

**Condiciones típicas que favorecen el tizón tardío (*Phytophthora infestans*):** humedad relativa alta (≥ 90 %) sostenida, temperaturas frescas a moderadas y presencia de agua libre en la hoja. Una versión simple de regla:

```python
def horas_riesgo(df, hr_min=90, t_min=10, t_max=25):
    return ((df.hr >= hr_min) & (df.temp.between(t_min, t_max))).sum()

alerta = horas_riesgo(ultimas_24h) >= 8   # umbral a calibrar con la literatura y tus datos
```

### 4.2 Modelos de aprendizaje automático supervisado

| Algoritmo | Entradas | Ventaja | Cuándo usar |
|---|---|---|---|
| ⭐ **Random Forest** | Temp, HR, horas de hoja húmeda, luz, déficit de presión de vapor | Robusto, da importancia de variables | Modelo principal tabular |
| **XGBoost / LightGBM** | Igual | Alta precisión | Comparación |
| **SVM (kernel RBF)** | Igual | Funciona con pocos datos | Antecedente en literatura de tizón |
| **Regresión logística** | Igual | Interpretable | Línea base |
| **Red neuronal (MLP)** | Igual | Captura no linealidades | Comparación |
| **LSTM / GRU** | Ventana de 24–72 h de series temporales | Capta dependencia temporal | Si logras suficientes datos |
| **Prophet / ARIMA** | Serie de temperatura/humedad | Pronóstico del microclima | Predicción a corto plazo |

**Variable derivada útil: Déficit de Presión de Vapor (VPD)**

```
es = 0.6108 · exp(17.27·T / (T + 237.3))      [kPa]
VPD = es · (1 − HR/100)
```

**Problema práctico:** necesitarás **etiquetas** (días con/sin infección o plaga detectada). Opciones: etiquetar con el conteo/detección de visión (esto conecta ambos módulos), registros del agrónomo, o usar BlightManager como etiqueta débil.

**Metodología de entrenamiento:**
- Validación cruzada **temporal** (*TimeSeriesSplit*), no aleatoria, para evitar fuga de información.
- Balanceo de clases (`class_weight`, SMOTE) si los eventos de riesgo son raros.
- Métricas: precisión, recall, F1, AUC-ROC, y **anticipación media** (horas antes de la detección visual).

### 4.3 Estado de crecimiento y estrés hídrico (opcional)

- **Grados-día de crecimiento (GDD)** para estimar la fase fenológica: `GDD = Σ max(0, (Tmax+Tmin)/2 − Tbase)`.
- **Umbrales por etapa** (emergencia, tuberización, floración) para cambiar los *setpoints* del PID según la fase.

---

## 5. Algoritmo de fusión y decisión (integra IoT + PID + IA)

Es el algoritmo que une los tres módulos y justifica el título de la tesis.

### 5.1 Puntaje de riesgo combinado ⭐

```
Riesgo = w1·R_clima + w2·R_visión + w3·R_tendencia          (w1 + w2 + w3 = 1)
```

| Componente | Origen | Rango |
|---|---|---|
| `R_clima` | Horas de riesgo / probabilidad del modelo RF o BlightManager | 0–1 |
| `R_visión` | Detecciones o severidad normalizada del modelo YOLO | 0–1 |
| `R_tendencia` | Pendiente del conteo de insectos en trampas (últimos días) | 0–1 |

### 5.2 Niveles de acción

| Riesgo | Nivel | Acción del sistema |
|---|---|---|
| < 0.3 | Normal | Mantener *setpoints* |
| 0.3 – 0.6 | Precaución | Aumentar ventilación; reducir HR objetivo; notificar |
| 0.6 – 0.8 | Alerta | Ajustar *setpoints* + alerta Telegram con foto |
| > 0.8 | Crítico | Alerta urgente; pedir inspección humana |

### 5.3 Lógica difusa para la decisión (alternativa)

Reglas lingüísticas del tipo:
- SI humedad **alta** Y temperatura **moderada** Y detección **alta** ENTONCES riesgo **muy alto**.
- Librería: `scikit-fuzzy`.

### 5.4 Adaptación del *setpoint* (lazo externo)

El PID sigue siendo el lazo interno y rápido (en el ESP32). La IA actúa como **lazo externo lento**: modifica el setpoint de humedad o temperatura vía MQTT cuando el riesgo sube. Si el servidor falla, el PID continúa con el último setpoint seguro.

```python
def ajustar_setpoint(riesgo, sp_base):
    if riesgo > 0.6:
        return {"hr_max": sp_base["hr_max"] - 5, "ventilacion_min": 30}
    return sp_base
```

---

## 6. Algoritmos de gestión de datos y alertas

| Algoritmo / técnica | Uso |
|---|---|
| **Muestreo periódico** | Sensores cada 5–30 s; fotos cada 30 s–5 min según el objetivo |
| **Remuestreo y agregación** (media por minuto/hora) | Reducir volumen para el modelo |
| **Detección de cambios (CUSUM)** | Detectar desvíos sostenidos de temperatura/humedad |
| **Histéresis y anti-rebote de alertas** | Evitar enviar la misma alerta repetidamente |
| **Cola de mensajes (MQTT QoS 1)** | Garantizar entrega de comandos |
| **Watchdog / *heartbeat*** | Detectar caída de nodos o del servidor |

---

## 7. Plan de experimentos para comparar algoritmos (capítulo de resultados)

| Experimento | Algoritmos comparados | Métrica principal |
|---|---|---|
| E1. Detección de enfermedades | YOLO26n vs YOLO11n vs YOLOv8n vs Faster R-CNN | mAP@0.5, recall, FPS en CPU |
| E2. Plagas en trampa | YOLO26 solo vs YOLO26 + SAHI vs segmentación HSV | mAP, error de conteo (MAE) |
| E3. Clasificación de hoja | MobileNetV3 vs EfficientNet-B0 vs ResNet50 | Exactitud, F1, tamaño del modelo |
| E4. Control de temperatura | On/Off vs PI vs PID (con autotune) | Sobreimpulso, ts, ess, IAE |
| E5. Control de humedad | On/Off con histéresis vs PID | Tiempo en rango (%), esfuerzo de control |
| E6. Predicción de riesgo | BlightManager vs Random Forest vs SVM vs LSTM | F1, AUC, horas de anticipación |
| E7. Sistema completo | Con sistema vs sin sistema (testigo manual) | Incidencia de plaga, variación microclimática |
| E8. Robustez | Variar luz, hora, ángulo de cámara | Caída de mAP |

**Diseño experimental sugerido:** dos unidades (**control** sin sistema y **tratamiento** con sistema), repeticiones suficientes y análisis estadístico (prueba t, ANOVA o Mann-Whitney).

---

## 8. Hiperparámetros y buenas prácticas de entrenamiento

| Aspecto | Recomendación |
|---|---|
| Modelo base | Pesos preentrenados (COCO/ImageNet) y *fine-tuning* |
| Tamaño de imagen | 640 px (más alto, p. ej. 960–1280, para insectos pequeños) |
| Épocas | 100–300 con *early stopping* (`patience`) |
| Optimizador | SGD (momento 0.9) o AdamW; probar ambos |
| Tasa de aprendizaje | 0.01 (SGD) con decaimiento coseno; 1e-3 a 1e-4 (AdamW) |
| Datos mínimos | Cientos de imágenes por clase propias del invernadero |
| Clases desbalanceadas | Aumento dirigido, pesos de clase, *focal loss* |
| Reproducibilidad | Fijar semillas, guardar `args.yaml`, registrar versiones de librerías |
| Seguimiento | TensorBoard, Weights & Biases o MLflow |

---

## 9. Resumen: lista corta de algoritmos para el prototipo

1. **Visión:** YOLO26 (n/s) + **SAHI**; clasificación con MobileNetV3 como comparación.
2. **Preprocesamiento:** CLAHE, balance de blancos, HSV para trampas.
3. **Sensores:** EMA + filtro de Hampel + calibración lineal.
4. **Control:** **PID con anti-windup** (PI en la práctica), control *split-range*, PWM de ventana de tiempo para el calefactor.
5. **Sintonización:** autosintonía por relé y Ziegler-Nichols, validada con identificación FOPDT.
6. **Riesgo:** BlightManager (línea base) + Random Forest; LSTM como extensión.
7. **Decisión:** puntaje de riesgo ponderado (clima + visión + tendencia) y ajuste de *setpoints* en lazo externo.
8. **Evaluación:** mAP/recall/F1 para visión, ts/Mp/ess/IAE para control, F1/AUC para riesgo, y comparación con y sin sistema.

> **Nota de rigor:** los umbrales (HR, temperatura, horas de riesgo, pesos w1–w3) son puntos de partida. Calíbralos con literatura agronómica de papa para tu altitud y variedad (consulta a un agrónomo o INIAF) y con tus propios datos del invernadero.
