# Catálogo de Figuras y Diagramas Técnicos (Formato APA 7.ª edición)

**Proyecto:** Sistema prototipo integrado de IoT, control PID e inteligencia artificial para la regulación microclimática y detección temprana de plagas en el cultivo de papa bajo invernadero  
**Institución / Ubicación:** Ingeniería de Sistemas, Universidad Salesiana de Bolivia — Zona Achachicala, La Paz, Bolivia (`16°31'20.1"S 68°07'25.6"W`; `-16.52225, -68.12378`; ~3.600–3.650 m s. n. m.)  
**Resolución estándar:** 300 dpi (PNG) para todas las figuras científicas y diagramas técnicos generados.  
**Script generador de diagramas arquitectónicos y mapa:** `tesis/scripts/generar_diagramas_tesis.py` (con datos cartográficos empaquetados en `tesis/scripts/geo_lapaz_bolivia.json`).

---

## Convención de Etiquetado de Origen y Evidencia

- **`[Arquitectura/código real]`**: Diagramas construidos estrictamente a partir de la implementación verificada en `firmware/`, `docker-compose.yml`, `server/`, `web/`, `config/` y `tests/`.
- **`[Cartografía oficial + coordenada declarada]`**: Mapa elaborado con límites administrativos reales (`geoBoundaries BOL ADM1/ADM3`, `Natural Earth 10m`) y las coordenadas geodésicas declaradas del sitio de estudio.
- **`[Piloto real Colab]`**: Figuras o muestras visuales procedentes de datasets públicos reales curados (`PlantVillage`, `PlantDoc`) y entrenamientos ejecutados en Google Colab (`2026-11-04`).
- **`[Generado de código/simulación]`**: Gráficas generadas por scripts reproducibles sobre datos simulados o valores de diseño (`data/synthetic/`, `scripts/ejecutar_fase*.py`), diferenciadas explícitamente de ensayos físicos en campo.

---

## 1. Diagramas de Arquitectura, Metodología, Ubicación y Diseño Experimental (Propios — `tesis/figuras/`)

**Figura 1**  
*Modelo de desarrollo en V adaptado a sistemas ciberfísicos (VDI/VDE 2206) para el prototipo IoT–PID–IA*  
- **Archivo fuente:** `tesis/figuras/fig_flujo_modelo_v.png` (4619 × 2307 px, 300 dpi)  
- **Script generador:** `tesis/scripts/generar_diagramas_tesis.py` (`generar_modelo_v()`)  
- **Origen:** `[Arquitectura/código real]`  
- **Nota.** Adaptación de la metodología VDI/VDE 2206 al desarrollo del sistema ciberfísico para cultivo de *Solanum tuberosum* en La Paz. El brazo descendente detalla la especificación bio-agronómica, la arquitectura jerárquica en cascada y el diseño de hardware/firmware/software/datasets; el vértice integra el firmware compilado en PlatformIO, los seis servicios Docker, el entrenamiento GPU en Colab (`YOLO26n`/`YOLO11n`) y el estado pendiente del ensamblaje físico en campo; el brazo ascendente vincula la verificación unitaria (117 pruebas Pytest aprobadas), la validación simulada del lazo FOPDT/PID y bus MQTT, y la evaluación piloto de visión junto con los protocolos experimentales E1–E8. Elaboración propia basada en los artefactos verificados del repositorio.

**Figura 2**  
*Arquitectura real del sistema integrado IoT–PID–IA en capa de borde, bus de mensajería Docker, inteligencia artificial y plataforma web*  
- **Archivo fuente:** `tesis/figuras/fig_arq_sistema_real.png` (3926 × 2446 px, 300 dpi)  
- **Script generador:** `tesis/scripts/generar_diagramas_tesis.py` (`generar_arquitectura_real()`)  
- **Origen:** `[Arquitectura/código real]`  
- **Nota.** Representación fiel de los componentes implementados en código: nodo de borde `ESP32 DevKit V1` con sensores (`SHT31` I2C `0x44`, `BH1750` I2C, `DS18B20` OneWire `GPIO4`, sensor capacitivo v1.2 `GPIO34`, interruptor flotador `GPI35`), procesamiento local a 10 Hz (filtrado Hampel + EMA, psicrometría Tetens/Magnus y control PID *split-range* con watchdog de 10 s), etapa de potencia y actuadores (calefactor 220 V vía SSR `GPIO23`, extractor 12 V vía MOSFET PWM 25 kHz `GPIO19`, humidificador `GPIO18` y bomba `GPIO26`), captura óptica (cámara USB 1080p / `ESP32-CAM`), red Docker `net_invernadero_iot` (`Eclipse Mosquitto 2.0.18` -> `Telegraf 1.30.0` -> `InfluxDB 2.7.5` -> `Grafana 10.4.1`), microservicios `FastAPI` + `Worker Supervisor` (`0,45·Clima + 0,35·Visión + 0,20·Tendencia`, `YOLO26n`/`YOLO11n` + `SAHI 0.12.8`), persistencia `SQLite WAL`, notificaciones vía `Bot de Telegram` y aplicación web `Django 6.1`. Elaboración propia a partir de `firmware/esp32_control/`, `docker-compose.yml`, `server/` y `web/`.

**Figura 3**  
*Delimitación espacial del área de estudio en la zona de Achachicala (Universidad Salesiana de Bolivia), cuenca de La Paz*  
- **Archivo fuente:** `tesis/figuras/fig_mapa_ubicacion_lapaz.png` (3879 × 2410 px, 300 dpi)  
- **Script generador:** `tesis/scripts/generar_diagramas_tesis.py` (`generar_mapa_lapaz()`)  
- **Origen:** `[Cartografía oficial + coordenada declarada]`  
- **Nota.** Mapa de encuadre doble en sistema de referencia WGS84. Panel (a): ubicación macro de Bolivia, límites departamentales con énfasis en el Departamento de La Paz, Lago Titicaca y ciudades de referencia. Panel (b): delimitación local sobre la cuenca de La Paz con límites municipales (`Nuestra Señora de La Paz`, `El Alto`, `Achocalla`, `Palca`), mancha urbana consolidada y marcador del punto experimental en `16°31'20.1"S, 68°07'25.6"W` (`-16,52225° Lat; -68,12378° Lon`), altitud referencial ~3.600–3.650 m s. n. m. y presión barométrica media ~67,5 kPa, con anillos geodésicos de 1 km y 2 km. Fuentes cartográficas: `geoBoundaries` (BOL ADM1/ADM3) y `Natural Earth 10m` (lagos y áreas urbanas). No incluye trazados viales ni linderos de parcela no levantados en campo.

**Figura 4**  
*Esquema experimental comparativo (Nivel 0 manual frente a Nivel 1 automatizado en cascada) y protocolos de validación E1–E8*  
- **Archivo fuente:** `tesis/figuras/fig_exp_diseno_cascada_bloques.png` (3810 × 2538 px, 300 dpi)  
- **Script generador:** `tesis/scripts/generar_diagramas_tesis.py` (`generar_diseno_cascada_bloques()`)  
- **Origen:** `[Arquitectura/código real]`  
- **Nota.** Contrastación estructural entre la condición testigo de lazo abierto (Nivel 0: inspección visual discontinua y accionamiento manual o On/Off con histéresis ±0,5 °C) y la arquitectura propuesta de control jerárquico en cascada (Nivel 1). El lazo externo supervisor (período 30 s en Docker) integra visión artificial (`YOLO26n`/`YOLO11n` + `SAHI`), telemetría microclimática y tendencia temporal mediante fusión multimodal ponderada para actualizar dinámicamente los setpoints (`T_sp`, `HR_sp`) vía MQTT y emitir alertas por Telegram; el lazo interno rápido (10 Hz en ESP32) ejecuta banda muerta (±0,25 °C), PID discreto con derivada sobre la medida y anti-windup, y distribución *split-range* hacia calefacción SSR y extracción PWM. El bloque inferior sintetiza los ocho protocolos experimentales (`E1`–`E8`) definidos en `scripts/seed_experiments.py`.

---

## 2. Muestra Visual de Datasets Públicos Curados (`data/processed/`)

**Figura 5**  
*Muestra visual curada de los conjuntos públicos reales de papa empleados en clasificación (PlantVillage) y detección foliar (PlantDoc)*  
- **Archivo fuente:** `data/processed/vista_previa_datasets_reales.jpg` (960 × 560 px)  
- **Script generador:** `scripts/preparar_datasets_reales.py`  
- **Origen:** `[Piloto real Colab]`  
- **Nota.** Composición de imágenes reales curadas tras deduplicación por hash exacto de píxeles y partición agrupada 70/15/15. Fila superior: ejemplares de `PlantVillage` (2.152 imágenes en 3 clases: `tizon_tardio`, `tizon_temprano` y `hoja_sana` sobre fondo uniforme de laboratorio). Fila inferior: ejemplares de `PlantDoc` (219 imágenes con 569 cajas delimitadoras de hoja completa para `tizon_tardio` y `tizon_temprano`), indicando la exclusión de la etiqueta genérica `Potato leaf` por sanidad no confirmada. Fuente primaria: repositorios públicos PlantVillage y PlantDoc.

---

## 3. Gráficos Científicos de Control, Visión y Riesgo Existentes (`thesis/figuras/`)

> **Advertencia metodológica:** Los 12 gráficos siguientes corresponden a las corridas de simulación y evaluación comparativa de Fases 2, 4 y 5 almacenadas en `thesis/figuras/`. Su naturaleza simulada o de diseño de referencia se especifica explícitamente en la nota de cada figura para evitar confundirlas con mediciones de campo o con los pesos reales entrenados en Colab el 2026-11-04.

### 3.1 Identificación Térmica FOPDT y Sintonización PID (Fase 2)

**Figura 6**  
*Identificación paramétrica de la dinámica térmica del invernadero mediante modelo de primer orden con retardo (FOPDT)*  
- **Archivo fuente:** `thesis/figuras/fig_fopdt_ajuste_escalon.png` (2700 × 1500 px, 300 dpi)  
- **Script generador:** `scripts/ejecutar_fase2_identificacion_pid.py` (sobre `data/synthetic/prueba_escalon_fopdt.csv`)  
- **Origen:** `[Generado de código/simulación]`  
- **Nota.** Ajuste por mínimos cuadrados no lineales de la respuesta térmica ante un escalón de calefacción al 70 % ($K = 0,1639\,^\circ\text{C}/\%$, $\tau = 242,96\text{ s}$, $\theta = 33,33\text{ s}$, $R^2 = 0,9990$, $\text{RMSE} = 0,1178\,^\circ\text{C}$). Curva generada a partir de datos simulados para el entorno térmico de La Paz; pendiente de reemplazo por ensayo al escalón en el prototipo físico.

**Figura 7**  
*Comparativa de respuesta dinámica en lazo cerrado y esfuerzo de control para cuatro métodos de sintonización PID*  
- **Archivo fuente:** `thesis/figuras/fig_comparativa_sintonias_pid.png` (3000 × 2100 px, 300 dpi)  
- **Script generador:** `scripts/ejecutar_fase2_identificacion_pid.py` (sobre `data/synthetic/metricas_comparativa_pid_onoff.csv`)  
- **Origen:** `[Generado de código/simulación]`  
- **Nota.** Evolución simulada de la temperatura del aire y de la acción de control $u(t)$ ante cambio de setpoint (20,0 °C) y perturbación externa (-2,5 °C en $t = 1400\text{ s}$) bajo los esquemas Ziegler-Nichols, Cohen-Coon, IMC y optimización bayesiana con Optuna TPE.

**Figura 8**  
*Comparativa de desempeño y desgaste de actuadores entre control On/Off con histéresis y control PID optimizado con Optuna*  
- **Archivo fuente:** `thesis/figuras/fig_comparativa_onoff_vs_pid.png` (3000 × 2100 px, 300 dpi)  
- **Script generador:** `scripts/ejecutar_fase2_identificacion_pid.py`  
- **Origen:** `[Generado de código/simulación]`  
- **Nota.** Contraste en simulación entre el control On/Off ($\pm 0,5\,^\circ\text{C}$, $\text{IAE} = 2566,79$, $M_p = 9,27\%$, $TV_u = 1900,0$) y el PID sintonizado con Optuna ($\text{IAE} = 1800,35$, $M_p = 1,61\%$, $TV_u = 152,87$), evidenciando una reducción del 29,9 % en el error absoluto integrado y mitigación de conmutaciones bruscas.

**Figura 9**  
*Curva de convergencia del optimizador bayesiano Optuna (TPE) en la búsqueda de ganancias PID*  
- **Archivo fuente:** `thesis/figuras/fig_optuna_convergencia.png` (2400 × 1350 px, 300 dpi)  
- **Script generador:** `scripts/ejecutar_fase2_identificacion_pid.py`  
- **Origen:** `[Generado de código/simulación]`  
- **Nota.** Evolución de la función de costo compuesta ($\text{IAE}$ más penalizaciones por sobreimpulso y variación total de control) a lo largo de las iteraciones (*trials*) de Optuna sobre el modelo FOPDT simulado.

### 3.2 Benchmark de Visión Artificial (Fase 4 — Valores de Referencia E1–E3)

**Figura 10**  
*Comparativa de precisión media (mAP@0.50 y mAP@0.50:0.95) entre arquitecturas de detección en el diseño E1*  
- **Archivo fuente:** `thesis/figuras/fig_comparativa_map_modelos.png` (2400 × 1440 px, 300 dpi)  
- **Script generador:** `scripts/ejecutar_fase4_evaluacion_vision.py` (sobre `data/synthetic/metricas_experimentos_e1_e2_e3.csv`)  
- **Origen:** `[Generado de código/simulación]`  
- **Nota.** Valores de referencia de diseño experimental E1 (`YOLO11n`, `YOLOv8n`, `Faster R-CNN ResNet-50`) previos a la ejecución piloto real en Google Colab (`YOLO26n` / `YOLO11n` sobre PlantDoc). No debe presentarse como resultado empírico de los pesos de Colab.

**Figura 11**  
*Compromiso entre latencia de inferencia en CPU (escala logarítmica) y precisión mAP@0.50 para despliegue sin GPU*  
- **Archivo fuente:** `thesis/figuras/fig_latencia_vs_map_cpu.png` (2400 × 1500 px, 300 dpi)  
- **Script generador:** `scripts/ejecutar_fase4_evaluacion_vision.py`  
- **Origen:** `[Generado de código/simulación]`  
- **Nota.** Gráfica de referencia de diseño comparando latencia CPU y mAP@0.50 frente al umbral operativo de 200 ms (5 FPS). Requiere verificación cronometrada en el servidor físico final usando los pesos `best.pt` definitivos.

**Figura 12**  
*Impacto esperado del algoritmo SAHI (mosaicos 320 × 320 px) en la sensibilidad de detección de insectos diminutos en trampas amarillas*  
- **Archivo fuente:** `thesis/figuras/fig_sahi_mejora_objetos_pequenos.png` (2550 × 1440 px, 300 dpi)  
- **Script generador:** `scripts/ejecutar_fase4_evaluacion_vision.py` (experimento de referencia E2)  
- **Origen:** `[Generado de código/simulación]`  
- **Nota.** Comparativa de diseño experimental entre inferencia estándar y `SAHI` para mosca minadora, pulgón y polilla de la papa. Los modelos actuales entrenados en Colab cubren únicamente patologías foliares; el entrenamiento y evaluación real sobre insectos en trampas amarillas permanece pendiente.

**Figura 13**  
*Matriz de confusión normalizada de seis clases de referencia para visión artificial (YOLO11n + SAHI)*  
- **Archivo fuente:** `thesis/figuras/fig_matriz_confusion_vision.png` (2250 × 1950 px, 300 dpi)  
- **Script generador:** `scripts/ejecutar_fase4_evaluacion_vision.py`  
- **Origen:** `[Generado de código/simulación]`  
- **Nota.** Matriz de confusión de referencia sobre el esquema de 6 clases (`tizon_tardio`, `tizon_temprano`, `hoja_sana`, `mosca_minadora`, `pulgon`, `polilla_papa`) correspondiente al diseño sintético/referencial E1–E2.

### 3.3 Modelado de Riesgo Fitopatológico y Fusión Multimodal (Fase 5)

**Figura 14**  
*Curvas ROC comparativas entre la línea base epidemiológica BlightManager y modelos de aprendizaje automático en conjunto test temporal*  
- **Archivo fuente:** `thesis/figuras/fig_blightmanager_vs_ml_roc.png` (2400 × 1800 px, 300 dpi)  
- **Script generador:** `scripts/ejecutar_fase5_riesgo_fusion.py` (sobre `data/synthetic/dataset_agroclimatico_invernadero.csv`)  
- **Origen:** `[Generado de código/simulación]`  
- **Nota.** Evaluación sobre las últimas 432 horas (18 días) de la serie biofísica simulada de 90 días: `XGBoost` calibrado ($\text{ROC-AUC} = 0,7123$), `Random Forest`, `Bioclimatic LSTM`, `SVM RBF` y `BlightManager`.

**Figura 15**  
*Diagrama de confiabilidad y calibración probabilística (Brier Score) para estimación de riesgo de tizón tardío*  
- **Archivo fuente:** `thesis/figuras/fig_curvas_calibracion_probabilidad.png` (2400 × 1800 px, 300 dpi)  
- **Script generador:** `scripts/ejecutar_fase5_riesgo_fusion.py`  
- **Origen:** `[Generado de código/simulación]`  
- **Nota.** Comparación entre la diagonal de calibración perfecta, `XGBoost` con calibración isotónica ($\text{Brier} = 0,1878$), `XGBoost` sin calibrar y el criterio `BlightManager` sobre la serie agroclimática simulada.

**Figura 16**  
*Importancia bioclimática global mediante valores SHAP absolutos medios en el modelo XGBoost*  
- **Archivo fuente:** `thesis/figuras/fig_shap_importancia_bioclimatica.png` (2700 × 1800 px, 300 dpi)  
- **Script generador:** `scripts/ejecutar_fase5_riesgo_fusion.py`  
- **Origen:** `[Generado de código/simulación]`  
- **Nota.** Jerarquización de las 10 variables bioclimáticas de mayor impacto en la predicción de riesgo sobre datos simulados de 90 días, encabezada por la acumulación de horas de hoja húmeda en 48 h (`lwh_suma_48h`, $|\text{SHAP}| = 1,3257$).

**Figura 17**  
*Respuesta temporal simulada del lazo supervisor externo mediante fusión multimodal y adaptación dinámica de setpoints*  
- **Archivo fuente:** `thesis/figuras/fig_simulacion_fusion_lazo_externo.png` (3600 × 3000 px, 300 dpi)  
- **Script generador:** `scripts/ejecutar_fase5_riesgo_fusion.py`  
- **Origen:** `[Generado de código/simulación]`  
- **Nota.** Evolución horaria durante 432 horas simuladas de prueba: (1) VPD y horas de hoja húmeda continua (LWH), (2) severidad foliar y conteo en trampa simulados, (3) score compuesto de fusión multimodal (`0,45·Clima + 0,35·Visión + 0,20·Tendencia`) con umbrales `0,30 / 0,55 / 0,75`, y (4) escalonamiento dinámico de los setpoints de temperatura y humedad enviados hacia el lazo interno.

---

## 4. Figuras Estadísticas y de Entrenamiento Real en `tesis/figuras/` (Complemento de Agente 5)

Para mantener la trazabilidad integral de la carpeta `tesis/figuras/`, se registran los cuatro gráficos estadísticos complementarios generados en paralelo con base en los archivos verificados del proyecto:

| Archivo en `tesis/figuras/` | Dimensiones / DPI | Temática y Fuente de Datos | Origen |
| :--- | :--- | :--- | :--- |
| `fig_est_distribucion_datasets_reales.png` | 3600 × 1560 px, 300 dpi | Distribución real por clase y partición (PlantVillage 2.152 imgs; PlantDoc 219 imgs / 569 cajas) | `[Piloto real Colab]` |
| `fig_est_curvas_colab_plantdoc.png` | 3450 × 2550 px, 300 dpi | Curvas reales de entrenamiento/validación en Google Colab (`YOLO26n` vs `YOLO11n`, `results.csv`) | `[Piloto real Colab]` |
| `fig_est_residuos_fopdt.png` | 3300 × 2460 px, 300 dpi | Diagnóstico de residuos del modelo FOPDT sobre `prueba_escalon_fopdt.csv` | `[Generado de código/simulación]` |
| `fig_est_boxplots_vpd_riesgo.png` | 3300 × 2550 px, 300 dpi | Distribución de VPD, humedad y temperatura según nivel de riesgo en `dataset_agroclimatico_invernadero.csv` | `[Generado de código/simulación]` |
