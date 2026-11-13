# Fichero de Fuentes Bibliográficas Verificadas (FASE 2 – Agente 2)

**Proyecto:** Sistema prototipo integrado de IoT, control PID e inteligencia artificial para la regulación microclimática y detección temprana de plagas en el cultivo de papa bajo invernadero  
**Formato:** APA 7.ª edición  
**Total de fuentes verificadas:** 32 fuentes reales contrastadas mediante búsqueda web, DOIs oficiales, repositorios institucionales, normativa boliviana vigente y documentación oficial (`docs/bibliografia_web_proyecto.md` y cuaderno NotebookLM `427f0def-ffd4-4749-879f-4978fe90bb05`).  
> [NOTA] Toda fuente no verificada o con metadatos dudosos en borradores previos fue descartada o corregida (p. ej., corrección del DOI de Chanchí-Golondrino et al., 2022 y del capítulo de Struik, 2007).

---

## 1. Normativa Boliviana, Agronomía de la Papa y Epidemiología Fitopatológica

1. **Estado Plurinacional de Bolivia. (2011).** *Ley N.º 144, de 26 de junio de 2011, Ley de la Revolución Productiva Comunitaria Agropecuaria.* Gaceta Oficial del Estado Plurinacional de Bolivia. https://www.gacetaoficialdebolivia.gob.bo/  
   - **Utilidad:** Establece el marco legal boliviano de seguridad y soberanía alimentaria, priorizando la asistencia técnica, semillas de calidad e innovación agroecológica sustentable en cultivos estratégicos.  
   - **Uso en la tesis:** Capítulo II (Marco normativo boliviano) y Capítulo I (Justificación social y contextual).

2. **Estado Plurinacional de Bolivia. (2012).** *Ley N.º 300, de 15 de octubre de 2012, Ley Marco de la Madre Tierra y Desarrollo Integral para Vivir Bien.* Gaceta Oficial del Estado Plurinacional de Bolivia. https://www.gacetaoficialdebolivia.gob.bo/  
   - **Utilidad:** Regula la gestión integral y sustentable de agroecosistemas y protege la agrobiodiversidad nativa boliviana, incluida la papa, reduciendo la dependencia de agroquímicos sintéticos.  
   - **Uso en la tesis:** Capítulo II (Marco legal ambiental/fitogenético) y justificación del Manejo Integrado de Plagas (MIP).

3. **Instituto Boliviano de Normalización y Calidad [IBNORCA]. (2015/2024).** *Norma Boliviana NB 777: Diseño y construcción de instalaciones eléctricas interiores en baja tensión.* IBNORCA. https://www.ibnorca.org/  
   - **Utilidad:** Define los requisitos obligatorios de seguridad eléctrica en Bolivia hasta 1000 V (protecciones, puesta a tierra, secciones de conductores y aislamiento), aplicables a la etapa de potencia de 220 V AC del calefactor SSR.  
   - **Uso en la tesis:** Capítulo II (Marco normativo técnico) y Capítulo III (3.2 Materiales y criterios de seguridad eléctrica en 220 V AC).

4. **Devaux, A., Goffart, J.-P., Petsakos, A., Kromann, P., Gatto, M., Okello, J. J., Suarez, V., & Hareau, G. (2020).** Global food security, contributions from sustainable potato agri-food systems. En H. Campos & O. Ortiz (Eds.), *The potato crop: Its agricultural, nutritional and social contribution to humankind* (pp. 3–35). Springer. https://doi.org/10.1007/978-3-030-28683-5_1  
   - **Utilidad:** Cuantifica la importancia estratégica global y andina de *Solanum tuberosum* para la seguridad alimentaria y los desafíos climáticos en regiones de montaña.  
   - **Uso en la tesis:** Capítulo I (Introducción y planteamiento) y Capítulo II (Importancia socioeconómica del cultivo de papa).

5. **Struik, P. C. (2007).** Responses of the potato plant to temperature. En D. Vreugdenhil, J. E. Bradshaw, C. Gebhardt, F. Govers, D. K. L. MacKerron, M. A. Taylor, & H. A. Ross (Eds.), *Potato biology and biotechnology: Advances and perspectives* (pp. 367–393). Elsevier. https://doi.org/10.1016/B978-044451018-1/50053-1  
   - **Utilidad:** Fundamenta fisiológicamente los umbrales térmicos diurnos/nocturnos por etapa fenológica y la inhibición hormonal de la tuberización por estrés térmico (>25 °C).  
   - **Uso en la tesis:** Capítulo II (Bases bio-agronómicas) y Capítulo III (Setpoints fisiológicos del PID).

6. **Andrade-Piedra, J. L., Hijmans, R. J., Forbes, G. A., Fry, W. E., & Nelson, R. J. (2005).** Simulation of potato late blight in the Andes. I: Modification and parameterization of the LATEBLIGHT model. *Phytopathology*, *95*(10), 1191–1199. https://doi.org/10.1094/PHYTO-95-1191  
   - **Utilidad:** Describe la dinámica epidemiológica de *Phytophthora infestans* bajo condiciones climáticas andinas de altura, temperaturas frescas y película de agua foliar.  
   - **Uso en la tesis:** Capítulo II (Fitopatología del tizón tardío) y Capítulo III (Lógica bioclimática y umbrales de riesgo).

7. **Wallin, J. R. (1962).** Summary of recent progress in predicting late blight epidemics in United States and Canada. *American Potato Journal*, *39*(8), 306–312.  
   - **Utilidad:** Fuente primaria histórica de los valores de severidad acumulada según temperatura y duración de alta humedad relativa, referenciada como base conceptual del módulo `BlightManager` de la Fase 5.  
   - **Uso en la tesis:** Capítulo II (Modelos predictivos de riesgo) y Capítulo III / IV (Aclaración explícita entre modelo Wallin clásico y adaptación sigmoide en código).

8. **Agriculture and Horticulture Development Board [AHDB]. (2020).** *Development and implementation of a new national warning system for potato late blight in Great Britain (Hutton Criteria).* AHDB Horticulture. https://horticulture.ahdb.org.uk/development-and-implementation-of-a-new-national-warning-system-for-potato-late-blight-in-great-britain-hutton-criteria  
   - **Utilidad:** Define el criterio contemporáneo de riesgo epidémico por tizón tardío (dos días consecutivos con T >= 10 °C y >= 6 h con HR >= 90 %), contrastable frente a la regla clásica de Smith.  
   - **Uso en la tesis:** Capítulo II (Estado del arte en sistemas de alerta fitosanitaria) y discusión de umbrales en el worker supervisor.

9. **Cruz-Trujillo, J. J., Hernández-Gutiérrez, V., Sánchez-Leal, L. C., & Fuentes-Quintero, L. S. (2021).** Alternativas de control biorracionales sobre *Phytophthora infestans*, fitopatógeno causante de la gota en papa. *Nova*, *19*(36), 31–48. https://doi.org/10.22490/24629448.5287  
   - **Utilidad:** Respalda el impacto productivo de *P. infestans* en papa andina y la necesidad de reducir fungicidas químicos mediante detección precoz y manejo integrado.  
   - **Uso en la tesis:** Capítulo I (Justificación ambiental) y Capítulo II (Manejo Integrado de Plagas).

10. **Wilches Ortiz, W., Vargas Díaz, R., & Espitia Malagón, E. (2022).** Relationship between effects of climate and the late blight (*Phytophthora infestans* (Mont.) de Bary) in the potato (*Solanum tuberosum* L.) crop. *Siembra*, *9*(2), e4008. https://doi.org/10.29166/siembra.v9i2.4008  
    - **Utilidad:** Demuestra empíricamente la correlación entre variables microclimáticas (humedad relativa, temperatura, precipitación/rocío) y severidad del tizón tardío en papa andina.  
    - **Uso en la tesis:** Capítulo II (Bases epidemiológicas) y Capítulo III (Variables climáticas de entrada al supervisor).

---

## 2. Agricultura 4.0, Sistemas Ciberfísicos (CPS), IoT y Antecedentes

11. **Liu, Y., Ma, X., Shu, L., Hancke, G. P., & Abu-Mahfouz, A. M. (2021).** From Industry 4.0 to Agriculture 4.0: Current status, enabling technologies, and research challenges. *IEEE Transactions on Industrial Informatics*, *17*(6), 4322–4334. https://doi.org/10.1109/TII.2020.3003910  
    - **Utilidad:** Taxonomía de tecnologías habilitadoras de Agricultura 4.0 (IoT, Edge/Cloud AI, automatización y desafíos en entornos agrícolas reales).  
    - **Uso en la tesis:** Capítulo II (Evolución hacia Agricultura 4.0 y estado del arte).

12. **Zambon, I., Cecchini, M., Egidi, G., Saporito, M. G., & Colantoni, A. (2019).** Revolution 4.0: Industry vs. agriculture in a future development for SMEs. *Processes*, *7*(1), 36. https://doi.org/10.3390/pr7010036  
    - **Utilidad:** Analiza la transferencia de tecnologías ciberfísicas 4.0 hacia productores de pequeña y mediana escala.  
    - **Uso en la tesis:** Capítulo I (Contexto) y Capítulo II (Paradigmas productivos).

13. **Ayaz, M., Ammad-Uddin, M., Sharif, Z., Mansour, A., & Aggoune, E.-H. M. (2019).** Internet-of-Things (IoT)-based smart agriculture: Toward making the fields talk. *IEEE Access*, *7*, 129551–129583. https://doi.org/10.1109/ACCESS.2019.2932609  
    - **Utilidad:** Revisión sistemática de sensores agrícolas, microcontroladores, topologías de comunicación y monitoreo ambiental bajo invernadero.  
    - **Uso en la tesis:** Capítulo II (Arquitectura IoT agrícola y justificación sensorial).

14. **Farooq, M. S., Riaz, S., Abid, A., Umer, T., & Zikria, Y. B. (2020).** Role of IoT technology in agriculture: A systematic literature review. *Electronics*, *9*(2), 319. https://doi.org/10.3390/electronics9020319  
    - **Utilidad:** Compara protocolos de comunicación, capas IoT y gestión de energía/red en aplicaciones agrícolas protegidas.  
    - **Uso en la tesis:** Capítulo II (Capas IoT y redes de sensores).

15. **Chanchí-Golondrino, G. E., Ospina-Alarcón, M. A., & Saba, M. (2022).** Sistema IoT para el monitoreo de variables climatológicas en cultivos de agricultura urbana. *Revista Científica*, *44*(2), 257–271. https://doi.org/10.14483/23448350.18470  
    - **Utilidad:** Antecedente latinoamericano directo de adquisición ambiental continua con nodos embebidos de bajo costo y persistencia telemática.  
    - **Uso en la tesis:** Capítulo I (Antecedentes) y Capítulo II (Estado del arte IoT).

16. **Arias Barragán, L., Aparicio, A., González, R. A., Nuncira, T., & Penagos, D. (2022).** Invernadero inteligente con control de variables de cultivos usando herramientas de IA. *Encuentro Internacional de Educación en Ingeniería (ACOFI)*. https://doi.org/10.26507/paper.4274  
    - **Utilidad:** Antecedente regional sobre integración de sensórica IoT, regulación ambiental e IA para supervisión de cultivos bajo cubierta.  
    - **Uso en la tesis:** Capítulo I y Capítulo II (Debate de integración de módulos).

17. **Aguilar Polit, M. A. (2025).** *Evaluación de la eficiencia en el crecimiento de la papa "Solanum phureja" mediante el uso de IoT y sensórica en producción hidropónica* [Trabajo de titulación, Universidad Internacional SEK Ecuador]. Repositorio Institucional UISEK. https://repositorio.uisek.edu.ec/handle/123456789/5412  
    - **Utilidad:** Antecedente andino reciente en papa bajo ambiente protegido que reporta optimización del desarrollo foliar y ahorro hídrico de 32,7 % con sensórica IoT.  
    - **Uso en la tesis:** Capítulo I (Antecedentes internacionales) y Capítulo II (Justificación agronómica del monitoreo continuo).

18. **OASIS. (2014).** *MQTT Version 3.1.1* [OASIS Standard]. https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/os/mqtt-v3.1.1-os.html  
    - **Utilidad:** Estándar oficial del protocolo publicación/suscripción ligero empleado entre el nodo ESP32, Mosquitto, Telegraf y el backend FastAPI.  
    - **Uso en la tesis:** Capítulo II (Protocolos IoT) y Capítulo III (Especificación de comunicaciones y QoS).

---

## 3. Termodinámica de Invernaderos, Control PID, FOPDT y Optuna

19. **van Straten, G., van Willigenburg, G., van Henten, E., & van Ooteghem, R. (2011).** *Optimal control of greenhouse cultivation.* CRC Press. https://doi.org/10.1201/b10321  
    - **Utilidad:** Obra de referencia en modelado dinámico de balance de calor y masa hídrica en invernaderos tratados como sistemas acoplados ante perturbaciones externas.  
    - **Uso en la tesis:** Capítulo II (Termodinámica del invernadero y TGS) y Capítulo III (Formulación del gemelo físico).

20. **Pérez Rojas, H., & Cortés, M. d. P. (2007/2018).** *Simulación y control de la temperatura dentro de un invernadero* [Trabajo de grado / material técnico]. Universidad de La Salle, Bogotá. https://ciencia.lasalle.edu.co/  
    - **Utilidad:** Presenta ecuaciones diferenciales concentradas del volumen de control del invernadero y su sintonización clásica por curva de reacción.  
    - **Uso en la tesis:** Capítulo II (Balance energético y acoplamiento higrotérmico).

21. **Skogestad, S. (2003).** Simple analytic rules for model reduction and PID controller tuning. *Journal of Process Control*, *13*(4), 291–309. https://doi.org/10.1016/S0959-1524(02)00062-8  
    - **Utilidad:** Fundamenta matemáticamente la reducción a primer orden con tiempo muerto (FOPDT) y las reglas analíticas IMC/SIMC para controladores PI/PID estables.  
    - **Uso en la tesis:** Capítulo II (Sintonización PID sobre plantas FOPDT) y Capítulo III (Evaluación comparativa de sintonías).

22. **Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019).** Optuna: A next-generation hyperparameter optimization framework. En *Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining* (pp. 2623–2631). ACM. https://doi.org/10.1145/3292500.3330701  
    - **Utilidad:** Sustenta la optimización bayesiana basada en *Tree-structured Parzen Estimator* (TPE) utilizada en la Fase 2 para hallar las ganancias óptimas $(K_p, K_i, K_d)$ minimizando IAE y sobrepaso.  
    - **Uso en la tesis:** Capítulo II y Capítulo III (3.6/3.7 Procedimiento de sintonización automatizada).

---

## 4. Visión Computacional, YOLO, SAHI, Aprendizaje Automático y Explicabilidad

23. **Mohanty, S. P., Hughes, D. P., & Salathé, M. (2016).** Using deep learning for image-based plant disease detection. *Frontiers in Plant Science*, *7*, 1419. https://doi.org/10.3389/fpls.2016.01419  
    - **Utilidad:** Introduce el conjunto PlantVillage y demuestra la alta exactitud en clasificación de hojas aisladas (y la brecha al pasar a fondos reales complejos).  
    - **Uso en la tesis:** Capítulo II (Debate clasificación en laboratorio vs. detección en campo) y Capítulo III (Piloto de clasificación `PlantVillage`).

24. **Singh, D., Jain, N., Jain, P., Kayal, P., Kumawat, S., & Batra, N. (2020).** PlantDoc: A dataset for visual plant disease detection. En *Proceedings of the 7th ACM IKDD CoDS and 25th COMAD* (pp. 249–253). ACM. https://doi.org/10.1145/3371158.3371196  
    - **Utilidad:** Justifica el uso de imágenes de campo con fondos heterogéneos y delimita que sus anotaciones corresponden a cajas de hojas completas (219 imágenes filtradas para papa).  
    - **Uso en la tesis:** Capítulo II (Estado del arte en datasets agrícolas) y Capítulo III (Justificación del piloto detector y sus límites).

25. **Pineda Medina, D., Miranda Cabrera, I., Alfonso de la Cruz, R., Guerra Arzuaga, L., Canales Becerra, H., Gonzáles Torres, J., & Amari, S. (2023).** Sistema para el diagnóstico de plagas de *Solanum tuberosum* L. mediante técnicas de inteligencia artificial. *Revista de Protección Vegetal*, *38*, e16. https://censa.edicionescervantes.com/index.php/RPV/article/view/1298  
    - **Utilidad:** Antecedente directo de plataforma web en Python para diagnóstico visual de *Alternaria solani* y *Phytophthora infestans* en papa.  
    - **Uso en la tesis:** Capítulo I (Antecedente internacional) y Capítulo II (Arquitecturas web + IA fitosanitaria).

26. **Amjoud, A. B., & Amrouch, M. (2023).** Object detection using deep learning, CNNs and vision transformers: A review. *IEEE Access*, *11*, 35479–35516. https://doi.org/10.1109/ACCESS.2023.3266093  
    - **Utilidad:** Compara detectores de una etapa (familia YOLO) frente a detectores de dos etapas (Faster R-CNN), fundamentando el compromiso latencia-precisión en CPU.  
    - **Uso en la tesis:** Capítulo II (Marco teórico de detección de objetos).

27. **Padilla, R., Netto, S. L., & da Silva, E. A. B. (2020).** A survey on performance metrics for object-detection algorithms. En *2020 International Conference on Systems, Signals and Image Processing (IWSSIP)* (pp. 237–242). IEEE. https://doi.org/10.1109/IWSSIP48289.2020.9145130  
    - **Utilidad:** Formaliza matemáticamente IoU, Precisión, Recall, curvas P-R, mAP@0.50 y mAP@0.50:0.95 utilizados en las evaluaciones de detección de objetos.  
    - **Uso en la tesis:** Capítulo II (Ecuaciones de evaluación IA) y Capítulo III (Parámetros de evaluación 3.5).

28. **Akyon, F. C., Altinuc, S. O., & Temizel, A. (2022).** Slicing aided hyper inference and fine-tuning for small object detection. En *2022 IEEE International Conference on Image Processing (ICIP)* (pp. 966–970). IEEE. https://doi.org/10.1109/ICIP46576.2022.9897990  
    - **Utilidad:** Fundamenta el particionado en ventanas superpuestas (SAHI) integrado en `vision_service.py` para evitar la pérdida de insectos o micro-lesiones en el submuestreo de YOLO.  
    - **Uso en la tesis:** Capítulo II (Inferencia en objetos pequeños) y Capítulo III (Protocolo de detección en trampas amarillas).

29. **Ultralytics. (2026).** *Ultralytics YOLO26 & YOLO11 documentation: Unified end-to-end vision models and SAHI integration.* https://docs.ultralytics.com/  
    - **Utilidad:** Documentación técnica oficial de las arquitecturas `YOLO26n`, `YOLO26n-cls` y `YOLO11n` (eliminación de DFL, ProgLoss, STAL, C2PSA y exportación ONNX/CPU).  
    - **Uso en la tesis:** Capítulo II y Capítulo III (3.2 Software y 3.3 Metodología de entrenamiento en Colab).

30. **Chen, T., & Guestrin, C. (2016).** XGBoost: A scalable tree boosting system. En *Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining* (pp. 785–794). ACM. https://doi.org/10.1145/2939672.2939785  
    - **Utilidad:** Fundamenta el modelo tabular de gradient boosting evaluado en la Fase 5 para predicción de riesgo fitopatológico a partir de series horarias bioclimáticas.  
    - **Uso en la tesis:** Capítulo II (Aprendizaje automático en series ambientales) y Capítulo III (3.6 Procesamiento y modelado predictivo).

31. **Lundberg, S. M., & Lee, S.-I. (2017).** A unified approach to interpreting model predictions. En *Advances in Neural Information Processing Systems* (Vol. 30, pp. 4765–4774). https://doi.org/10.48550/arXiv.1705.07874  
    - **Utilidad:** Sustenta el cálculo de valores Shapley (`TreeExplainer` SHAP) para explicar la contribución de variables como `lwh_suma_48h` y `vpd_min_24h` en el modelo de riesgo.  
    - **Uso en la tesis:** Capítulo II (IA explicable) y Capítulo III / IV (Interpretabilidad de alertas bioclimáticas).

---

## 5. Metodología de Investigación, Ingeniería Ciberfísica y Calidad de Software

32. **Verein Deutscher Ingenieure [VDI/VDE]. (2021).** *VDI/VDE 2206: Development of mechatronic and cyber-physical systems.* VDI-Gesellschaft Produkt- und Prozessgestaltung. https://www.vdi.de/  
    - **Utilidad:** Estándar de ingeniería de sistemas que formaliza el Modelo en V para sistemas ciberfísicos interdisciplinarios (mecánica, electrónica, control e informática), complementado en seguridad funcional por IEC 61508 y en calidad web por ISO/IEC 25010.  
    - **Uso en la tesis:** Capítulo II (Metodología de desarrollo en V) y Capítulo III (3.3 Fases metodológicas y verificación cruzada).

*(Complemento técnico instrumental verificado en `docs/bibliografia_web_proyecto.md`: hojas de datos oficiales de Sensirion SHT31-DIS-B, Analog Devices DS18B20, Espressif ESP32, Docker Compose, FastAPI 0.110, Django 5.2, Telegraf/InfluxDB v2/Grafana y texto metodológico clásico de Hernández-Sampieri & Mendoza, 2018 para la clasificación del diseño cuantitativo cuasiexperimental).*
