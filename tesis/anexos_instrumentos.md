# ANEXOS DE INSTRUMENTOS METODOLÓGICOS Y PROTOCOLOS EXPERIMENTALES

**Proyecto:** Sistema prototipo integrado de IoT, control PID e inteligencia artificial para la regulación microclimática y detección temprana de plagas en el cultivo de papa bajo invernadero  
**Institución:** Carrera de Ingeniería de Sistemas, Universidad Salesiana de Bolivia (La Paz, Bolivia)  
**Postulante:** Alvaro Rodrigo De La Barra Velasco  
**Vinculación documental:** Complemento operativo del **Capítulo III. Diseño Metodológico** (`tesis/cap3_diseno_metodologico.md`)  

> **Advertencia de integridad probatoria:** Los protocolos e instrumentos incluidos en este documento constituyen los formatos técnicos y de campo propuestos para la ejecución física y validación experta en el invernadero piloto de La Paz. Ninguna casilla de medición física o respuesta humana ha sido prellenada ni simulada como dato de campo ejecutado.

---

## Anexo A. Protocolos Experimentales Detallados (`E1`–`E8`)

Los ocho protocolos experimentales están alineados con la tabla relacional `experimentos_ensayos` (`server/app/models/schemas.sql`) y el script de inicialización `scripts/seed_experiments.py`. Se precisa explícitamente que las fechas referenciales de marzo–abril y los valores JSON de `seed_experiments.py` corresponden a registros semilla de prueba de *software*, debiendo sustituirse por las mediciones reales ejecutadas durante la ventana experimental en campo.

### Protocolo E1: Validación metrológica de sensores y repetibilidad a $3.600\text{ m s. n. m.}$

- **Objetivos vinculados:** OE1.
- **Duración nominal de referencia:** $\ge 58\text{ h}$ continuas de contraste sincrónico.
- **Precondiciones y materiales:** Nodo `ESP32 DevKit V1` con `firmware.bin` cargado, sensores `SHT31` (I2C `0x44`, bajo pantalla de radiación ventilada), `DS18B20` (OneWire `GPIO4`), `BH1750` (I2C), sensor capacitivo de suelo v1.2 (`GPIO34`), termohigrómetro patrón certificado `[DATO FALTANTE: marca/modelo y certificado vigente]`, estufa de secado a $105\,^\circ\text{C}$ y balanza analítica ($0{,}01\text{ g}$).
- **Procedimiento paso a paso:**
  1. Verificar la lectura I2C/OneWire y activar el registro continuo a $1\text{ Hz}$ en `InfluxDB v2`.
  2. Colocar el `SHT31` y la sonda del termohigrómetro patrón a una distancia $\le 5\text{ cm}$ dentro de la misma cámara de referencia ventilada, evitando radiación solar directa.
  3. Registrar pares sincrónicos cada $5\text{ min}$ durante $58\text{ h}$ cubriendo ciclos térmicos diurnos y nocturnos de La Paz ($P_{\text{atm}} \approx 67{,}5\text{ kPa}$).
  4. Ejecutar paralelamente el protocolo de calibración gravimétrica de sustrato descrito en el **Anexo B**.
- **Indicadores y criterio de aceptación:** Sesgo medio, histéresis ascenso/descenso, deriva diaria, $\text{RMSE}_T \le 0{,}3\,^\circ\text{C}$, $\text{RMSE}_{\text{HR}} \le 2{,}0\,\%$ y coeficiente de determinación $R^2 \ge 0{,}90$ en la curva $\text{ADC} \to \% \text{ VWC}$.
- **Estado actual:** Pendiente de ejecución física `[DATO FALTANTE]`.

### Protocolo E2: Identificación de la dinámica térmica FOPDT en lazo abierto

- **Objetivos vinculados:** OE2.
- **Duración nominal de referencia:** $4\text{ h}$ (incluyendo estabilización previa, escalón de $30$–$60\text{ min}$ y retorno térmico).
- **Precondiciones y materiales:** Módulo de invernadero cerrado con cubierta instalada, calefactor `220 V AC` conectado al `SSR` (`GPIO23`), nodo ESP32 en modo `MANUAL` y registro en `InfluxDB v2` a $1\text{ Hz}$.
- **Procedimiento paso a paso:**
  1. Mantener el calefactor apagado ($u = 0\,\%$) hasta alcanzar estabilidad térmica basal ($|\Delta T/\Delta t| < 0{,}05\,^\circ\text{C/min}$ durante $10\text{ min}$), preferentemente en horario nocturno o de nubosidad uniforme para minimizar perturbación solar.
  2. Aplicar un escalón positivo constante de potencia de calefacción ($\Delta u = 60\,\%$ a $70\,\%$) registrando $T_{\text{aire}}(t)$ y $T_{\text{ext}}(t)$ a $1\text{ Hz}$ hasta alcanzar el $95\,\%$ de la nueva temperatura estacionaria.
  3. Exportar la serie temporal y ejecutar el ajuste no lineal por mínimos cuadrados (`scipy.optimize.curve_fit`, script basado en `scripts/ejecutar_fase2_identificacion_pid.py`) para estimar $K$, $\tau$ y $\theta$.
  4. Verificar residuos mediante Shapiro-Wilk y Durbin-Watson ($\text{DW}$).
- **Indicadores y criterio de aceptación:** $K$ ($^\circ\text{C}/\%$), $\tau$ ($\text{s}$), $\theta$ ($\text{s}$), $R^2 \ge 0{,}95$ y $\text{RMSE}$ documentado.
- **Estado actual:** Ejecutado únicamente sobre datos simulados (`prueba_escalon_fopdt.csv`: $K=0{,}1639$, $\tau=242{,}96\text{ s}$, $\theta=33{,}33\text{ s}$, $R^2=0{,}9990$). Ensayo físico pendiente `[DATO FALTANTE]`.

### Protocolo E3: Sintonización comparativa de control térmico (Optuna vs. métodos clásicos y On/Off)

- **Objetivos vinculados:** OE2, OE5.
- **Duración nominal de referencia:** $72\text{ h}$ distribuidas en bloques temporales equivalentes.
- **Precondiciones y materiales:** Parámetros reales $(K, \tau, \theta)$ obtenidos en `E2`, script de optimización bayesiana `Optuna` TPE ($100$ *trials*), `ESP32` en modo `AUTO` y registro en `auditoria_control_pid` e `InfluxDB v2`.
- **Procedimiento paso a paso:**
  1. Calcular las ganancias PID mediante `Ziegler-Nichols`, `Cohen-Coon`, `IMC` (Skogestad, 2003) y `Optuna` TPE minimizando $J = \text{IAE} + 50\max(0, M_p - 5)^2 + 0{,}01\,TV_u$.
  2. Ejecutar ensayos comparativos ante cambio de consigna ($SP_T = 20{,}0\,^\circ\text{C}$) y descenso térmico nocturno bajo: (a) control On/Off ($\pm 0{,}5\,^\circ\text{C}$, Nivel 0); (b) sintonías clásicas; y (c) PID `Optuna` *split-range* $10\text{ Hz}$ (Nivel 1).
  3. Registrar `temp_ext`, `luz_lux`, `pv_temp`, `sp_temp` y `cv_salida` a $1\text{ Hz}$.
- **Indicadores y criterio de aceptación:** Reducción de $\text{IAE} \ge 25\,\%$ frente a On/Off, $M_p \le 5\,\%$, $e_{ss} \le 5\,\%$, menor $\text{ITAE}$ y menor desgaste $TV_u$.
- **Estado actual:** Ejecutado en simulación matemática (Tabla 2 del informe `02_analisis_datos.md`: $\Delta\text{IAE} = -29{,}86\,\%$, $M_p = 1{,}61\,\%$, $\Delta TV_u = -91{,}95\,\%$). Ensayo físico pendiente `[DATO FALTANTE]`.

### Protocolo E4: Control psicrométrico desacoplado de humedad relativa y $\text{VPD}$

- **Objetivos vinculados:** OE2, OE5.
- **Duración nominal de referencia:** $60\text{ h}$ continuas.
- **Precondiciones y materiales:** Extractor axial $12\text{ V}$ vía `MOSFET` PWM $25\text{ kHz}$ (`GPIO19`), humidificador ultrasónico (`GPIO18`), bomba de riego (`GPIO26`) con interruptor flotador (`GPI35`), y registro de volumen de agua aplicado.
- **Procedimiento paso a paso:**
  1. Configurar el objetivo fisiológico $\text{VPD} \in [0{,}8;\, 1{,}2]\text{ kPa}$ mediante consignas acopladas de temperatura y humedad ($SP_{\text{HR}} = 70$–$75\,\%$).
  2. Comparar la proporción de horas fuera de rango y los eventos en que $T_{\text{aire}} \le T_d + 0{,}5\,^\circ\text{C}$ (riesgo de condensación) entre Nivel 0 y Nivel 1.
  3. Medir el volumen de agua consumido mediante aforo en tanque o caudalímetro instalado (`[DATO FALTANTE: caudalímetro]`).
- **Indicadores y criterio de aceptación:** Permanencia $\ge 85\,\%$ del tiempo en $\text{VPD} \in [0{,}8;\, 1{,}2]\text{ kPa}$, mitigación de eventos de rocío nocturno y registro descriptivo en $\text{L/m}^2/\text{semana}$.
- **Estado actual:** Evaluado en serie agroclimática simulada (`2.160 h`). Ensayo físico pendiente `[DATO FALTANTE]`.

### Protocolo E5: Detección fitosanitaria foliar en campo (*Phytophthora infestans* y *Alternaria solani*)

- **Objetivos vinculados:** OE3, OE5.
- **Duración nominal de referencia:** Campaña de captura y validación de $\ge 32\text{ h}$ distribuidas en ventanas lumínicas estratificadas.
- **Precondiciones y materiales:** Cámara USB 1080p en soporte rígido a $25\text{ cm} \pm 5\text{ cm}$ ($70^\circ$–$80^\circ$), servidor local con `FastAPI` y pesos `YOLO26n`/`YOLO11n`, y **Anexo C** (*Ground Truth* agronómico).
- **Procedimiento paso a paso:**
  1. Capturar imágenes de hojas en tres franjas (`08:00–10:00`, `12:00–13:30`, `16:30–18:00`) identificando cada unidad con código de planta (`planta_XX`).
  2. Aplicar revisión y etiquetado agronómico de lesiones activas (incluyendo halo clorótico) y estimación de severidad real ($\le 5\,\%$ temprana vs. $> 5\,\%$).
  3. Particionar `70/15/15` por grupo físico (`planta_XX`), entrenar/ajustar el detector con semántica `box_semantics = "lesion"`, generar `best.metadata.json` con hash `SHA-256` y evaluar en el conjunto `test` independiente en CPU.
- **Indicadores y criterio de aceptación:** Meta experimental de campo $\text{mAP@0.50} \ge 0{,}80$, $\text{F1-Score} \ge 85\,\%$ ante lesiones $\le 5\,\%$, y latencia cronometrada en CPU local.
- **Estado actual:** Piloto real ejecutado en Google Colab sobre conjuntos públicos (`PlantVillage` Acc@1 = $1{,}000$; `PlantDoc` test $\text{mAP@0.50} = 0{,}4926$ con cajas de hoja completa y `severidad_disponible = false`). Captura, anotación de lesión y entrenamiento local pendientes `[DATO FALTANTE]`.

### Protocolo E6: Inspección de trampas cromáticas amarillas con `SAHI` y desempeño telemétrico IoT

- **Objetivos vinculados:** OE1, OE3.
- **Duración nominal de referencia:** $34\text{ h}$ de muestreo periódico óptico e ingesta telemétrica continua.
- **Precondiciones y materiales:** Trampas adhesivas amarillas ($15 \times 20\text{ cm}$) dispuestas a nivel de copa, luz LED difusa, cámara USB 1080p a $15\text{ cm} \pm 2\text{ cm}$ ($90^\circ$), servicio `vision_service.py` con `SAHI 0.12.8` (`320 × 320 px`, solapamiento `0.20`).
- **Procedimiento paso a paso:**
  1. Fotografiar diariamente las trampas a hora fija bajo iluminación difusa sin reflejo especular.
  2. Etiquetar individualmente *Liriomyza huidobrensis*, *Myzus persicae* y *Phthorimaea operculella* (prohibido agrupar clústeres en una sola caja; umbral de visibilidad $\ge 40\,\%$).
  3. Contrastar la inferencia YOLO estándar frente a `YOLO + SAHI` en CPU sobre el conjunto `test` agrupado por código de trampa (`trampa_XX`), midiendo incremento de $\text{Recall}$, reducción de falsos negativos y latencia (ms).
  4. Verificar simultáneamente la tasa de disponibilidad de paquetes MQTT ($D_{\text{reg}}$) y latencia extremo a extremo ($L_{\text{tx}}$).
- **Indicadores y criterio de aceptación:** Incremento estadísticamente significativo de $\text{Recall}$ con `SAHI` en objetos $< 32 \times 32\text{ px}$, $D_{\text{reg}} \ge 98\,\%$ y $L_{\text{tx}} \le 5\text{ s}$.
- **Estado actual:** Motor `SAHI` integrado y verificado en código (`vision_service.py`, `117 pytest`), con cifras de diseño en `experiments/e2_trampas/README.md`. Dataset real de insectos en trampas amarillas y pesos entrenados pendientes `[DATO FALTANTE]`.

### Protocolo E7: Predicción de riesgo bioclimático, explicabilidad `SHAP` y fusión multimodal

- **Objetivos vinculados:** OE4.
- **Duración nominal de referencia:** $\ge 120\text{ h}$ ($5$ días) de serie temporal continua con episodios de alta humedad.
- **Precondiciones y materiales:** Contenedor `inference_worker` (`server/app/worker.py`), modelo `XGBoost` calibrado isotónicamente, `TreeExplainer` SHAP, bot de `Telegram` configurado y base `SQLite WAL`.
- **Procedimiento paso a paso:**
  1. Alimentar la ventana deslizante causal de $48\text{ h}$ con telemetría real de `SHT31` y detecciones visuales verificadas.
  2. Comparar las probabilidades emitidas por `XGBoost` calibrado frente a la línea base epidemiológica (`BlightManager`/Hutton) contra la confirmación agronómica de aparición de síntomas en el invernadero.
  3. Verificar la transición automática de niveles (`BAJO`, `MEDIO`, `ALTO`, `CRÍTICO`) en la función $S_{\text{riesgo}} = 0{,}45\,P_{\text{clima}} + 0{,}35\,S_{\text{visión}} + 0{,}20\,T_{48\text{h}}$, el despacho de nuevos *setpoints* vía MQTT y el tiempo transcurrido hasta la recepción de alerta con imagen en `Telegram`.
- **Indicadores y criterio de aceptación:** Menor *Brier Score* probabilístico, $\text{ROC-AUC} > 0{,}50$, coherencia agronómica de valores $|\text{SHAP}|$ y tiempo de alerta $t_{\text{alerta}} \le 30\text{ min}$.
- **Estado actual:** Evaluado en simulación biofísica de 90 días (`XGBoost` $\text{Brier}=0{,}1878$, $\text{ROC-AUC}=0{,}7123$, `lwh_suma_48h` $|\text{SHAP}|=1{,}3257$). Validación epidemiológica de campo pendiente `[DATO FALTANTE]`.

### Protocolo E8: Ensayo integrado 24/7 y resiliencia ante helada altiplánica (Nivel 0 vs. Nivel 1)

- **Objetivos vinculados:** OE1, OE2, OE4, OE5.
- **Duración nominal de referencia:** $\ge 192\text{ h}$ ($8$ días continuos) en campo por bloque comparativo.
- **Precondiciones y materiales:** Prototipo integral operativo (hardware, 6 contenedores Docker, `Django 6.1.2`, `SQLite WAL`), lote/bloque testigo Nivel 0, **Anexo C** y **Anexo D**.
- **Procedimiento paso a paso:**
  1. Operar de manera ininterrumpida durante $192\text{ h}$ bajo condiciones ambientales reales de La Paz (incluyendo descensos nocturnos de $T_{\text{ext}}$ y ciclos de nubosidad/radiación).
  2. Simular o registrar al menos un corte de conectividad Wi-Fi/servidor de $15\text{ min}$ para verificar la autonomía del lazo interno a $10\text{ Hz}$ y la recuperación del *Watchdog* de $10\text{ s}$.
  3. Comparar estadísticamente las distribuciones de $T_{\text{aire}}$, $\text{HR}$, $\text{VPD}$, $\text{IAE}$, $TV_u$, disponibilidad $D_{\text{reg}}$, latencia $L_{\text{tx}}$ e incidencia fitosanitaria entre Nivel 0 y Nivel 1 mediante la prueba U de Mann-Whitney ($\alpha = 0{,}05$).
  4. Aplicar el **Anexo D** (ISO/IEC 25010) a los operadores al cierre del ensayo.
- **Indicadores y criterio de aceptación:** $D_{\text{reg}} \ge 98\,\%$, $L_{\text{tx}} \le 5\text{ s}$, reducción significativa de $\text{IAE}$ y excursiones fuera de $\text{VPD}$ óptimo, ausencia de daño por helada en Nivel 1 y valoración media $\ge 4{,}0/5{,}0$ en encuesta ISO/IEC 25010.
- **Estado actual:** Infraestructura de *software* verificada (`117 pytest`). Ensayo físico continuo 24/7 pendiente `[DATO FALTANTE]`.

---

## Anexo B. Ficha de Calibración Metrológica (Gravimétrica $105\,^\circ\text{C}$ e Higrométrica)

**Código de registro:** `CAL-MET-____` | **Fecha:** `____-__-__` | **Responsable:** `____________________`  
**Ubicación y presión barométrica local:** La Paz, Bolivia (~`____ m s. n. m.`, `____ kPa`)

### Parte I. Contraste Termohigrométrico (`SHT31` y `DS18B20` vs. Patrón Certificado)

- **Identificación del patrón:** Marca/Modelo: `______________` | N.º Serie: `__________` | Certificado vigente hasta: `____-__-__`
- **ID del nodo ESP32:** `__________________` | **Intervalo de muestreo:** `5 min` | **Duración total:** `____ h`

Las mediciones pareadas contra el termohigrómetro patrón se registran en el formato de la Tabla A1.

**Tabla A1**  
*Registro de contraste termohigrométrico de campo (SHT31 y DS18B20 frente a patrón certificado)*

| N.º Lectura | Fecha / Hora | $T_{\text{patrón}}$ ($^\circ\text{C}$) | $T_{\text{SHT31}}$ ($^\circ\text{C}$) | $\Delta T$ ($^\circ\text{C}$) | $\text{HR}_{\text{patrón}}$ ($\%$) | $\text{HR}_{\text{SHT31}}$ ($\%$) | $\Delta \text{HR}$ ($\%$) | $T_{\text{suelo, patrón}}$ ($^\circ\text{C}$) | $T_{\text{DS18B20}}$ ($^\circ\text{C}$) | Observaciones |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 01 | | | | | | | | | | |
| 02 | | | | | | | | | | |
| ... | | | | | | | | | | |

*Nota.* Formato de campo propuesto para el protocolo `E1` (contraste mínimo de $58\text{ h}$ continuas). Las celdas vacías representan mediciones físicas pendientes de ejecución en laboratorio/invernadero (`[DATO FALTANTE]`).

- **Resumen estadístico calculado:** $\text{RMSE}_T = \_\_\_\_\_\,^\circ\text{C}$ | Sesgo medio $T = \_\_\_\_\_\,^\circ\text{C}$ | $\text{RMSE}_{\text{HR}} = \_\_\_\_\_\,\%$ | Histéresis máx. $\text{HR} = \_\_\_\_\_\,\%$ | $\text{RMSE}_{T,\text{suelo}} = \_\_\_\_\_\,^\circ\text{C}$.

### Parte II. Calibración Gravimétrica del Sensor Capacitivo de Humedad de Suelo v1.2 (Estufa $105\,^\circ\text{C}$)

- **Tipo de sustrato:** `____________________` | **Densidad aparente medida ($\rho_a$):** `______ g/cm³` | **Volumen cilindro ($V_c$):** `______ cm³`
- **Temperatura de estufa:** $105\,^\circ\text{C} \pm 2\,^\circ\text{C}$ | **Tiempo de secado:** `24 h` (hasta masa constante) | **Resolución balanza:** `0.01 g`

Los pares de lectura digital (`ADC`), masa húmeda/seca y contenido volumétrico de agua se consignan en la Tabla A2.

**Tabla A2**  
*Hoja de calibración gravimétrica en estufa ($105\,^\circ\text{C}$) para el sensor capacitivo de humedad de suelo v1.2*

| Nivel hídrico | Lectura `ADC` media ($0$–$4095$) | Voltaje medido ($\text{V}$) | Tara cápsula $m_c$ ($\text{g}$) | Masa cápsula + suelo húmedo $m_{ch}$ ($\text{g}$) | Masa cápsula + suelo seco $m_{cs}$ ($\text{g}$) | Humedad gravimétrica $\theta_g = \frac{m_{ch}-m_{cs}}{m_{cs}-m_c}$ ($\text{g/g}$) | Humedad volumétrica $\text{VWC} = \theta_g \cdot \frac{\rho_a}{\rho_w}\cdot 100$ ($\%$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Nivel 1 (Seco al aire) | | | | | | | |
| Nivel 2 (Humedad baja) | | | | | | | |
| Nivel 3 (Óptimo cultivo) | | | | | | | |
| Nivel 4 (Capacidad campo) | | | | | | | |
| Nivel 5 (Saturación drenada) | | | | | | | |

*Nota.* Formato de calibración gravimétrica para el sustrato real del invernadero en La Paz (`E1`), donde $\rho_w \approx 1{,}00\text{ g/cm}^3$ denota la densidad del agua. Pendiente de ejecución física (`[DATO FALTANTE]`).

- **Ecuación de calibración ajustada en `config_invernadero.h`:** $\text{VWC}(\%) = a \cdot \text{ADC}^2 + b \cdot \text{ADC} + c$ (o lineal) | $R^2 = \_\_\_\_\_$ | $\text{RMSE}_{\text{VWC}} = \_\_\_\_\_\,\%$.

---

## Anexo C. Ficha de Validación Agronómica (*Ground Truth* Foliar y Entomológico)

**Código de inspección:** `AGR-GT-____` | **Fecha y hora:** `____-__-__ __:__` | **Evaluador agrónomo:** `____________________` | **Registro profesional:** `________`  
**Ensayo / Bloque:** `[ ] Nivel 0 (Testigo)` `[ ] Nivel 1 (IoT-PID-IA)` | **Variedad *Solanum tuberosum*:** `______________` | **Estadio fenológico:** `______________`

### Sección 1. Validación Foliar en Dosel (Cámara a $25\text{ cm}$, ángulo $70^\circ$–$80^\circ$)

El registro de diagnóstico experto foliar frente a la predicción visual se estructura en la Tabla A3.

**Tabla A3**  
*Formato de validación agronómica foliar en dosel (Ground Truth frente a detección YOLO)*

| ID Imagen / Archivo | Código Planta (`planta_XX`) | Estrato dosel (Inf/Med/Sup) | Diagnóstico experto (*Ground Truth*) | Severidad real estimada ($\%$ área foliar) | Lesión incipiente ($\le 5\,\%$) `[S/N]` | Predicción `YOLO` + Confianza | Coincidencia diagnóstica `[TP/FP/FN]` | Observaciones morfológicas (halo clorótico, anillos concéntricos) |
| :--- | :---: | :---: | :--- | :---: | :---: | :--- | :---: | :--- |
| | | | | | | | | |
| | | | | | | | | |

*Nota.* Instrumento destinado al protocolo `E5` en campo bajo criterio de especialista agrónomo titulado. Ninguna fila ha sido prellenada (`[DATO FALTANTE]`).

### Sección 2. Validación Entomológica en Trampa Cromática Amarilla (Cámara a $15\text{ cm}$, ángulo $90^\circ$)

El conteo manual experto por especie objetivo frente al algoritmo particionado por ventanas se registra en la Tabla A4.

**Tabla A4**  
*Formato de validación entomológica en trampa cromática amarilla (Ground Truth frente a YOLO + SAHI)*

| ID Imagen / Archivo | Código Trampa (`trampa_XX`) | Conteo experto *L. huidobrensis* | Conteo experto *M. persicae* | Conteo experto *P. operculella* | Total real insectos | Conteo `YOLO + SAHI` | Diferencia absoluta / Falsos negativos | Observaciones (solapamientos, luz, pegamento) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| | | | | | | | | |
| | | | | | | | | |

*Nota.* Instrumento destinado al protocolo `E6` para validación de insectos diminutos sobre trampas adhesivas ($15 \times 20\text{ cm}$). Ninguna fila ha sido prellenada (`[DATO FALTANTE]`).

**Firma del especialista agrónomo:** `___________________________` | **Firma del tesista:** `___________________________`

---

## Anexo D. Cuestionario de Usabilidad y Calidad Operacional (Basado en ISO/IEC 25010)

**Propósito:** Evaluar la calidad percibida de la plataforma web (`Django 6.1.2`), tableros analíticos (`Grafana`) y sistema de alertas (`Telegram`) por parte de operadores, estudiantes y docentes de la Universidad Salesiana de Bolivia tras la interacción con el prototipo.  
**Perfil del participante:** `[ ] Operador / Productor` `[ ] Estudiante` `[ ] Docente / Especialista Agrónomo` | **Fecha:** `____-__-__`

**Instrucciones:** Marque con una `X` su grado de acuerdo con cada afirmación utilizando la escala de Likert de 5 puntos presentada en la Tabla A5:  
`1 = Totalmente en desacuerdo` | `2 = En desacuerdo` | `3 = Ni de acuerdo ni en desacuerdo` | `4 = De acuerdo` | `5 = Totalmente de acuerdo`.

**Tabla A5**  
*Escala de evaluación de usabilidad y calidad operacional basada en `ISO/IEC 25010`*

| Código | Dimensión ISO/IEC 25010 | Ítem de evaluación | 1 | 2 | 3 | 4 | 5 |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **AF-1** | Adecuación funcional | La plataforma presenta de forma completa las variables esenciales del cultivo de papa ($T_{\text{aire}}$, $\text{HR}$, $\text{VPD}$, humedad del suelo y riesgo). | [ ] | [ ] | [ ] | [ ] | [ ] |
| **AF-2** | Adecuación funcional | Las alertas enviadas por `Telegram` incluyen información comprensible y útil para tomar decisiones agronómicas oportunas. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **AF-3** | Adecuación funcional | La distinción explícita cuando la severidad foliar no está disponible evita interpretaciones erróneas sobre el estado de la planta. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **ED-1** | Eficiencia de desempeño | Los paneles de monitoreo en tiempo real y el gemelo digital responden con fluidez sin demoras perceptibles. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **ED-2** | Eficiencia de desempeño | El tiempo de respuesta al subir una fotografía foliar o de trampa para diagnóstico es adecuado para la operación rutinaria. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **US-1** | Usabilidad | La navegación entre las vistas de resumen, control PID, visión artificial, alertas y experimentos resulta intuitiva sin capacitación extensa. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **US-2** | Usabilidad | La codificación visual por colores de riesgo (`BAJO`, `MEDIO`, `ALTO`, `CRÍTICO`) permite identificar anomalías de un vistazo. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **US-3** | Usabilidad | El ajuste manual de consignas (*setpoints*) desde la interfaz web ofrece retroalimentación clara y protege contra valores fuera de rango. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **FI-1** | Fiabilidad y trazabilidad | El historial de auditoría de cambios de *setpoint* y alarmas permite reconstruir con claridad qué ocurrió en el invernadero. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **FI-2** | Fiabilidad y trazabilidad | El sistema mantiene coherencia de datos y continuidad ante recargas o consultas simultáneas al tablero. | [ ] | [ ] | [ ] | [ ] | [ ] |
| **MA-1** | Mantenibilidad / Operabilidad | La exportación de registros en formato CSV y la visualización de protocolos `E1`–`E8` facilitan el análisis posterior. | [ ] | [ ] | [ ] | [ ] | [ ] |

*Nota.* Instrumento propuesto para la evaluación presencial al cierre del protocolo `E8` (criterio de aceptación: media $\ge 4{,}0/5{,}0$). Aplicación pendiente (`[DATO FALTANTE]`).

**Observaciones y sugerencias de mejora del participante:**  
`_________________________________________________________________________________________`  
`_________________________________________________________________________________________`

---

## Anexo E. Trazabilidad de Scripts Reproducibles y Artefactos Verificados

Con el fin de garantizar la auditabilidad integral del Capítulo III y del análisis estadístico, la Tabla A6 lista los scripts ejecutables del repositorio empleados para producir las tablas, figuras, simulaciones y verificaciones de calidad.

**Tabla A6**  
*Inventario de scripts reproducibles y artefactos verificados en el repositorio*

| Archivo / Script | Entorno de ejecución | Entradas principales | Salidas verificadas |
| :--- | :--- | :--- | :--- |
| `tesis/scripts/analisis_estadistico_tesis.py` | `.venv/bin/python` (Python 3.14, `scipy 1.18.1`, `pandas 3.0.6`) | `data/synthetic/*.csv`, `data/models/entrenados_colab/*`, `data/processed/*/report.json` | `tesis/tablas/tabla_01..04.{csv,md}` y `tesis/figuras/fig_est_*.png` ($300\text{ dpi}$). |
| `tesis/scripts/generar_diagramas_tesis.py` | `.venv/bin/python` (`matplotlib 3.11.2`, `geo_lapaz_bolivia.json`) | Especificaciones reales de `firmware/`, `docker-compose.yml`, `server/`, `web/` | `tesis/figuras/fig_flujo_modelo_v.png`, `fig_arq_sistema_real.png`, `fig_mapa_ubicacion_lapaz.png`, `fig_exp_diseno_cascada_bloques.png`. |
| `scripts/preparar_datasets_reales.py` | Python + `Pillow` + `PyYAML` | Repositorios públicos *PlantVillage* y *PlantDoc* | `data/processed/papa_plantvillage_clasificacion/`, `data/processed/papa_plantdoc_yolo/`, `report.json` (`exact_duplicate_leakage: false`). |
| `scripts/entrenar_yolo26.py` / `scripts/flujo_colab.py` | Google Colab GPU (`ultralytics 8.4.201`, `torch 2.11.0+cu130`) | Datasets curados en `data/processed/` | `data/models/entrenados_colab/*/weights/best.pt`, `best.metadata.json`, `verificacion.json`, `resumen_evaluacion_final.csv`. |
| `scripts/ejecutar_fase2_identificacion_pid.py` | `.venv/bin/python` (`scipy`, `optuna`, `matplotlib`) | `data/synthetic/prueba_escalon_fopdt.csv` | `data/synthetic/metricas_comparativa_pid_onoff.csv` y 4 figuras PID en `thesis/figuras/`. |
| `scripts/ejecutar_fase5_riesgo_fusion.py` | `.venv/bin/python` (`xgboost`, `scikit-learn`, `shap`, `torch`) | `data/synthetic/dataset_agroclimatico_invernadero.csv` | `data/synthetic/metricas_experimentos_fase5_riesgo.csv` y 4 figuras de riesgo/SHAP/fusión en `thesis/figuras/`. |
| `scripts/init_db.py` y `scripts/seed_experiments.py` | Python (`sqlite3`) | `server/app/models/schemas.sql` | `data/invernadero_relacional.db` (5 tablas operativas + protocolos semilla `E1`–`E8`). |
| Suite `pytest` + PlatformIO | `.venv/bin/pytest -q` / `pio run` | `tests/*.py`, `firmware/esp32_control/` | `117 passed` ($4{,}69\text{ s}$) y `firmware.bin` ($818.992\text{ bytes}$). |

*Nota.* Inventario verificado directamente sobre los archivos ejecutables del repositorio `/home/rodrigo/Desktop/IOTtesis`.
