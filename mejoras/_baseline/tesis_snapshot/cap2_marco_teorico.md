# CAPÍTULO II. MARCO TEÓRICO

El presente capítulo desarrolla los fundamentos científicos, tecnológicos, matemáticos, agronómicos y normativos que sustentan el diseño, la implementación y la evaluación experimental del sistema prototipo integrado de Internet de las Cosas (IoT), control Proporcional-Integral-Derivativo (PID) e inteligencia artificial (IA) para la regulación microclimática y detección temprana de plagas en el cultivo de papa (*Solanum tuberosum*) bajo invernadero. De acuerdo con los principios de estructuración deductiva de la investigación científica (Hernández-Sampieri & Mendoza, 2018), la exposición avanza de lo general a lo específico: inicia con el análisis crítico del estado del arte y la evolución hacia la Agricultura 4.0; continúa con las bases ecofisiológicas, psicrométricas y fitopatológicas del cultivo en condiciones altoandinas; fundamenta luego la arquitectura ciberfísica IoT, la teoría de control automático en cascada y los algoritmos de visión computacional y fusión de riesgo; y culmina con las metodologías de ingeniería de sistemas, el marco legal boliviano vigente y el glosario técnico de términos clave.

---

## 2.1 Estado del arte y antecedentes investigativos

### 2.1.1 Transición paradigmática hacia la Agricultura 4.0 y sistemas ciberfísicos

La agricultura ha atravesado sucesivas revoluciones tecnológicas determinadas por el grado de mecanización, química aplicada, automatización electrónica y procesamiento digital de información. Según Liu et al. (2021) y Zambon et al. (2019), la evolución productiva puede sistematizarse desde la agricultura tradicional de tracción animal y fuerza humana (Agricultura 1.0), pasando por la mecanización motorizada y el uso intensivo de fertilizantes y plaguicidas sintéticos de la Revolución Verde (Agricultura 2.0), hasta la incorporación de sistemas de posicionamiento global, monitoreo de rendimiento y control localizado propios de la agricultura de precisión (Agricultura 3.0). A partir de la segunda década del siglo XXI, la convergencia de redes de sensores inalámbricos, dispositivos embebidos conectados mediante el paradigma IoT, computación en la nube y en el borde (*Edge Computing*), control automático en lazo cerrado y aprendizaje automático dio origen a la Agricultura 4.0, caracterizada por la toma de decisiones basada en datos continuos y la actuación ciberfísica coordinada (Ayaz et al., 2019; Liu et al., 2021).

En el ámbito de la agricultura protegida bajo invernadero, esta transformación resulta especialmente relevante para unidades productivas de pequeña y mediana escala. Zambon et al. (2019) señalan que la transferencia efectiva de la Revolución 4.0 hacia productores con restricciones de capital exige arquitecturas modulares, estándares abiertos de comunicación y componentes de bajo costo que preserven la autonomía operativa frente a fallas de conectividad externa. En consonancia con este planteamiento, Farooq et al. (2020) y Ayaz et al. (2019) destacan que los invernaderos instrumentados requieren integrar tres planos funcionales que históricamente han evolucionado por separado: la adquisición telemétrica de variables abióticas, la regulación dinámica del volumen de control mediante leyes de retroalimentación y la vigilancia fitosanitaria automatizada mediante visión computacional.

### 2.1.2 Revisión crítica de antecedentes en telemetría IoT, control climático, visión artificial y epidemiología

La literatura científica reciente evidencia avances significativos en cada uno de los componentes del problema planteado, aunque con notables fragmentaciones arquitectónicas y limitaciones de transferencia al entorno altiplánico boliviano. En el eje de telemetría IoT agrícola, Chanchí-Golondrino et al. (2022) desarrollaron un sistema IoT de bajo costo para el monitoreo continuo de variables climatológicas en cultivos urbanos, demostrando que el registro automatizado de temperatura y humedad relativa supera las brechas temporales de la inspección manual y habilita la trazabilidad histórica para análisis agronómico. No obstante, su propuesta se circunscribe a la capa de observación ambiental sin cerrar el lazo mediante controladores PID ni incorporar modelos de visión artificial. De manera complementaria, Arias Barragán et al. (2022) diseñaron un invernadero inteligente que articula sensores ambientales y herramientas de inteligencia artificial para supervisar variables de cultivo, evidenciando el potencial de la integración digital bajo cubierta, aunque sin profundizar en el modelado dinámico de la planta térmica ni en el cálculo de índices integrales de desempeño de control.

En el contexto andino específico del género *Solanum*, Aguilar Polit (2025) evaluó en Ecuador la eficiencia del crecimiento de *Solanum phureja* mediante sensórica IoT en sistemas protegidos hidropónicos y aeropónicos, logrando acelerar el desarrollo foliar y documentar un ahorro hídrico del 32,7 % respecto al cultivo convencional en suelo. Este antecedente respalda el valor agronómico de la instrumentación continua en papa bajo cubierta; sin embargo, al operar en sustrato hidropónico sin regulación térmica PID ante heladas radiativas nocturnas ni detección automatizada de fitopatógenos, sus parámetros de operación no son directamente extrapolables a módulos experimentales en suelo o sustrato sólido a 3.600 m s. n. m. en La Paz.

Respecto a la regulación automática del microclima, van Straten et al. (2011) formalizaron el invernadero como un sistema termodinámico acoplado sujeto a perturbaciones externas de radiación, temperatura y viento, demostrando la superioridad del control óptimo frente a la apertura manual empírica. En entornos latinoamericanos de altura, Pérez Rojas y Cortés (2007/2018) modelaron la dinámica térmica de un invernadero mediante ecuaciones diferenciales concentradas y aproximaciones de primer orden con tiempo muerto (FOPDT), validando estrategias de sintonización PID clásicas sobre curvas de reacción. Paralelamente, Skogestad (2003) demostró analíticamente que la reducción de procesos térmicos complejos a modelos FOPDT permite derivar reglas de sintonización de control interno (IMC/SIMC) mucho menos oscilatorias que los ajustes heurísticos tradicionales, mientras que Akiba et al. (2019) introdujeron el marco de optimización bayesiana `Optuna` basado en *Tree-structured Parzen Estimator* (TPE), el cual posibilita hallar ganancias PID óptimas bajo funciones de costo multiobjetivo que penalizan simultáneamente el error acumulado, el sobrepaso y el desgaste de los actuadores.

En el eje de visión por computadora aplicada a fitopatología, Mohanty et al. (2016) sentaron un referente fundacional al entrenar redes neuronales convolucionales (CNN) sobre el conjunto público `PlantVillage` (54.306 imágenes de hojas aisladas sobre fondo uniforme), alcanzando exactitudes superiores al 99 %. Sin embargo, Singh et al. (2020) demostraron mediante el conjunto `PlantDoc` que los clasificadores entrenados en fondos homogéneos sufren una severa caída de desempeño al enfrentarse a fotografías de campo con iluminación heterogénea, oclusiones y múltiples hojas superpuestas. Para el caso particular de la papa, Pineda Medina et al. (2023) implementaron una plataforma web en Python orientada al diagnóstico de *Alternaria solani* y *Phytophthora infestans* en *Solanum tuberosum* L., confirmando la viabilidad de desplegar inferencia fitosanitaria en interfaces web accesibles, pero manteniendo el diagnóstico visual desacoplado del lazo de regulación microclimática. Por otro lado, Amjoud y Amrouch (2023) compararon detectores de dos etapas frente a arquitecturas de una sola etapa en tiempo real, mientras que Akyon et al. (2022) formularon la técnica *Slicing Aided Hyper Inference* (SAHI) para resolver la pérdida de información espacial de objetos diminutos durante el reescalamiento de entrada en detectores modernos como la familia YOLO (Ultralytics, 2026).

Finalmente, en el eje epidemiológico y predictivo, Wallin (1962) estableció los valores acumulados de severidad en función de la temperatura y la duración de humedad relativa alta para anticipar brotes de *P. infestans*; Andrade-Piedra et al. (2005) calibraron el modelo mecanístico `LATEBLIGHT` para agroecosistemas andinos de altura; la *Agriculture and Horticulture Development Board* (AHDB, 2020) formalizó los Criterios de Hutton contemporáneos; y Wilches Ortiz et al. (2022) corroboraron estadísticamente la correlación entre humedad relativa, rocío, temperatura y severidad del tizón tardío en papa andina. La integración de estas reglas epidemiológicas con ensambles calibrados de aprendizaje automático como `XGBoost` (Chen & Guestrin, 2016) y métodos de explicabilidad basados en valores de Shapley (`SHAP`; Lundberg & Lee, 2017) permite superar el enfoque reactivo denunciado por Cruz-Trujillo et al. (2021).

**Tabla 2**  
*Análisis comparativo crítico del estado del arte frente a la arquitectura propuesta*

| Referencia | Dominio principal | Tecnología / Método central | Aporte verificado al estudio | Limitación o brecha identificada |
| :--- | :--- | :--- | :--- | :--- |
| Chanchí-Golondrino et al. (2022) | Telemetría IoT urbana | Nodos embebidos, protocolo ligero y persistencia | Valida continuidad y trazabilidad de telemetría T/HR a bajo costo | Sin lazo cerrado PID, sin visión artificial ni fusión epidemiológica |
| Arias Barragán et al. (2022) | Invernadero inteligente | Sensórica ambiental e integración con herramientas de IA | Evidencia integración conceptual IoT + IA bajo cubierta | Ausencia de identificación FOPDT y métricas integrales de control |
| Aguilar Polit (2025) | Papa protegida (*S. phureja*) | Sensórica IoT en hidroponía/aeroponía | Cuantifica mejora foliar y ahorro hídrico de 32,7 % con monitoreo | Sin control térmico PID frente a heladas ni detección de patógenos |
| van Straten et al. (2011) | Control óptimo de invernadero | Balance dinámico de calor/masa y MPC | Fundamenta modelado acoplado y perturbaciones externas | Alto costo computacional matricial para microcontroladores de borde |
| Pérez Rojas y Cortés (2007/2018); Skogestad (2003) | Control FOPDT y PID analítico | Reducción FOPDT y sintonización IMC/SIMC | Sustenta estabilidad robusta sin sobreimpulsos severos | No articula sintonización bayesiana ni supervisión fitosanitaria |
| Mohanty et al. (2016); Singh et al. (2020) | Visión fitopatológica | CNN en `PlantVillage` y detección en `PlantDoc` | Demuestra brecha entre laboratorio y campo; base de curaduría | `PlantDoc` anota hojas completas y carece de insectos/trampas |
| Pineda Medina et al. (2023) | Diagnóstico visual en papa | Plataforma web Python para *P. infestans* y *A. solani* | Referente directo de flujo web + IA en *Solanum tuberosum* | Diagnóstico reactivo aislado del microclima y del control ambiental |
| Akyon et al. (2022); Ultralytics (2026) | Detección en tiempo real | `YOLO11n`/`YOLO26n` libre de NMS + corte `SAHI` | Habilita inferencia rápida en CPU y detección de micro-objetos | Requiere adaptación y pesos propios para plagas en invernadero local |
| Andrade-Piedra et al. (2005); AHDB (2020) | Epidemiología de *P. infestans* | Modelos `LATEBLIGHT`, Wallin y Criterios de Hutton | Define ventanas críticas de infección por temperatura y HR | Modelos puramente climáticos sin verificación visual en follaje |

*Nota.* Elaboración propia con base en las fuentes verificadas del estudio. La columna de brechas justifica la arquitectura jerárquica en cascada adoptada en la tesis.

Del contraste sintetizado en la Tabla 2 se desprenden tres vacíos de investigación (*research gaps*) que fundamentan la pertinencia del presente proyecto: (1) la fragmentación operativa entre monitoreo IoT, control térmico PID y diagnóstico visual fitosanitario; (2) la escasez de arquitecturas de lazo externo supervisor que ajusten dinámicamente las consignas climáticas en cascada a partir de la fusión calibrada entre riesgo bioclimático y visión computacional sin depender de conectividad WAN; y (3) la necesidad de validar dichos subsistemas bajo restricciones térmicas y barométricas representativas del Altiplano de La Paz (~3.600 m s. n. m.).

---

## 2.2 Bases ecofisiológicas y psicrométricas del cultivo de papa (*Solanum tuberosum*) bajo invernadero altiplánico

### 2.2.1 Biología, fenología y termoperiodismo de *Solanum tuberosum*

La papa (*Solanum tuberosum* L.), perteneciente a la familia *Solanaceae*, constituye el cuarto cultivo alimentario de mayor relevancia mundial y un pilar nutricional y económico en los sistemas agroalimentarios andinos (Devaux et al., 2020). Desde el punto de vista ecofisiológico, su productividad depende estrechamente de la interacción entre radiación fotosintéticamente activa, temperatura del aire y del suelo, disponibilidad hídrica en la zona radicular y régimen higrométrico del dosel foliar (Struik, 2007).

De acuerdo con Struik (2007), el ciclo fenológico de la papa comprende cinco fases diferenciadas con sensibilidad térmica específica: (a) *brotación y emergencia*, dependiente de la temperatura edáfica para activar los brotes del tubérculo-semilla y desarrollar el sistema radicular inicial; (b) *crecimiento vegetativo y formación del dosel*, donde temperaturas diurnas templadas maximizan la expansión foliar y la intercepción lumínica; (c) *iniciación de la tuberización*, etapa hormonalmente crítica gobernada por la relación giberelinas/ácido abscísico y altamente sensible al fotoperiodo y a la temperatura nocturna; (d) *llenado o engrosamiento de tubérculos*, periodo en el que la asimilación neta de carbohidratos en las hojas se trasloca hacia los estolones subterráneos; y (e) *senescencia y maduración*.

Struik (2007) demuestra que la temperatura ejerce un control determinante sobre la partición de asimilados en *Solanum tuberosum*. Mientras las temperaturas diurnas óptimas para la fotosíntesis neta se sitúan en torno a $18\text{–}22\text{ }^\circ\text{C}$ y la temperatura nocturna favorable para la tuberización oscila entre $10\text{ y }15\text{ }^\circ\text{C}$, exposiciones sostenidas por encima de $25\text{ }^\circ\text{C}$ —y particularmente noches cálidas superiores a $20\text{ }^\circ\text{C}$— incrementan la respiración de mantenimiento, estimulan el crecimiento vegetativo excesivo en detrimento de los estolones e inhiben o retrasan severamente la formación de tubérculos. Inversamente, descensos térmicos por debajo de $2\text{–}4\text{ }^\circ\text{C}$ generan daño celular por enfriamiento y riesgo letal de congelación foliar ante heladas radiativas. En consecuencia, el diseño del lazo de control del prototipo adopta un *setpoint* diurno nominal de $20{,}0\text{ }^\circ\text{C}$ y consignas adaptativas entre $18{,}0\text{ y }20{,}0\text{ }^\circ\text{C}$ según el estado de riesgo supervisor, evitando tanto el umbral de congelación nocturna como el estrés térmico inhibidor de la tuberización.

### 2.2.2 Influencia de la altitud de La Paz (~3.600 m s. n. m.) y termodinámica del invernadero

El emplazamiento experimental en la ciudad de La Paz (~3.600 m s. n. m.) impone condiciones físicas singulares al balance energético e hídrico de un invernadero. A esa altitud, la presión barométrica atmosférica media desciende hasta aproximadamente $P_{\text{atm}} \approx 67{,}5\text{ kPa}$ (frente a $101{,}325\text{ kPa}$ al nivel del mar), lo que reduce proporcionalmente la densidad del aire ($\rho \approx 0{,}80\text{–}0{,}85\text{ kg/m}^3$) y su capacidad calorífica volumétrica ($\rho c_p$). Como consecuencia termodinámica directa, la atmósfera presenta menor inercia térmica convectiva y una menor atenuación atmosférica de la radiación solar incidente: durante las horas de insolación diurna, la carga radiativa atraviesa la cubierta y eleva rápidamente la temperatura interior por efecto invernadero; durante la noche y madrugada, el cielo despejado altoandino acelera las pérdidas por radiación infrarroja de onda larga y conducción a través de la cubierta, provocando caídas térmicas abruptas hacia valores próximos a $0\text{–}8\text{ }^\circ\text{C}$.

Siguiendo la formulación dinámica de balances de energía y masa de van Straten et al. (2011) y Pérez Rojas y Cortés (2007/2018), el volumen de aire interior del invernadero de masa $m_a = \rho V_g$ y calor específico $c_p$ obedece a la ecuación diferencial de balance térmico:

$$\rho V_g c_p \frac{dT_{\text{in}}}{dt} = Q_{\text{rad}} + Q_{\text{cal}} - Q_{\text{cub}} - Q_{\text{vent}} - \lambda E_{\text{transp}}$$

donde $Q_{\text{rad}}$ representa la ganancia solar neta absorbida, $Q_{\text{cal}}$ es el aporte térmico controlado mediante el calefactor eléctrico gobernado por relé de estado sólido (SSR), $Q_{\text{cub}} = U_c A_c (T_{\text{in}} - T_{\text{ext}})$ modela las pérdidas conductivas y convectivas a través de la cubierta de área $A_c$ y coeficiente global $U_c$, $Q_{\text{vent}} = \rho c_p q_v (T_{\text{in}} - T_{\text{ext}})$ corresponde a la evacuación de calor sensible por renovación forzada de caudal $q_v$ mediante el extractor PWM, y $\lambda E_{\text{transp}}$ denota el flujo de calor latente asociado a la transpiración del cultivo y a la evaporación del humidificador. Paralelamente, el balance de masa de vapor de agua en el aire interior vincula la tasa de transpiración foliar, el aporte del humidificador, la condensación sobre superficies frías y el intercambio convectivo hacia el exterior (van Straten et al., 2011).

### 2.2.3 Psicrometría aplicada: ecuaciones de Tetens y Magnus y Déficit de Presión de Vapor (VPD)

La regulación independiente de temperatura o humedad relativa resulta fisiológicamente insuficiente si no se evalúa su acoplamiento termodinámico mediante el Déficit de Presión de Vapor ($\text{VPD}$). La presión de vapor de saturación $e_s(T)$ expresa la presión máxima que el vapor de agua puede ejercer en equilibrio a una temperatura $T$ ($^\circ\text{C}$), calculada en el firmware embebido mediante la ecuación empírica de Tetens:

$$e_s(T) = 0{,}61078 \cdot \exp\left(\frac{17{,}27 \cdot T}{T + 237{,}3}\right) \quad [\text{kPa}]$$

A partir de la humedad relativa medida $\text{HR}$ ($\%$), la presión parcial real de vapor de agua en el aire $e_a$ y el $\text{VPD}$ se obtienen como:

$$e_a(T, \text{HR}) = e_s(T) \cdot \frac{\text{HR}}{100} \quad [\text{kPa}]$$

$$\text{VPD}(T, \text{HR}) = e_s(T) - e_a(T, \text{HR}) = e_s(T) \left(1 - \frac{\text{HR}}{100}\right) \quad [\text{kPa}]$$

De forma complementaria, la temperatura del punto de rocío ($T_d$), umbral térmico en el que el vapor interior alcanza saturación y condensa en forma de película líquida sobre las hojas de papa, se estima mediante la aproximación psicrométrica de Magnus implementada directamente en el microcontrolador:

$$\gamma(T, \text{HR}) = \frac{17{,}27 \cdot T}{237{,}7 + T} + \ln\left(\frac{\text{HR}}{100}\right), \qquad T_d = \frac{237{,}7 \cdot \gamma(T, \text{HR})}{17{,}27 - \gamma(T, \text{HR})} \quad [^\circ\text{C}]$$

El $\text{VPD}$ gobierna directamente la fuerza motriz difusiva entre la cámara subestomática saturada de la hoja y la atmósfera circundante, definiendo tres regímenes operativos para el cultivo de papa (Andrade-Piedra et al., 2005; Struik, 2007):

1. **Ventana fisiológica óptima ($0{,}8\text{ kPa} \le \text{VPD} \le 1{,}2\text{ kPa}$):** Combinada con $T_{\text{in}} \in [18; 22]\text{ }^\circ\text{C}$ y $\text{HR} \in [65; 75]\text{ \%}$, sostiene la apertura estomática, el intercambio gaseoso de $\text{CO}_2$ y el flujo transpiratorio necesario para la absorción de nutrientes minerales sin inducir deshidratación ni condensación foliar.
2. **Estrés evaporativo por atmósfera secante ($\text{VPD} > 1{,}5\text{ kPa}$):** Ocurre ante radiación solar elevada y baja humedad relativa ($\text{HR} < 50\text{ \%}$). Cuando la demanda atmosférica supera la conductancia hidráulica radicular, la planta cierra sus estomas para conservar agua, deprimiendo la tasa fotosintética y provocando estrés hídrico.
3. **Saturación higrométrica y condensación epidémica ($\text{VPD} < 0{,}4\text{ kPa}$, $\text{HR} \ge 85\text{–}90\text{ \%}$):** Durante el enfriamiento nocturno, la caída de $T_{\text{in}}$ aproxima la temperatura foliar al punto de rocío ($T_{\text{in}} - T_d \to 0$), favoreciendo la formación de agua libre sobre el follaje (horas de hoja húmeda, $\text{LWH}$) y creando el microambiente idóneo para la germinación de esporangios patógenos. La síntesis cuantitativa de estas condiciones óptimas y críticas se presenta en la Tabla 3.

**Tabla 3**  
*Rangos ecofisiológicos, psicrométricos y umbrales críticos de riesgo para el cultivo de papa bajo invernadero*

| Parámetro ambiental / edáfico | Rango óptimo diurno | Rango óptimo nocturno | Umbral crítico de estrés o riesgo | Sustento técnico-agronómico |
| :--- | :--- | :--- | :--- | :--- |
| Temperatura del aire ($T_{\text{in}}$) | $18{,}0\text{–}22{,}0\text{ }^\circ\text{C}$ | $10{,}0\text{–}15{,}0\text{ }^\circ\text{C}$ | $< 4\text{ }^\circ\text{C}$ (helada) o $> 25\text{ }^\circ\text{C}$ (inhibe tuberización) | Struik (2007); consigna base $20{,}0\text{ }^\circ\text{C}$ en firmware |
| Humedad relativa ($\text{HR}$) | $65\text{–}75\text{ \%}$ | $70\text{–}80\text{ \%}$ | $\ge 85\text{–}90\text{ \%}$ por $\ge 6\text{ h}$ (riesgo *P. infestans*) | Andrade-Piedra et al. (2005); AHDB (2020) |
| Déficit de Presión de Vapor ($\text{VPD}$) | $0{,}8\text{–}1{,}2\text{ kPa}$ | $0{,}4\text{–}0{,}8\text{ kPa}$ | $< 0{,}4\text{ kPa}$ (condensación) o $> 1{,}5\text{ kPa}$ (cierre estomático) | Ecuación de Tetens; Wilches Ortiz et al. (2022) |
| Temperatura del suelo ($T_{\text{suelo}}$) | $15{,}0\text{–}18{,}0\text{ }^\circ\text{C}$ | $12{,}0\text{–}15{,}0\text{ }^\circ\text{C}$ | $< 8\text{ }^\circ\text{C}$ (retardo radicular) o $> 22\text{ }^\circ\text{C}$ (estrés estolonar) | Struik (2007); medición `DS18B20` |
| Humedad volumétrica de sustrato ($\text{VWC}$) | $60\text{–}75\text{ \%}$ capacidad de campo | $60\text{–}75\text{ \%}$ capacidad de campo | Requiere curva gravimétrica en estufa ($105\text{ }^\circ\text{C}$) | `[DATO FALTANTE: curva gravimétrica específica]` |

*Nota.* Elaboración propia con base en Struik (2007), Andrade-Piedra et al. (2005), AHDB (2020) y parámetros de referencia configurados en `config_invernadero.h`.

### 2.2.4 Epidemiología de patógenos foliares y delimitación de plagas entomológicas

En el cultivo de *Solanum tuberosum*, dos enfermedades foliares concentran la mayor relevancia epidemiológica y cuentan además con cobertura verificada en los conjuntos públicos curados del proyecto:

1. **Tizón tardío (*Phytophthora infestans*):** Causado por un oomiceto hemibiotrófico altamente destructivo en regiones andinas, capaz de defoliar un cultivo susceptible en pocos días cuando convergen inóculo viable, tejido hospedero y condiciones ambientales húmedas (Andrade-Piedra et al., 2005; Cruz-Trujillo et al., 2021). Entre $10\text{ y }15\text{ }^\circ\text{C}$ en presencia de agua libre foliar ($\text{HR} \ge 90\text{ \%}$), los esporangios liberan zoosporas biflageladas móviles que penetran la epidermis foliar; entre $16\text{ y }24\text{ }^\circ\text{C}$, germinan directamente por tubo germinativo (Andrade-Piedra et al., 2005). Sus lesiones incipientes aparecen como manchas irregulares de aspecto hidroso verde oscuro que evolucionan a necrosis pardo-negruzca con halo clorótico y esporulación blanquecina en el envés. Tanto los valores de severidad históricos de Wallin (1962) como los Criterios de Hutton (AHDB, 2020) —dos días consecutivos con temperatura mínima $\ge 10\text{ }^\circ\text{C}$ y al menos $6\text{ h/día}$ con $\text{HR} \ge 90\text{ \%}$— y las correlaciones empíricas andinas reportadas por Wilches Ortiz et al. (2022) confirman que la duración continua de hoja húmeda constituye el predictor ambiental primario del brote.
2. **Tizón temprano (*Alternaria solani*):** Causado por un hongo necrotrófico que produce lesiones necróticas pardo-oscuras delimitadas por anillos concéntricos característicos sobre hojas maduras e inferiores, favorecidas por ciclos alternos de humedad y estrés térmico o nutricional (Pineda Medina et al., 2023; Singh et al., 2020).

En el ámbito entomológico, la agricultura protegida de papa en invernadero se ve potencialmente afectada por insectos fitófagos de tamaño milimétrico cuya captura suele monitorearse mediante trampas cromáticas adhesivas amarillas y revisión foliar: la **mosca blanca** (*Bemisia tabaci*), la **mosca minadora** (*Liriomyza huidobrensis*), el **pulgón** (*Myzus persicae*) y el complejo de **polilla de la papa** (*Phthorimaea operculella*) o gorgojo andino (*Premnotrypes* spp.) en etapas de campo. Con estricto rigor probatorio, resulta indispensable delimitar el estado real de los datos del proyecto respecto a estas plagas: mientras el esquema de backend (`vision_service.py`) y los scripts de validación de flujo (`dataset_yolo`) contemplan etiquetas nominales para las tres clases foliares (`tizon_tardio`, `tizon_temprano`, `hoja_sana`) y tres clases de insectos (`mosca_minadora`, `pulgon`, `polilla_papa`), **los pesos reales actualmente entrenados en Google Colab (`YOLO26n-cls`, `YOLO26n` y `YOLO11n`) cubren exclusivamente patologías foliares de `PlantVillage` y `PlantDoc`**, quedando la recopilación, etiquetado experto e incorporación de pesos reales de insectos en trampas amarillas y follaje local explícitamente reservada para la fase de campo `[DATO FALTANTE: dataset propio de campo e imágenes anotadas de plagas entomológicas sobre trampas amarillas]`.

---

## 2.3 Arquitectura IoT ciberfísica, instrumentación electrónica y protocolos de telemetría

### 2.3.1 Paradigma de Sistemas Ciberfísicos (CPS) y arquitectura IoT de cuatro capas

Un Sistema Ciberfísico (CPS) articula de forma estrecha procesos físicos continuos, adquisición sensorial, comunicación en red y algoritmos de cómputo en lazo cerrado, siguiendo la tríada funcional de Computación, Comunicación y Control (Ayaz et al., 2019; Liu et al., 2021). En la agricultura protegida, la arquitectura IoT se estructura en cuatro capas jerárquicas (Farooq et al., 2020): (1) *capa de percepción y actuación*, conformada por transductores ambientales/edáficos y actuadores de potencia acoplados a un nodo microcontrolador; (2) *capa de red y transporte*, encargada del enlace inalámbrico local y el enrutamiento de paquetes mediante protocolos ligeros; (3) *capa de procesamiento y persistencia*, responsable de almacenar series temporales, ejecutar modelos analíticos y calcular consignas supervisoras; y (4) *capa de aplicación y supervisión*, que expone tableros históricos, auditoría de control y alertas al usuario.

### 2.3.2 Instrumentación electrónica, filtrado digital y etapas de potencia implementadas

La arquitectura física verificada en el firmware del proyecto (`firmware/esp32_control/`) emplea un nodo microcontrolador **ESP32 DevKit V1** (30 pines, procesador dual-core Xtensa LX6 de 32 bits, Wi-Fi IEEE 802.11 b/g/n integrado y temporizador *Hardware Watchdog* `esp_task_wdt` configurado a $10\text{ s}$ para recuperación automática ante bloqueos). La selección de sensores y pines responde a criterios de inmunidad electromagnética, resolución metrológica y separación de buses digitales:

1. **Sensor termohigrométrico digital `SHT31` (bus I2C en GPIO 21 SDA y GPIO 22 SCL, dirección `0x44`):** Proporciona mediciones calibradas de fábrica de temperatura y humedad relativa del aire con comunicación digital robusta frente a ruido analógico, evitando las derivas y limitaciones de respuesta observadas en sensores elementales de menor grado.
2. **Luxómetro digital `BH1750` (bus I2C compartido en GPIO 21/22):** Cuantifica la iluminancia interior ($\text{lux}$) para registrar la radiación incidente como covariable fotosintética y perturbación térmica.
3. **Sonda térmica sumergible `DS18B20` (bus OneWire en GPIO 4 con resistencia *pull-up* de $4{,}7\text{ k}\Omega$):** Mide la temperatura del sustrato radicular con resolución programable (Analog Devices, 2019).
4. **Sensor capacitivo de humedad de suelo v1.2 (GPIO 34, `ADC1_CH6`):** Mide la permitividad dieléctrica del sustrato sin electrólisis de electrodos. Se asigna específicamente al bloque `ADC1` del ESP32 porque el bloque `ADC2` entra en conflicto hardware con el transceptor Wi-Fi activo. En el firmware, el rango crudo de 12 bits se acota entre `ADC_SUELO_AIRE_SECO = 3100` y `ADC_SUELO_AGUA_SAT = 1450`, aunque su conversión física a contenido volumétrico de agua ($\text{\% VWC}$) exige calibración gravimétrica en estufa a $105\text{ }^\circ\text{C}$ (`[DATO FALTANTE: curva gravimétrica de calibración del sustrato local]`).
5. **Interruptor de flotador de nivel hídrico (GPIO 35 con *pull-up* externo de $10\text{ k}\Omega$):** Protege contra operación en seco de la bomba de riego y el humidificador.

Para suprimir picos espurios inducidos por conmutación de cargas inductivas o red eléctrica de 220 V AC, el firmware aplica en el borde un esquema de **filtrado digital en dos etapas**: primero un **filtro de Hampel** sobre una ventana deslizante de tres muestras que reemplaza cualquier lectura cuya desviación respecto a la mediana supere $3{,}5\text{ }^\circ\text{C}$; segundo, un **filtro de promedio móvil exponencial (EMA)** definido por la ecuación en diferencias:

$$y[k] = \alpha \cdot x[k] + (1 - \alpha) \cdot y[k - 1]$$

con factor de suavizado $\alpha = 0{,}15$ para temperatura y humedad del aire y $\alpha = 0{,}10$ para temperatura del sustrato, logrando atenuar el ruido de alta frecuencia sin introducir un retardo de fase perjudicial para el lazo PID de $10\text{ Hz}$.

En la **etapa de potencia y actuación**, el nodo gobierna cuatro elementos finales con aislamiento galvánico y supresión de transitorios: (a) un **relé de estado sólido (SSR) fototriac** optoaislado ($4000\text{ V}$) en el **GPIO 23** que conmuta el calefactor de $220\text{ V AC}$ mediante modulación proporcional en ventana temporal de $2000\text{ ms}$; (b) un **MOSFET de canal N de nivel lógico `IRLZ44N`** en el **GPIO 19** excitado mediante periférico `LEDC` por hardware a frecuencia ultrasónica de $25\text{ kHz}$ (resolución de 8 bits, $0\text{–}255$) para modular la velocidad del extractor axial de $12\text{ V DC}$ sin zumbido audible; (c) un módulo relé optoacoplado en lógica *Active-LOW* (**GPIO 18**) para el humidificador; y (d) un segundo canal de relé *Active-LOW* (**GPIO 26**) con diodo volante *flyback* `1N4007` en paralelo para proteger la etapa frente a picos inductivos de la bomba de riego. La alimentación general se resuelve mediante fuente conmutada de $12\text{ V / }10\text{ A}$, conversor reductor *Buck* `LM2596` ($12\text{ V} \to 5\text{ V}$) y fusibles de protección de $5\text{ A}$ y $8\text{ A}$. El detalle integral de pines, señales y protecciones implementadas en el nodo se consolida en la Tabla 4.

**Tabla 4**  
*Especificación electrónica verificada de sensores, actuadores y asignación GPIO en el ESP32 DevKit V1*

| Pin / Bus | Dispositivo / Función | Tipo de señal | Parámetro técnico / Protección |
| :--- | :--- | :--- | :--- |
| GPIO 21 / 22 | Bus I2C (`SHT31` `0x44` + `BH1750`) | Digital bidireccional $3{,}3\text{ V}$ | Resistencias *pull-up* $4{,}7\text{ k}\Omega$; filtrado Hampel + EMA ($\alpha = 0{,}15$) |
| GPIO 4 | `DS18B20` (temperatura de suelo) | Digital OneWire $3{,}3\text{ V}$ | *Pull-up* $4{,}7\text{ k}\Omega$; filtrado EMA ($\alpha = 0{,}10$) |
| GPIO 34 | Sensor capacitivo humedad suelo v1.2 | Analógica `ADC1_CH6` (12 bits) | Inmune a radio Wi-Fi; requiere curva gravimétrica `% VWC` |
| GPIO 35 | Interruptor de flotador (nivel de agua) | Entrada digital GPI $3{,}3\text{ V}$ | *Pull-up* externo $10\text{ k}\Omega$; bloqueo de marcha en seco |
| GPIO 23 | Calefactor $220\text{ V AC}$ vía SSR | Salida digital $3{,}3\text{ V}$ | SSR optoaislado $4000\text{ V}$; modulación en ventana de $2000\text{ ms}$ |
| GPIO 19 | Extractor axial $12\text{ V DC}$ vía `IRLZ44N` | PWM `LEDC` $25\text{ kHz}$ (8 bits) | Frecuencia ultrasónica sin zumbido; control *split-range* ($CV < 0$) |
| GPIO 18 / 26 | Humidificador y bomba de riego | Salida digital *Active-LOW* | Módulos relé optoacoplados; diodo *flyback* `1N4007` en bomba |
| GPIO 2 | LED de estado y diagnóstico (*heartbeat*) | Salida digital integrada | Señalización de estado operativo, enlace Wi-Fi/MQTT y fallo |

*Nota.* Datos verificados directamente en `firmware/esp32_control/include/config_invernadero.h`, `src/main.cpp` y `diagramas/circuito_esp32_invernadero.json`.

### 2.3.3 Protocolo MQTT, microservicios en contenedores y persistencia híbrida

Para transportar la telemetría entre el nodo embebido y el servidor local con mínima sobrecarga de protocolo y desacoplamiento asíncrono, el sistema adopta el estándar **MQTT v3.1.1** (OASIS, 2014) sobre TCP/IP en red de área local (LAN). A diferencia del paradigma síncrono petición-respuesta de HTTP/REST —cuyas cabeceras textuales incrementan la latencia y acoplan rígidamente al emisor con el receptor—, MQTT opera bajo un patrón de publicación/suscripción mediado por un *broker* central, con cabecera fija mínima de $2\text{ bytes}$ y niveles configurables de Calidad de Servicio: `QoS 0` (máximo esfuerzo) para tramas continuas de alta frecuencia y `QoS 1` (entrega garantizada al menos una vez mediante `PUBACK`) para eventos críticos, comandos de consigna e índices de riesgo (Farooq et al., 2020; OASIS, 2014).

En contraste con arquitecturas heredadas basadas en flujos visuales monolíticos o bases únicas, la infraestructura de servidor verificada en `docker-compose.yml` orquesta **seis servicios en contenedores aislados** dentro de la red interna `red_invernadero` (Tabla 5), complementados por la plataforma web de supervisión:

- **Broker `Eclipse Mosquitto 2.0.18`:** Gestiona los puertos `1883` (TCP) y `9001` (WebSockets) con autenticación obligatoria (`allow_anonymous false`) y archivo de credenciales cifradas mediante `PBKDF2-SHA512`, estructurando tópicos jerárquicos (`invernadero/telemetria/microclima`, `invernadero/telemetria/pid`, `invernadero/control/setpoints`, `invernadero/vision/detecciones`, `invernadero/riesgo/indice` e `invernadero/alarmas/eventos`).
- **Colector `Telegraf 1.30.0-alpine` y base de series temporales `InfluxDB 2.7.5-alpine`:** `Telegraf` consume las tramas JSON publicadas a $1\text{ Hz}$ y las ingiere directamente en el *bucket* `invernadero_data` de `InfluxDB v2`, motor optimizado para indexación temporal, compresión de series continuas y agregaciones por ventanas móviles.
- **Analítica visual `Grafana 10.4.1`:** Se conecta declarativamente a `InfluxDB v2` mediante consultas *Flux* para la inspección de series históricas de $T_{\text{aire}}$, $\text{HR}$, $\text{VPD}$, $T_d$, error y señales de control PID.
- **Backend `FastAPI` + `Uvicorn` y trabajador supervisor `inference_worker`:** Exponen siete *endpoints* REST (`/health`, `/vision/modelos`, `/vision/inferir`, `/control/setpoints`, `/vision/historial`, `/alertas`, `/telegram/notificar`), ejecutan la inferencia visual bajo demanda en CPU y corren el lazo asíncrono supervisor de fusión multimodal (intervalo nominal de $30\text{ s}$; ciclo operativo cada $15\text{ s}$ en código), despachando alertas instantáneas mediante la API de **Telegram Bot** (`httpx`).
- **Plataforma web `Django 6.1.2` y persistencia relacional `SQLite WAL`:** La aplicación web en `Django 6.1.2` (`web/invernadero_web/settings.py`) ofrece interfaces operativas para operadores y un gemelo digital interactivo sobre la base relacional `SQLite` en modo *Write-Ahead Logging* (WAL), garantizando lecturas concurrentes no bloqueantes sobre cinco tablas auditables (`nodos_sensores`, `detecciones_vision`, `eventos_alarmas`, `auditoria_control_pid` y `experimentos_ensayos`). Esta dualidad **InfluxDB v2 (series temporales) + SQLite WAL (eventos, auditoría y ensayos)** evita degradar las transacciones relacionales con millones de lecturas de $1\text{ Hz}$ y mantiene el sistema íntegramente ejecutable en una computadora local sin conexión a Internet.

**Tabla 5**  
*Comparativa de protocolos de mensajería y arquitectura híbrida de servicios implementada*

| Capa / Componente | Tecnología seleccionada | Alternativa descartada | Justificación técnica en el prototipo |
| :--- | :--- | :--- | :--- |
| Mensajería M2M en campo | `MQTT v3.1.1` (`Mosquitto 2.0.18`, `QoS 0/1`, `PBKDF2-SHA512`) | `HTTP/REST` continuo desde el ESP32 | Cabecera mínima ($2\text{ bytes}$), sesión TCP persistente, baja latencia y desacoplamiento nodo-servidor (OASIS, 2014) |
| Persistencia de telemetría $1\text{ Hz}$ | `Telegraf 1.30.0` $\to$ `InfluxDB 2.7.5` | Tablas relacionales únicas para series crudas | Compresión temporal nativa, retención configurable y consultas *Flux* de baja latencia |
| Persistencia relacional y auditoría | `SQLite` en modo `WAL` (`aiosqlite` + ORM `Django 6.1.2`) | Motores cliente-servidor pesados en nodo local | Cero sobrecarga administrativa, concurrencia lectura/escritura segura y trazabilidad de ensayos `E1`–`E8` |
| API y supervisión web | `FastAPI` + `inference_worker` + `Django 6.1.2` + `Grafana 10.4.1` | Flujos monolíticos acoplados a la nube | Separación limpia entre inferencia de IA, analítica temporal, tablero operativo y alertas `Telegram` |

*Nota.* Elaboración propia a partir de la configuración verificada en `docker-compose.yml`, `config/` y `web/invernadero_web/settings.py`.

---

## 2.4 Teoría de control automático en invernaderos: modelado FOPDT, PID discreto en cascada y optimización Bayesiana

### 2.4.1 Análisis crítico de paradigmas de control: On/Off, PID clásico, IMC y MPC

La selección de la estrategia de control climático en un invernadero a escala exige ponderar desempeño dinámico, robustez ante incertidumbre paramétrica, desgaste electromecánico de actuadores y viabilidad computacional en hardware embebido. En el extremo más simple, el **control todo-nada (On/Off) con histéresis** conmuta los actuadores entre $0\text{ \%}$ y $100\text{ \%}$ cuando la variable medida rebasa una banda en torno a la consigna. Aunque su implementación es trivial, en sistemas térmicos con retardo de transporte genera **ciclos límite sostenidos**, elevados sobreimpulsos térmicos, error estacionario medio no nulo y una variación total de control ($TV_u$) extrema que acelera la fatiga de relés y ventiladores (Pérez Rojas & Cortés, 2007/2018; Skogestad, 2003).

En el extremo opuesto, el **Control Predictivo Basado en Modelos (MPC)** optimiza trayectorias futuras sobre un horizonte finito utilizando modelos multivariables acoplados (van Straten et al., 2011). Si bien el MPC ofrece un aprovechamiento energético superior en invernaderos industriales de gran escala dotados de pronósticos meteorológicos locales, requiere resolver problemas de optimización restringida en cada intervalo de muestreo y mantener modelos matriciales sensibles a variaciones estructurales del cultivo o cubierta.

Frente a ambos extremos, el **controlador Proporcional-Integral-Derivativo (PID)** en lazo cerrado constituye la solución de compromiso óptima para sistemas embebidos de tiempo real: anula asintóticamente el error en estado estacionario ante perturbaciones de escalón, atenúa la oscilación mediante amortiguamiento derivativo, admite reglas analíticas transparentes de sintonización sobre modelos reducidos (Skogestad, 2003) y se ejecuta con carga computacional despreciable a $10\text{ Hz}$ dentro del `ESP32 DevKit V1`.

### 2.4.2 Modelado térmico de Primer Orden más Tiempo Muerto (FOPDT) e identificación paramétrica

A pesar de la naturaleza distribuida y no lineal de la transferencia de calor en un invernadero, su dinámica dominante en torno a un punto de operación térmico puede representarse con elevada exactitud mediante una función de transferencia lineal de **Primer Orden más Tiempo Muerto (FOPDT)** (Pérez Rojas & Cortés, 2007/2018; Skogestad, 2003):

$$G_p(s) = \frac{\Delta T_{\text{in}}(s)}{\Delta U(s)} = \frac{K \cdot e^{-\theta s}}{\tau s + 1}$$

donde $K$ ($^\circ\text{C}/\%$) es la ganancia estática de la planta (incremento térmico estacionario por unidad porcentual de actuación), $\tau$ ($\text{s}$) representa la constante de tiempo dominante asociada a la capacitancia térmica del recinto y $\theta$ ($\text{s}$) denota el tiempo muerto efectivo o retardo puro entre la aplicación de potencia en el actuador y la detección del cambio en el sensor `SHT31`. Ante una entrada en escalón de amplitud $\Delta u$ aplicada en el instante $t_0$ desde una temperatura de equilibrio $T_0$, la respuesta temporal analítica viene dada por:

$$T(t) = T_0 + K \cdot \Delta u \cdot \left[1 - \exp\left(-\frac{t - t_0 - \theta}{\tau}\right)\right] \cdot H(t - t_0 - \theta)$$

siendo $H(\cdot)$ la función escalón unitario de Heaviside. Para estimar la terna $(K, \tau, \theta)$, se combina una inicialización geométrica mediante el método de dos puntos de Smith ($28{,}3\text{ \%}$ y $63{,}2\text{ \%}$ del cambio estacionario) con un refinamiento por **mínimos cuadrados no lineales** (`scipy.optimize.curve_fit`). En el entorno de simulación biofísica del proyecto correspondiente a un escalón del $70\text{ \%}$ bajo condición nocturna de La Paz ($T_0 \approx 8{,}5\text{ }^\circ\text{C}$), se identificaron los parámetros de referencia $K = 0{,}1639\text{ }^\circ\text{C}/\%$, $\tau = 242{,}96\text{ s}$ ($4{,}05\text{ min}$) y $\theta = 33{,}33\text{ s}$ (razón de incontrolabilidad $\theta/\tau = 0{,}137$, proceso dominado por capacitancia térmica y plenamente gobernable por PID), con $R^2 = 0{,}9990$ y $\text{RMSE} = 0{,}1178\text{ }^\circ\text{C}$. Estos valores constituyen la línea base teórica del gemelo digital y deberán reidentificarse empíricamente sobre la curva física del módulo construido (`[DATO FALTANTE: ensayo físico de respuesta al escalón del invernadero real]`).

### 2.4.3 Sintonización clásica, IMC-Skogestad y optimización bayesiana con Optuna (TPE)

A partir de la planta FOPDT identificada, existen métodos heurísticos clásicos —como **Ziegler-Nichols** (basado en razón de amortiguamiento de un cuarto) y **Cohen-Coon**— y métodos analíticos modernos como el **Control por Modelo Interno (IMC / SIMC)** formulado por Skogestad (2003). Como advierte Skogestad (2003), las sintonizaciones clásicas de Ziegler-Nichols y Cohen-Coon tienden a producir ganancias proporcionales elevadas y tiempos derivativos agresivos, lo que amplifica el ruido sensorial e incrementa la variación total de control ($TV_u$). En contraste, las reglas IMC introducen un parámetro de filtro de lazo cerrado $\lambda$ (o constante deseada $\tau_c$) que permite modular explícitamente el compromiso entre velocidad de rechazo de perturbaciones y suavidad de actuación.

Para superar las limitaciones de los métodos analíticos de criterio único y ajustar simultáneamente desempeño transitorio, precisión estacionaria y protección física de los actuadores, el proyecto incorpora la **optimización bayesiana de hiperparámetros mediante `Optuna`** utilizando el estimador secuencial basado en árboles de Parzen (*Tree-structured Parzen Estimator*, TPE) (Akiba et al., 2019). En cada ensayo (*trial*), `Optuna` propone una terna candidata $(K_p, K_i, K_d)$ y evalúa por simulación temporal en lazo cerrado una función de costo multiobjetivo que minimiza la Integral del Error Absoluto ($\text{IAE}$), penaliza cuadráticamente cualquier sobrepaso superior al $5\text{ \%}$ y modera el esfuerzo de conmutación ($TV_u$):

$$J(K_p, K_i, K_d) = \text{IAE} + 50{,}0 \cdot \left[\max(0,\; M_p - 5{,}0)\right]^2 + 0{,}01 \cdot TV_u$$

donde $\text{IAE} = \sum |e[k]|\,\Delta t$ y $TV_u = \sum |u[k] - u[k-1]|$. Frente a las reglas clásicas y al control On/Off, este enfoque multiobjetivo evita soluciones de ganancia excesiva y permite evaluar cuantitativamente las métricas transitorias de tiempo de subida ($t_r$), tiempo de asentamiento ($t_s$), sobrepaso ($M_p$), error en estado estacionario ($e_{ss}$) e índices integrales ($\text{IAE}$, $\text{ITAE}$), cuyas diferencias teóricas y matemáticas se contrastan en la Tabla 6.

**Tabla 6**  
*Comparativa teórica y matemática de reglas de sintonización PID y control On/Off sobre modelo FOPDT*

| Estrategia de control | Criterio de diseño | Fórmulas / Mecanismo base | Ventaja principal | Limitación o compromiso |
| :--- | :--- | :--- | :--- | :--- |
| On/Off con histéresis | Conmutación por banda ($\pm 0{,}5\text{ }^\circ\text{C}$) | $u \in \{0\text{ \%}, 100\text{ \%}\}$ según cruce de umbral | Simplicidad lógica sin sintonización | Ciclos límite permanentes, elevado $M_p$, $e_{ss} \ne 0$ y desgaste máximo ($TV_u$) |
| Ziegler-Nichols (lazo abierto) | Amortiguamiento $1/4$ | $K_p = \frac{1{,}2\tau}{K\theta},\; T_i = 2\theta,\; T_d = 0{,}5\theta$ | Rechazo rápido a perturbaciones | Ganancias muy elevadas ($K_p, K_d$); alto esfuerzo de actuación |
| Cohen-Coon | Compensación de razón $\theta/\tau$ | Ajuste polinómico de $K_p, T_i, T_d$ en función de $R = \theta/\tau$ | Sobrepaso acotado en retardos moderados | Sensibilidad a ruido y alta acción derivativa en implementación discreta |
| IMC / SIMC (Skogestad, 2003) | Polo deseado en lazo cerrado ($\lambda$) | $K_p = \frac{\tau + 0{,}5\theta}{K(\lambda + 0{,}5\theta)},\; T_i = \tau + 0{,}5\theta$ | Respuesta suave sin sobreimpulso y alta robustez | Respuesta más lenta ($t_s$ mayor) ante cambios de consigna |
| Optuna TPE (Akiba et al., 2019) | Minimización bayesiana multiobjetivo | $\min J = \text{IAE} + 50[\max(0, M_p-5)]^2 + 0{,}01\,TV_u$ | Equilibrio verificable entre rapidez ($\text{IAE}$), $M_p \le 5\text{ \%}$ y bajo $TV_u$ | Requiere modelo FOPDT identificado o ensayos de validación en planta |

*Nota.* Fórmulas y función de costo verificadas en `scripts/ejecutar_fase2_identificacion_pid.py` y sustentadas en Skogestad (2003) y Akiba et al. (2019).

### 2.4.4 Ley PID discreta implementada, actuación *split-range* y arquitectura en cascada

En la implementación real del microcontrolador (`firmware/esp32_control/src/main.cpp`), el lazo interno ejecuta la ley de control discreta con periodo de muestreo fijo $\Delta t = 0{,}1\text{ s}$ ($10\text{ Hz}$), incorporando cuatro mecanismos de ingeniería indispensables para estabilidad en planta física:

1. **Banda muerta (*deadband*) de reposo ($\pm 0{,}25\text{ }^\circ\text{C}$):** Si $|SP - PV[k]| < 0{,}25\text{ }^\circ\text{C}$, el error efectivo se fija en $e[k] = 0$, suprimiendo conmutaciones innecesarias del SSR y del extractor ante ruido residual del sensor `SHT31`.
2. **Derivada sobre la variable medida (*anti-derivative kick*):** Para evitar impulsos bruscos en la salida cuando el lazo supervisor modifica el *setpoint*, el término derivativo diferencia únicamente la temperatura filtrada ($PV$) en lugar del error:
   $$D[k] = -K_d \cdot \frac{PV[k] - PV[k - 1]}{\Delta t}$$
3. **Integración condicional (*clamping anti-windup*):** Cuando la variable de control saturada alcanza los límites físicos ($CV \ge +100\text{ \%}$ o $CV \le -100\text{ \%}$) y el signo del error continúa empujando hacia la saturación, se congela la acumulación del término integral $I[k] = I[k-1] + K_i e[k]\Delta t$ y se acota al intervalo $[-100, +100]$, previniendo sobreimpulsos prolongados al recuperarse de una perturbación severa.
4. **Divisor de rango partido (*split-range*) en $[-100\text{ \%}, +100\text{ \%}]$:** La señal neta saturada $CV[k] = \text{sat}_{-100}^{100}(P[k] + I[k] + D[k])$ gobierna de manera mutuamente excluyente la calefacción y la extracción térmica:
   - Si $CV[k] > 0$: modo calefacción, donde el calefactor de $220\text{ V}$ modula su ciclo activo dentro de la ventana de $2000\text{ ms}$ del `SSR` con porcentaje $CV[k]$, permaneciendo el extractor apagado ($0\text{ \%}$).
   - Si $CV[k] < 0$: modo enfriamiento/deshumidificación, donde el extractor de $12\text{ V}$ opera con ciclo de trabajo PWM $|CV[k]|$ a $25\text{ kHz}$, permaneciendo el calefactor apagado.

Finalmente, la relación entre el firmware del ESP32 y el servicio `inference_worker` configura una **estructura jerárquica en cascada de dos niveles**: el lazo interno rápido ($10\text{ Hz}$) rechaza perturbaciones térmicas locales de forma autónoma (incluso sin red), mientras el lazo externo supervisor ($1/30\text{ Hz}$) evalúa el riesgo fitopatológico multimodal y publica nuevas consignas $(SP_T, SP_{\text{HR}})$ en MQTT cuando el riesgo asciende a nivel `ALTO` o `CRÍTICO` (p. ej., elevando $SP_T$ a $19{,}5\text{–}20{,}0\text{ }^\circ\text{C}$ y reduciendo $SP_{\text{HR}}$ a $60\text{–}65\text{ \%}$ para inhibir condensación nocturna).

---

## 2.5 Inteligencia artificial aplicada a sanidad vegetal y fusión bioclimática multimodal

### 2.5.1 Evolución de la visión artificial agrícola: de CNN clásicas a detectores YOLO11n y YOLO26n

El diagnóstico visual automatizado de enfermedades e insectos en cultivos ha transitado desde tuberías basadas en descriptores manuales de color/textura hacia redes neuronales convolucionales profundas (CNN) capaces de aprender jerarquías espaciales directamente de los tensores RGB (Amjoud & Amrouch, 2023; Mohanty et al., 2016). Sin embargo, en aplicaciones fitosanitarias reales resulta necesario distinguir entre **clasificación global** —que asigna una única etiqueta a toda la fotografía de una hoja aislada— y **detección de objetos**, que localiza simultáneamente múltiples instancias mediante cajas delimitadoras (*bounding boxes*) $[x_1, y_1, x_2, y_2]$ y sus probabilidades de clase sobre fondos complejos (Amjoud & Amrouch, 2023; Padilla et al., 2020).

Dentro de los algoritmos de detección de una sola etapa (*one-stage*), la familia **YOLO** (*You Only Look Once*) destaca por su compromiso favorable entre precisión y latencia en procesadores sin aceleración GPU dedicada (Amjoud & Amrouch, 2023; Ultralytics, 2026). El proyecto evalúa y contrasta específicamente las variantes compactas **`YOLO11n`** y **`YOLO26n`** documentadas por Ultralytics (2026):

- **`YOLO11n`:** Incorpora bloques convolucionales optimizados y módulos de atención espacial (`C2PSA`) sobre una cabeza desacoplada que aún depende de *Distribution Focal Loss* (DFL) y de un posprocesamiento heurístico de Supresión de No Máximos (NMS) para filtrar cajas solapadas.
- **`YOLO26n` y `YOLO26n-cls`:** Arquitectura de generación reciente orientada a despliegue en el borde (*edge*), diseñada mediante la eliminación del módulo DFL —simplificando la regresión de coordenadas y facilitando la cuantización y exportación a `ONNX Runtime` en CPU—, predicción directa extremo a extremo libre de NMS (*NMS-free*), función de pérdida progresiva (`ProgLoss`) y asignación de etiquetas consciente de la escala (`STAL`) para mejorar la sensibilidad sobre objetos de pocos píxeles, además del optimizador híbrido `MuSGD` (Ultralytics, 2026).

La comparación empírica en Google Colab GPU sobre la partición de validación de `PlantDoc` fundamentó objetivamente la selección de `YOLO26n` frente a `YOLO11n` en el módulo `vision_service.py`, manteniéndose el soporte dual tanto para detección (`detect`) como para clasificación foliar (`classify`) con verificación estricta de integridad criptográfica `SHA-256` entre los pesos `best.pt` y su archivo `.metadata.json`.

### 2.5.2 Inferencia particionada SAHI para objetos pequeños y semántica de cajas

Un cuello de botella físico bien documentado en detectores YOLO estándar ocurre cuando imágenes de alta resolución se reescalan a tensores de entrada fijos (p. ej., $640 \times 640\text{ px}$): lesiones necróticas incipientes ($\le 5\text{ \%}$ del área foliar) o insectos milimétricos en trampas amarillas pierden resolución espacial tras el submuestreo convolucional, generando falsos negativos sistemáticos. Para mitigar este fenómeno sin incrementar el costo de entrenamiento, Akyon et al. (2022) propusieron **SAHI** (*Slicing Aided Hyper Inference*). Durante la inferencia, SAHI divide la escena en ventanas superpuestas (*slices*) de tamaño reducido, ejecuta el detector sobre cada recorte a resolución nativa y recombina las predicciones en el sistema de coordenadas global mediante supresión basada en Intersección sobre Área menor (IoA) o NMS inter-parche.

En la implementación real de `server/app/services/vision_service.py`, `SAHI` se configura con ventanas de **$320 \times 320\text{ píxeles}$** y razón de solapamiento de **$0{,}20$ ($20\text{ \%}$)** tanto horizontal como verticalmente, activándose automáticamente para imágenes de `TRAMPA_AMARILLA` o bajo solicitud explícita en `HOJA_FOLLAJE`. Adicionalmente, el servicio implementa una salvaguarda epistemológica crítica denominada **semántica explícita de cajas (`box_semantics`)**: cuando un modelo fue entrenado con cajas que rodean hojas completas (`whole_leaf`, como ocurre en `PlantDoc`; Singh et al., 2020), el sistema bloquea el cálculo de porcentaje de severidad de lesión (`severidad_disponible = false`), evitando reportar falsamente el área de la hoja como área necrosada hasta disponer de anotaciones reales a nivel de lesión (`box_semantics = 'lesion'`).

### 2.5.3 Rigor en conjuntos de datos agrícolas: fuga por duplicados, desbalance y métricas de detección

La validez estadística de un modelo de visión agrícola depende de prevenir tres sesgos metodológicos recurrentes:

1. **Fuga de datos (*data leakage*) por imágenes casi idénticas:** Los repositorios públicos suelen contener variantes aumentadas o duplicados exactos que, bajo particiones aleatorias simples, se distribuyen simultáneamente entre entrenamiento y prueba, inflando artificialmente las métricas. Por ello, la curaduría del proyecto aplica **deduplicación por hash de píxeles y partición agrupada estratificada (`70/15/15`)**, verificando explícitamente la ausencia de fuga (`exact_duplicate_leakage: false`) tanto en `PlantVillage` ($2.152$ imágenes únicas) como en `PlantDoc` ($219$ imágenes únicas, $569$ cajas).
2. **Desbalance severo de clases:** En conjuntos fitopatológicos, las muestras enfermas suelen superar ampliamente a las sanas (p. ej., razón de `6,579:1` entre clases enfermas y `hoja_sana` en `PlantVillage`), lo que exige evaluar métricas sensibles a clases minoritarias y no solo exactitud global.
3. **Métricas geométricas de detección (Padilla et al., 2020):** El solapamiento espacial entre caja predicha $B_{\text{pred}}$ y verdad de campo $B_{\text{gt}}$ se mide mediante la Intersección sobre Unión ($\text{IoU}$):

$$\text{IoU}(B_{\text{pred}}, B_{\text{gt}}) = \frac{\text{Área}(B_{\text{pred}} \cap B_{\text{gt}})}{\text{Área}(B_{\text{pred}} \cup B_{\text{gt}})}$$

A partir de un umbral mínimo $\text{IoU} \ge 0{,}50$ se computan verdaderos positivos ($TP$), falsos positivos ($FP$) y falsos negativos ($FN$), derivándose la Precisión ($P$), la Sensibilidad o *Recall* ($R$), la puntuación armónica $\text{F1-Score}$ y la Precisión Media Promedio ($\text{mAP@0.50}$ y $\text{mAP@0.50:0.95}$):

$$P = \frac{TP}{TP + FP}, \qquad R = \frac{TP}{TP + FN}, \qquad \text{F1} = \frac{2 \cdot P \cdot R}{P + R}, \qquad \text{mAP} = \frac{1}{K} \sum_{i=1}^{K} \int_{0}^{1} P_i(R)\,dR$$

Desde la perspectiva agronómica, maximizar el *Recall* resulta prioritario para impedir que un foco inicial de *P. infestans* pase inadvertido, mientras una Precisión equilibrada evita la fatiga de falsas alarmas al operador.

### 2.5.4 Modelos epidemiológicos, aprendizaje automático calibrado (XGBoost + SHAP) y fusión multimodal

Para anticipar el riesgo de tizón tardío antes de la aparición de síntomas visibles, el proyecto contrasta modelos epidemiológicos basados en reglas frente a algoritmos de aprendizaje automático supervisado sobre series bioclimáticas:

- **Línea base epidemiológica (`Wallin, 1962` / `BlightManager` / `Hutton Criteria`):** Los modelos clásicos acumulan unidades de severidad (*blight units*) a partir de temperatura y duración continua de humedad relativa alta ($\text{HR} \ge 90\text{ \%}$, $\text{LWH}$) (AHDB, 2020; Andrade-Piedra et al., 2005; Wallin, 1962). En los experimentos computacionales de la Fase 5, `BlightManagerBaseline` adapta estas unidades acumuladas de 7 días mediante una transformación sigmoide centrada en $18$ puntos ($P = [1 + \exp(-(BU_{7\text{d}} - 18)/3{,}5)]^{-1}$), aclarando metodológicamente que dicha sigmoide constituye una parametrización propia inspirada en Wallin y no una equivalencia literal con los Criterios de Hutton británicos.
- **Modelos tabulares y secuenciales calibrados:** Cuando se excluye la variable determinística `blight_units_7d` y se entrena exclusivamente sobre variables de telemetría bruta y ventanas móviles pasadas (sin fuga temporal o *no lookahead bias*), algoritmos como **`XGBoost`** (Chen & Guestrin, 2016), Máquinas de Soporte Vectorial (SVM-RBF), Bosques Aleatorios y redes recurrentes LSTM permiten modelar interacciones no lineales entre depresión del punto de rocío, $\text{VPD}$ mínimo y horas acumuladas de humedad foliar. Dado que los clasificadores de árbol pueden producir probabilidades descalibradas, se aplica **calibración probabilística isotónica** o de Platt minimizando el **Brier Score** ($\text{BS} = \frac{1}{N}\sum (p_i - y_i)^2$), métrica propia estricta de confiabilidad probabilística, junto con **valores Shapley (`SHAP` `TreeExplainer`)** (Lundberg & Lee, 2017) para auditar qué variables bioclimáticas (p. ej., `lwh_suma_48h`) explican cada alerta de riesgo.

Finalmente, el trabajador supervisor `inference_worker` (`server/app/worker.py`) integra la componente climática ($P_{\text{clima}}$), la evidencia visual ($S_{\text{visión}}$, ponderando severidad foliar y conteo de insectos) y la derivada temporal higrométrica reciente ($T_{48\text{h}}$) mediante la función lineal de **fusión multimodal** acotada en $[0, 1]$:

$$R_{\text{total}} = \text{clip}\Big(0{,}45\,P_{\text{clima}} + 0{,}35\,S_{\text{visión}} + 0{,}20\,T_{48\text{h}},\; 0,\; 1\Big)$$

Según el umbral alcanzado, el supervisor clasifica el estado en `BAJO` ($< 0{,}30$), `MEDIO` ($[0{,}30; 0{,}55)$), `ALTO` ($[0{,}55; 0{,}75)$) o `CRÍTICO` ($\ge 0{,}75$), comandando nuevos *setpoints* al ESP32 vía MQTT y disparando notificaciones enriquecidas por `Telegram` únicamente en transiciones de riesgo elevado. La arquitectura completa de modelos visuales, predictores bioclimáticos y fusión multimodal se sintetiza en la Tabla 7.

**Tabla 7**  
*Síntesis de modelos de visión artificial, riesgo bioclimático y arquitectura de fusión multimodal del sistema*

| Subsistema IA | Modelo / Técnica | Datos / Entradas | Métrica clave de selección | Rol en el sistema integrado |
| :--- | :--- | :--- | :--- | :--- |
| Visión foliar piloto (clasificación) | `YOLO26n-cls` | `PlantVillage` curado ($2.152$ imgs, 3 clases) | `Accuracy Top-1`, `val/loss` | Validación base de clasificación foliar sin fuga por hash |
| Visión foliar piloto (detección) | `YOLO26n` vs. `YOLO11n` | `PlantDoc` curado ($219$ imgs, $569$ cajas `whole_leaf`) | `mAP@0.50`, `mAP@0.50:0.95`, `Recall` | Selección de `YOLO26n` por superioridad en validación |
| Detección de micro-objetos | `YOLO26n` + `SAHI` ($320\times 320$, solape $0{,}20$) | Imágenes de `TRAMPA_AMARILLA` y `HOJA_FOLLAJE` | `mAP@0.50`, `F1-Score`, latencia CPU | Mitigar pérdida espacial en insectos y lesiones $\le 5\text{ \%}$ |
| Predicción de riesgo climático | `XGBoost` calibrado isotónicamente + `SHAP` | 24 variables de telemetría y ventanas móviles (sin *lookahead*) | Mínimo `Brier Score`, `ROC-AUC`, `PR-AUC` | Estimar probabilidad climática calibrada e interpretable |
| Fusión multimodal supervisora | $0{,}45\,P_{\text{clima}} + 0{,}35\,S_{\text{visión}} + 0{,}20\,T_{48\text{h}}$ | Ventana climática + última detección + tendencia | Latencia de alerta $\le 30\text{ min}$ | Actualizar *setpoints* en cascada vía MQTT y alertar en `Telegram` |

*Nota.* Elaboración propia a partir de `vision_service.py`, `worker.py`, `ejecutar_fase5_riesgo_fusion.py` y `verificacion.json`.

---

## 2.6 Metodologías de ingeniería de sistemas y evaluación de calidad

El desarrollo de un prototipo donde convergen electrónica de potencia, firmware de tiempo real, telecomunicaciones IoT, control automático y modelos de aprendizaje automático exige metodologías formales que aseguren trazabilidad entre requisitos y verificación empírica:

1. **Modelo en V para sistemas mecatrónicos y ciberfísicos (`VDI/VDE 2206`):** La guía técnica `VDI/VDE 2206` (Verein Deutscher Ingenieure [VDI/VDE], 2021) estructura el ciclo de vida en dos ramas simétricas. La rama descendente izquierda descompone los requisitos del sistema (microclima de papa, seguridad eléctrica y detección temprana) en diseño de dominio específico: electrónica/firmware en el `ESP32`, leyes de control FOPDT/PID, microservicios Docker y modelos de visión. La rama ascendente derecha verifica progresivamente cada módulo (pruebas unitarias, compilación de firmware, simulación Wokwi, pruebas de integración API/MQTT) y culmina en la validación experimental integrada del sistema completo (`E1`–`E8`), en armonía con principios de seguridad funcional derivados de `IEC 61508` (como estados seguros ante fallo de sensor y *Watchdog* de hardware).
2. **Flujo reproducible de ciencia de datos y MLOps (`CRISP-DM` verificable):** Para el ciclo analítico de visión artificial y modelado de riesgo se adoptan las fases de comprensión del dominio agronómico, preparación y curaduría de datos con manifiestos criptográficos `SHA-256`, modelado comparativo con semillas fijas y partición temporal estricta sin fuga futura, y evaluación cuantitativa previa al despliegue en servicio.
3. **Calidad de producto software (`ISO/IEC 25010`) y diseño experimental cuantitativo:** Siguiendo las pautas de `ISO/IEC 25010` (referenciada en el marco de calidad de sistemas ciberfísicos de VDI/VDE, 2021), la plataforma web `Django 6.1.2` y la API `FastAPI` se evalúan en adecuación funcional, fiabilidad operativa, usabilidad de tableros, seguridad (autenticación MQTT y validación de entradas) y mantenibilidad mediante integración continua automatizada (`pytest`, `flake8`, `manage.py check`). A nivel metodológico, la contrastación entre el Nivel 0 (manual/On-Off) y el Nivel 1 (automatizado IoT–PID–IA) se encuadra en un diseño **cuantitativo aplicado cuasiexperimental en bloques pareados** (Hernández-Sampieri & Mendoza, 2018), evitando la falacia de tratar lecturas secuenciales de un sensor a $1\text{ Hz}$ como réplicas estadísticas independientes.

---

## 2.7 Marco legal, normativo y ético en el Estado Plurinacional de Bolivia

El desarrollo y eventual despliegue de tecnología ciberfísica agrícola en Bolivia se enmarca en disposiciones jurídicas, reglamentos técnicos nacionales y estándares internacionales de interoperabilidad:

- **Ley N.º 144 de Revolución Productiva Comunitaria Agropecuaria (Estado Plurinacional de Bolivia, 2011):** Establece como política de Estado el logro de la seguridad con soberanía alimentaria mediante el fomento a la innovación tecnológica, la asistencia técnica oportuna y la protección de cultivos estratégicos como la papa, legitimando el desarrollo nacional de herramientas de monitoreo y control agrícola adaptadas a zonas altoandinas.
- **Ley N.º 300 Marco de la Madre Tierra y Desarrollo Integral para Vivir Bien (Estado Plurinacional de Bolivia, 2012):** Dispone el aprovechamiento sustentable de los sistemas de vida y la conservación de la agrobiodiversidad nativa, promoviendo la reducción progresiva de agroquímicos sintéticos contaminantes. El enfoque de Manejo Integrado de Plagas del prototipo —basado en prevención microclimática y detección temprana no destructiva— responde directamente a este mandato ambiental.
- **Norma Boliviana `NB 777` de diseño y construcción de instalaciones eléctricas interiores en baja tensión (Instituto Boliviano de Normalización y Calidad [IBNORCA], 2015/2024):** Regula obligatoriamente en Bolivia los criterios de seguridad en circuitos de hasta $1000\text{ V}$, incluyendo dimensionamiento de conductores, protecciones termomagnéticas y diferenciales, fusibles, puesta a tierra y aislamiento galvánico. Su observancia resulta crítica en la etapa de potencia de $220\text{ V AC}$ del calefactor gobernado por el `SSR` fototriac del prototipo, separando físicamente los circuitos de alta tensión de la etapa lógica de $3{,}3\text{ V}$ y $12\text{ V DC}$.
- **Estándares abiertos de interoperabilidad y ética de datos:** El uso del estándar internacional `MQTT v3.1.1` (OASIS, 2014) evita el aprisionamiento tecnológico (*vendor lock-in*). Desde el punto de vista ético y científico, el sistema garantiza soberanía local de datos (al operar íntegramente en LAN sin exponer imágenes ni telemetría a servidores externos propietarios), mantiene transparencia absoluta entre métricas simuladas, pilotos en datasets públicos y resultados de campo, y preserva el principio de **supervisión humana en el bucle**: la IA informa y sugiere acciones fitosanitarias, pero nunca ejecuta aplicaciones químicas autónomas. El resumen del marco jurídico y normativo aplicable se presenta en la Tabla 8.

**Tabla 8**  
*Matriz de marco legal, normativo y ético aplicable al prototipo en Bolivia*

| Instrumento normativo / estándar | Entidad emisora y año | Ámbito de aplicación | Implicación directa en el prototipo |
| :--- | :--- | :--- | :--- |
| `Ley N.º 144` | Estado Plurinacional de Bolivia (2011) | Soberanía alimentaria e innovación agropecuaria | Respalda la transferencia tecnológica hacia el cultivo estratégico de papa |
| `Ley N.º 300` | Estado Plurinacional de Bolivia (2012) | Madre Tierra, agrobiodiversidad y sustentabilidad | Fundamenta la reducción de fungicidas vía MIP y uso racional del agua |
| `Norma Boliviana NB 777` | IBNORCA (2015/2024) | Seguridad en instalaciones eléctricas de baja tensión | Exige protecciones, fusibles, puesta a tierra y aislamiento `SSR` en $220\text{ V AC}$ |
| `OASIS MQTT v3.1.1` | OASIS (2014) | Interoperabilidad M2M en redes restringidas | Asegura estándar abierto, autenticación `PBKDF2-SHA512` y portabilidad IoT |
| `VDI/VDE 2206` e `ISO/IEC 25010` | VDI/VDE (2021); marco ISO/IEC 25010 | Ingeniería de sistemas ciberfísicos y calidad software | Estructura trazabilidad requisitos-ensayos (`E1`–`E8`) y seguridad operativa |

*Nota.* Elaboración propia a partir del marco jurídico boliviano y estándares técnicos verificados en el proyecto.

---

## 2.8 Marco conceptual

Con el propósito de unificar la precisión terminológica a lo largo de la memoria de tesis, se definen a continuación veinticinco conceptos técnicos fundamentales ordenados alfabéticamente:

1. **Agricultura 4.0:** Paradigma agroproductivo que integra sensores IoT, computación en el borde o nube, control automático e inteligencia artificial para optimizar la toma de decisiones agronómicas basadas en datos continuos (Liu et al., 2021; Zambon et al., 2019).
2. **Anti-windup (Clamping condicional):** Mecanismo de protección en controladores PID discretos que suspende la acumulación del término integral cuando el actuador alcanza saturación ($\pm 100\text{ \%}$), evitando sobreimpulsos prolongados al retornar a la zona lineal (Skogestad, 2003).
3. **Banda muerta (*Deadband*):** Intervalo simétrico alrededor del *setpoint* ($\pm 0{,}25\text{ }^\circ\text{C}$ en el firmware `ESP32`) dentro del cual el error se asume nulo para evitar conmutaciones repetitivas de actuadores frente a ruido de medición.
4. **Brier Score:** Métrica propia de evaluación probabilística definida como el error cuadrático medio entre las probabilidades predichas y los desenlaces binarios reales, utilizada para seleccionar modelos calibrados de riesgo fitopatológico (Chen & Guestrin, 2016).
5. **Broker MQTT:** Servidor intermediario ligero (implementado con `Eclipse Mosquitto 2.0.18`) que autentica clientes, filtra mensajes por tópicos jerárquicos y distribuye cargas JSON según niveles de Calidad de Servicio (OASIS, 2014).
6. **Caja delimitadora (*Bounding Box*):** Coordenada rectangular $[x_1, y_1, x_2, y_2]$ que localiza espacialmente una hoja, lesión o insecto dentro de una imagen digital para entrenamiento y evaluación de detectores (Padilla et al., 2020).
7. **Calibración gravimétrica edáfica:** Procedimiento metrológico que correlaciona las cuentas ADC de un sensor capacitivo de suelo con el contenido volumétrico real de agua ($\text{\% VWC}$) determinado mediante secado de muestras en estufa a $105\text{ }^\circ\text{C}$.
8. **Control en cascada jerárquica:** Arquitectura de dos lazos acoplados donde un lazo externo lento (supervisor multimodal en `inference_worker`) recalcula las consignas de un lazo interno rápido y autónomo (PID de $10\text{ Hz}$ en `ESP32`).
9. **Controlador PID discreto:** Algoritmo de retroalimentación en tiempo muestreado que combina acciones proporcional al error actual, integral del error acumulado y derivativa sobre la tasa de cambio de la variable medida (Skogestad, 2003).
10. **Criterios de Hutton:** Regla epidemiológica contemporánea de alerta para tizón tardío de la papa que declara riesgo crítico tras dos días consecutivos con temperatura mínima $\ge 10{,}0\text{ }^\circ\text{C}$ y al menos $6\text{ h/día}$ de $\text{HR} \ge 90\text{ \%}$ (AHDB, 2020).
11. **Déficit de Presión de Vapor (VPD):** Diferencia en kilopascales ($\text{kPa}$) entre la presión de saturación y la presión parcial real de vapor en el aire, indicador físico directo de la demanda evaporativa y transpiración estomática (Andrade-Piedra et al., 2005).
12. **Filtro de Hampel y EMA:** Cadena de acondicionamiento digital en borde que rechaza picos atípicos respecto a la mediana móvil (Hampel) y suaviza fluctuaciones de alta frecuencia mediante promedio móvil exponencial (EMA).
13. **Fuga de datos (*Data Leakage*):** Contaminación metodológica entre particiones de entrenamiento y prueba provocada por imágenes duplicadas o información temporal futura (*lookahead*), mitigada mediante hashing de píxeles y partición cronológica estricta.
14. **Fusión multimodal bioclimática-visual:** Combinación ponderada ($0{,}45\,P_{\text{clima}} + 0{,}35\,S_{\text{visión}} + 0{,}20\,T_{48\text{h}}$) que integra probabilidad de riesgo ambiental, detección visual y tendencia higrométrica reciente en un índice de decisión unificado.
15. **Horas de Hoja Húmeda (LWH):** Duración acumulada o continua (en horas) durante la cual las condiciones de humedad relativa elevada o proximidad al punto de rocío mantienen película acuosa favorable a la infección fúngica (Andrade-Piedra et al., 2005; Wallin, 1962).
16. **IAE (*Integral of Absolute Error*):** Índice integral de desempeño dinámico ($\int |e(t)|\,dt$) que cuantifica la desviación térmica acumulada sin cancelación de errores positivos y negativos (Skogestad, 2003).
17. **Intersección sobre Unión (IoU):** Razón geométrica entre el área de intersección y el área de unión de las cajas predicha y real, utilizada como criterio espacial de acierto ($\text{IoU} \ge 0{,}50$) en detección de objetos (Padilla et al., 2020).
18. **Manejo Integrado de Plagas (MIP):** Estrategia fitosanitaria sustentable que combina prevención microclimática y monitoreo temprano para intervenir únicamente antes de alcanzar el umbral de daño económico, reduciendo agroquímicos (Cruz-Trujillo et al., 2021).
19. **Modelo FOPDT (*First-Order Plus Dead-Time*):** Aproximación lineal de planta térmica caracterizada por ganancia estática $K$, constante de tiempo $\tau$ y tiempo muerto $\theta$, base para identificación y sintonización PID (Pérez Rojas & Cortés, 2007/2018; Skogestad, 2003).
20. **Optuna (TPE):** Marco de optimización bayesiana secuencial basado en estimadores de Parzen estructurados en árbol para hallar ganancias PID óptimas minimizando funciones de costo multiobjetivo (Akiba et al., 2019).
21. **Precisión Media Promedio (`mAP@0.50`):** Promedio de las áreas bajo la curva Precisión-*Recall* entre todas las clases evaluadas bajo umbral $\text{IoU} \ge 0{,}50$ (Padilla et al., 2020).
22. **SAHI (*Slicing Aided Hyper Inference*):** Técnica de inferencia en visión computacional que particiona imágenes en ventanas superpuestas ($320 \times 320\text{ px}$, solape $20\text{ \%}$) para preservar la resolución de insectos diminutos y microlesiones (Akyon et al., 2022).
23. **SHAP (*SHapley Additive exPlanations*):** Método de explicabilidad basado en teoría de juegos cooperativos que cuantifica la contribución marginal de cada variable bioclimática en la predicción de riesgo de `XGBoost` (Lundberg & Lee, 2017).
24. **Sistema Ciberfísico (CPS) y Modelo en V (`VDI/VDE 2206`):** Paradigma de ingeniería que acopla cómputo, comunicación y control físico mediante un ciclo simétrico de diseño modular descendente y verificación experimental ascendente (VDI/VDE, 2021).
25. **YOLO26n (*You Only Look Once* v26 Nano):** Detector de objetos ligero de una sola etapa diseñado para CPU de borde, con regresión directa sin DFL, inferencia libre de NMS y pérdidas `ProgLoss`/`STAL` para objetos pequeños (Ultralytics, 2026).
