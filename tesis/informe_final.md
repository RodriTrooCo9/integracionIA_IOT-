# Informe Final de Orquestación de Tesis (Fases 1 a 5)

**Proyecto auditado:** `/home/rodrigo/Desktop/IOTtesis`  
**Título de la tesis:** *Sistema prototipo integrado de IoT, control PID e inteligencia artificial para la regulación microclimática y detección temprana de plagas en el cultivo de papa bajo invernadero*  
**Postulante:** Alvaro Rodrigo De La Barra Velasco  
**Institución:** Universidad Salesiana de Bolivia — Carrera de Ingeniería de Sistemas (La Paz, Bolivia)  
**Docente Guía:** Ing. Freddy Cosme Garnica Carrasco  
**Fecha de cierre de orquestación:** 2026-11-13  

---

## 1. Resumen de Ejecución por Fases y Entregables Generados

El equipo multiagente ejecutó las cinco fases del flujo editorial, estadístico e ingenieril bajo la regla estricta de **cero invención de datos** y trazabilidad 1:1 hacia archivos reales del repositorio y fuentes bibliográficas verificadas:

1. **Fase 1 — Auditoría integral del repositorio y conexión a NotebookLM (Agente 1 + MCP):**
   - `/home/rodrigo/Desktop/IOTtesis/tesis/00_auditoria.md`: Inventario completo de código, commits (`2026-10-16` a `2026-11-09`), firmware (`firmware.bin` de `818.992` bytes), pila Docker de 6 servicios, pilotos reales entrenados en Google Colab (`2026-11-04`), simulaciones sintéticas y discrepancias críticas frente al borrador Word antiguo (`thesis/borrador/TG-I Tesis alvaro rodrigo de la barra velasco 1.2.docx`).
   - `/home/rodrigo/Desktop/IOTtesis/tesis/registro_evidencias.md`: Matriz `EV-01` a `EV-17` vinculando cada afirmación con su archivo fuente exacto.
   - `/home/rodrigo/Desktop/IOTtesis/tesis/pendientes.md`: Registro consolidado de elementos físicos o de campo aún inexistentes (`[DATO FALTANTE]`).
   - Conexión mediante servidor MCP `gemini-notebook-mcp` al cuaderno `427f0def-ffd4-4749-879f-4978fe90bb05` (180 fuentes), recuperando los lineamientos estructurales USB 2022 y las 8 observaciones del docente guía Ing. Freddy Cosme Garnica Carrasco.

2. **Fase 2 — Investigación bibliográfica, análisis estadístico reproducible y diseño gráfico (Agentes 2, 5 y 6):**
   - `/home/rodrigo/Desktop/IOTtesis/tesis/01_fuentes.md`: Compendio de fuentes verificadas vía búsqueda web/DOI y normativa boliviana vigente (`Ley N.º 144`, `Ley N.º 300`, `NB 777` IBNORCA), corrigiendo DOIs y años erróneos presentes en el borrador inicial.
   - `/home/rodrigo/Desktop/IOTtesis/tesis/scripts/analisis_estadistico_tesis.py` y `/home/rodrigo/Desktop/IOTtesis/tesis/02_analisis_datos.md`: Ejecución estadística real sobre `.venv/bin/python` (`numpy`, `pandas`, `scipy`), generando 4 tablas APA 7 (`tesis/tablas/tabla_01..04.csv` y `.md`) y 4 figuras científicas a 300 dpi (`tesis/figuras/fig_est_*.png`) con separación estricta entre pilotos reales de Colab, simulaciones FOPDT/agroclimáticas y datos de referencia de diseño.
   - `/home/rodrigo/Desktop/IOTtesis/tesis/scripts/generar_diagramas_tesis.py` (con geometrías reales en `tesis/scripts/geo_lapaz_bolivia.json`) y `/home/rodrigo/Desktop/IOTtesis/tesis/03_figuras_diagramas.md`: Generación de 4 diagramas propios a 300 dpi (`fig_flujo_modelo_v.png`, `fig_arq_sistema_real.png`, `fig_mapa_ubicacion_lapaz.png`, `fig_exp_diseno_cascada_bloques.png`) e inventario completo de las 17 figuras verificadas en disco.

3. **Fase 3 — Redacción académica en español APA 7 (Agentes 3 y 4):**
   - `/home/rodrigo/Desktop/IOTtesis/tesis/cap1_introduccion.md`: Capítulo I (antecedentes, planteamiento y formulación del problema, Objetivo General y 5 Objetivos Específicos medibles `OE1`–`OE5`, hipótesis `H1`/`H0`, definición conceptual y operacionalización preliminar `Tabla 1`, justificación, alcances y limitaciones).
   - `/home/rodrigo/Desktop/IOTtesis/tesis/cap2_marco_teorico.md`: Capítulo II extenso de lo general a lo específico (estado del arte comparativo, bases ecofisiológicas de *Solanum tuberosum* y psicrometría en La Paz, arquitectura CPS/IoT real, control FOPDT/PID/Optuna, visión `YOLO26n`/`YOLO11n` + `SAHI` y fusión `XGBoost`/Wallin, metodologías `VDI/VDE 2206`/`CRISP-DM`/`ISO/IEC 25010`, marco legal boliviano y glosario de 25 términos clave).
   - `/home/rodrigo/Desktop/IOTtesis/tesis/cap3_diseno_metodologico.md`: Capítulo III con estructura exacta `3.1` a `3.7` (más `3.8` de síntesis sobre apartados condicionales), 4 tablas densas (`Tabla 9`–`Tabla 12`) y las 17 figuras integradas.
   - `/home/rodrigo/Desktop/IOTtesis/tesis/anexos_instrumentos.md`: Anexos `A`–`E` con protocolos `E1`–`E8`, ficha de calibración gravimétrica (`105 °C`) e higrométrica, fichas de validación agronómica foliar y entomológica (*Ground Truth*), cuestionario `ISO/IEC 25010` y trazabilidad de scripts/pruebas.

4. **Fase 4 — Revisión APA 7.ª edición y ensamblado final `.docx` (Agentes 7 y 8):**
   - `/home/rodrigo/Desktop/IOTtesis/tesis/referencias_apa7.md` y `/home/rodrigo/Desktop/IOTtesis/tesis/04_revision_apa7.md`: Biyección verificada **34/34** entre citas en el cuerpo y referencias finales (0 citas rotas, 0 referencias huérfanas), numeración secuencial unificada (`Tabla 1`–`12`, `Tabla A1`–`A6`, `Figura 1`–`17`), eliminación de 100 % de inconsistencias heredadas y confirmación exacta con código (`Django 6.1.2`, `117 pytest`, `572 h` totales en `E1`–`E8`, `24` variables en `XGBoost`).
   - `/home/rodrigo/Desktop/IOTtesis/tesis/scripts/ensamblar_tesis_docx.py` y `/home/rodrigo/Desktop/IOTtesis/tesis/Tesis_Capitulos_I_II_III_APA7.docx` (`7.542.073` bytes / `7,2 MB`): Documento Word en tamaño Carta (`612 x 792 pts`), márgenes `2,54 cm`, Times New Roman `12 pt`, interlineado doble en prosa y referencias, sangría `1,27 cm`, alineación izquierda, portada institucional, índices automáticos con números de página reales verificados en doble pasada, tablas APA 7 solo con líneas horizontales, ecuaciones nativas OMML y 17 figuras embebidas.

5. **Fase 5 — Validación visual PDF y consolidación final (Orquestador):**
   - Conversión verificada mediante `LibreOffice 26.2.6.3` a PDF (`131` páginas totales en formato Letter) e inspección visual directa mediante `pdftoppm` (`p-001.png`, `p-002.png`, `cap3-060.png`, `cap3-061.png`, `sample-063.png`, `sample-064.png`, `t9-065.png`, `ref-111.png`).
   - Distribución real verificada en PDF: Portada (p. 1), Índices preliminares (pp. 2–7), Capítulo I (pp. 8–23; 16 páginas), Capítulo II (pp. 24–59; 36 páginas), Capítulo III (pp. 60–110; 51 páginas), Referencias (pp. 111–116; 6 páginas) y Anexos (pp. 117–131; 15 páginas).

---

## 2. Decisiones Metodológicas sobre Apartados Condicionales ("si aplica") del Capítulo III

| Sección de Cap. III | Decisión | Justificación basada en la auditoría y datos reales |
| :--- | :--- | :--- |
| **`3.4.4` Población y muestra** | **Incluida** | El proyecto opera sobre tres universos empíricos definidos: (1) muestreo censal sin fuga de imágenes reales curadas (`PlantVillage`: `2.152` imágenes, 3 clases; `PlantDoc`: `219` imágenes únicas y `569` cajas de hoja completa, 2 clases, partición agrupada `70/15/15`); (2) series temporales de telemetría/simulación (`2.160 h` agroclimáticas en 90 días y `1.800 s` de escalón FOPDT a `1 Hz`); y (3) unidades experimentales vegetales y muestras de evaluación física proyectadas en La Paz (con tamaño muestral de plantas y evaluadores humanos consignado como `[DATO FALTANTE]` hasta la instalación del ensayo). |
| **`3.6` Procesamiento y análisis de datos** | **Incluida** | La ingeniería del sistema depende de un pipeline explícito de depuración y trazabilidad: filtrado en borde (`Hampel` + `EMA`), ingestión `MQTT -> Telegraf -> InfluxDB v2 + SQLite WAL`, deduplicación por hash criptográfico/perceptual (`exact_duplicate_leakage: false`), partición temporal causal `60/20/20` sin fuga de futuro y procesamiento reproducible mediante Python (`tesis/scripts/analisis_estadistico_tesis.py`). |
| **`3.7` Análisis estadístico y diseño experimental** | **Incluida** | El enfoque cuantitativo cuasiexperimental (`Nivel 0` testigo manual vs. `Nivel 1` automatizado en cascada) y las pruebas sobre datasets reales/simulados exigen verificación previa de supuestos (Shapiro-Wilk $W$, D'Agostino-Pearson $K^2$, Levene $F$, Durbin-Watson $\text{DW}$) y selección justificada de pruebas no paramétricas (`U de Mann-Whitney` con $r_{rb}$ y $|r|$ de Rosenthal; `Wilcoxon` pareado sobre épocas comunes `YOLO26n` vs. `YOLO11n`; correlación de `Spearman` $\rho$; $\alpha = 0,05$), junto con el diseño experimental en 8 bloques (`E1`–`E8`). |

---

## 3. Coherencia Técnica Reconciliada (Borrador Antiguo vs. Código Real)

1. **Arquitectura real implementada:** Se sustituyeron todas las menciones obsoletas del borrador Word (`Node-RED`, `PostgreSQL/TimescaleDB`, `DHT22/RHT03`, nebulización neumática `AirWet`, `Raspberry Pi 4/5`, `YOLOv8` y referencias geográficas a Colombia) por los componentes reales del repositorio: `ESP32 DevKit V1` (`firmware.bin` de `818.992 bytes`), sensores `SHT31` (`I2C 0x44`), `DS18B20` (`OneWire GPIO4`), `BH1750`, sensor capacitivo v1.2 (`ADC1_CH6 GPIO34`), flotador (`GPI35`), actuadores mediante `SSR 220V` (`GPIO23`), `MOSFET IRLZ44N` PWM `25 kHz` (`GPIO19`) y relés *Active-LOW* (`GPIO18`, `GPIO26` + `1N4007`), bus Docker de 6 servicios (`Eclipse Mosquitto 2.0.18`, `Telegraf 1.30.0`, `InfluxDB 2.7.5`, `Grafana 10.4.1`, `FastAPI` + `inference_worker`), plataforma web **`Django 6.1.2`** (`web/invernadero_web/settings.py`) sobre `SQLite WAL`, bot de `Telegram` y modelos `YOLO26n`/`YOLO11n` + `SAHI 0.12.8`.
2. **Alineación epistemológica de visión y fusión:** Se delimitó explícitamente que los pesos reales entrenados en Colab (`2026-11-04`) cubren patologías foliares (`tizon_tardio`, `tizon_temprano`, `hoja_sana`) y que `PlantDoc` usa cajas de hoja completa (`severidad_disponible=false`), dejando las clases entomológicas en trampa amarilla y la severidad porcentual de lesión marcadas como `[DATO FALTANTE]`. También se distinguió entre el servicio de riesgo offline (`XGBoost` calibrado + `SHAP` sobre 24 variables) y la regla de fusión ponderada en vivo del worker (`0,45*Clima + 0,35*Visión + 0,20*Tendencia`).
3. **Alineación 1:1 de Objetivos ↔ Protocolos:** Se sincronizó la relación exacta entre `OE1`–`OE5`, la matriz `Tabla 1` (Cap. I), `Tabla 12` (sección `3.5`) y `Tabla A1` (`Anexo A` / `scripts/seed_experiments.py`, total `572 h`).

---

## 4. Advertencias, Supuestos y Nota sobre Extensión del Capítulo III

1. **Extensión del Capítulo III (`51` páginas en `.docx` con APA 7 2.0 y 17 figuras):** El borrador metodológico redactado (`12.113` palabras brutas, 4 tablas densas y **17 figuras** incrustadas) rinde `51` páginas en el `.docx` ensamblado bajo interlineado doble (`2.0`) estricto de APA 7 (incluso sin figuras, el texto y las 4 tablas ocupan ~35 páginas a doble espacio). Si el tribunal o la normativa interna de la Universidad Salesiana de Bolivia exigiera ajustar físicamente el Capítulo III al rango de **15 a 30 páginas**, el script `/home/rodrigo/Desktop/IOTtesis/tesis/scripts/ensamblar_tesis_docx.py` admite `--line-spacing 360` (interlineado `1,5`) y permite trasladar las figuras de evaluación piloto/simulación (`Figura 7`–`Figura 17`) hacia un futuro Capítulo IV de Resultados o Anexos gráficos sin perder rigor.
2. **Separación de datos simulados y de diseño:** Ninguna cifra de `dataset_agroclimatico_invernadero.csv` (`2.160 h`), `prueba_escalon_fopdt.csv` (`K = 0,1639`, `tau = 242,96 s`, `theta = 33,33 s`, `R² = 0,9990`), `metricas_comparativa_pid_onoff.csv` (`Optuna IAE = 1.800,35`), `metricas_experimentos_fase5_riesgo.csv` (`XGBoost Brier = 0,1878`) o `metricas_experimentos_e1_e2_e3.csv` ha sido presentada como medición física en invernadero real; todas aparecen etiquetadas explícitamente por su origen (`[Generado de código/simulación]` vs. `[Piloto real Colab]`).
3. **Conversión matemática y Unicode:** Las ecuaciones de bloque se renderizaron en Word mediante OMML nativo (`m:oMath`) y la simbología en prosa se normalizó a Unicode, verificando `0` escapes LaTeX (`$` / `\frac`) ni sintaxis Markdown residual en las 131 páginas del PDF compilado.

---

## 5. Lista Consolidada de Datos Pendientes de Campo (`[DATO FALTANTE]`)

El manuscrito conserva intactas `58` marcas `[DATO FALTANTE]` en los archivos fuente Markdown (agrupadas en `15` categorías en `/home/rodrigo/Desktop/IOTtesis/tesis/pendientes.md`) que deberán completarse durante la etapa presencial en el invernadero de La Paz (`16°31'20.1"S 68°07'25.6"W`, horizonte restante hasta `2027-04-16`):

1. **Cronograma agronómico exacto:** Fechas reales de siembra, emergencia, tuberización y cierre experimental dentro del horizonte semestral.
2. **Caracterización física del módulo y cultivo:** Dimensiones geométricas (`largo`, `ancho`, `altura H`, volumen útil), tipo y espesor de cubierta, tipo/densidad del sustrato y variedad específica de *Solanum tuberosum* (más número definitivo de plantas y réplicas).
3. **BOM físico definitivo y evidencias fotográficas:** Marcas, modelos comerciales, potencias reales de calefactor/extractor/humidificador/bomba/SSR/cámara, precios unitarios reales en Bs./USD, comprobantes y fotografías del tablero eléctrico bajo `NB 777` y del módulo armado.
4. **Calibración metrológica de laboratorio:** Lecturas comparativas de `SHT31` y `DS18B20` frente a termohigrómetro patrón certificado (`RMSE` y sesgo real) y curva empírica de secado gravimétrico en estufa a `105 °C` (`ADC` vs. `% VWC`) para el sensor capacitivo v1.2.
5. **Ensayos físicos de control, IoT y consumo hídrico:** Curva de respuesta al escalón real en el módulo de La Paz para reidentificar `(K, tau, theta)` físicos, bitácoras continuas de disponibilidad/latencia MQTT (`D_reg`, `L_tx`) y medición volumétrica/caudalímetro de consumo hídrico (`L/m²/semana`).
6. **Dataset local de invernadero e insectos:** Capturas fotográficas locales anotadas por especialista agronómico en La Paz, máscaras o anotaciones de severidad foliar (`<= 5 %`) y dataset + pesos entrenados para insectos en trampas cromáticas amarillas (*Bemisia tabaci*, *Liriomyza huidobrensis*, *Myzus persicae*, polilla de la papa), además de la latencia `SAHI` cronometrada en el servidor físico final.
7. **Ejecución presencial de protocolos E1–E8 e instrumentos humanos:** Aplicación efectiva de las fichas del Anexo B, Anexo C (*Ground Truth* agronómico) y Anexo D (encuesta de usabilidad `ISO/IEC 25010`) con registro de validadores humanos.
