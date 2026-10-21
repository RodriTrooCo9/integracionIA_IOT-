# Protocolo de Captura de Imágenes y Guía de Etiquetado para Detección de Plagas y Enfermedades en Papa

> **Proyecto:** Prototipo Integrado IoT–PID–IA para Papa bajo Invernadero (La Paz, Bolivia)  
> **Fase:** 3 – Dataset de Visión (Captura, Curaduría y Etiquetado)

---

## 1. Contexto Biológico y Agronómico en La Paz

En el altiplano paceño (~3600 msnm), el cultivo de papa (*Solanum tuberosum*) enfrenta dos amenazas patológicas y entomológicas críticas debido a la gran amplitud térmica y el confinamiento bajo cubierta plástica (agrofilm térmico):
1. **Complejo Fúngico Foliar:**
   - **Tizón Tardío (*Phytophthora infestans*):** Oomiceto devastador que prolifera con humedad relativa $> 85\%$ y temperaturas entre $12^\circ\text{C}$ y $20^\circ\text{C}$ (noches frías y madrugadas de La Paz). Provoca lesiones acuosas oscuras de rápida expansión.
   - **Tizón Temprano (*Alternaria solani*):** Hongo caracterizado por manchas necróticas secas de color marrón oscuro con anillos concéntricos concéntricos distintivos ("efecto diana").
2. **Plagas Entomológicas en Trampas Adhesivas:**
   - **Mosca Minadora (*Liriomyza huidobrensis*):** Díptero adulto de 1.5 a 2.2 mm con escudo dorsal negro y un escutelo amarillo brillante muy visible en el tórax.
   - **Pulgones (*Myzus persicae* / *Aphididae*):** Insectos diminutos de 1.2 a 2.5 mm, vectores de virus primarios (PLRV, PVY).
   - **Polilla de la Papa (*Phthorimaea operculella*):** Microlepidóptero nocturno de 7 a 9 mm de envergadura, color grisáceo ocre con puntos oscuros.

---

## 2. Taxonomía de Clases Priorizadas

Para balancear la complejidad computacional en CPU y maximizar la precisión en la defensa de tesis, el modelo de visión se estructura en **6 clases estandarizadas**:

| Class ID | Nombre de Clase | Tipo de Objetivo | Entorno de Captura | Dimensiones Típicas en Píxeles (640×640) |
| :---: | :--- | :--- | :--- | :---: |
| `0` | `tizon_tardio` | Patología foliar | Hoja de papa en dosel | $40 \times 40$ a $250 \times 250\text{ px}$ |
| `1` | `tizon_temprano` | Patología foliar | Hoja de papa en dosel | $30 \times 30$ a $180 \times 180\text{ px}$ |
| `2` | `hoja_sana` | Control foliar | Follaje vigoroso | $100 \times 100$ a $400 \times 400\text{ px}$ |
| `3` | `mosca_minadora` | Insecto plaga | Trampa adhesiva amarilla | **$12 \times 12$ a $35 \times 35\text{ px}$** (Objeto pequeño) |
| `4` | `pulgon` | Insecto plaga | Trampa adhesiva amarilla | **$8 \times 8$ a $25 \times 25\text{ px}$** (Objeto pequeño) |
| `5` | `polilla_papa` | Insecto plaga | Trampa adhesiva amarilla | $40 \times 25$ a $90 \times 50\text{ px}$ |

> [!IMPORTANT]
> Las clases `mosca_minadora` y `pulgon` sobre trampa amarilla son clasificadas como **objetos pequeños** según el estándar MS COCO ($area < 32 \times 32\text{ px}$). Por esta razón, el pipeline de inferencia integra **SAHI (Slicing Aided Hyper Inference)** con ventanas deslizantes de $320 \times 320\text{ px}$ para resolver el problema de baja resolución sin recurrir a sensores industriales costosos.

---

## 3. Protocolo Físico de Captura en Invernadero

### 3.1 Equipamiento Óptico
- **Cámara Principal:** Cámara USB 1080p ($1920 \times 1080$), sensor CMOS de 2 MP, lente de baja distorsión ($< 1\%$), montada en brazo rígido articulado.
- **Nodo Inalámbrico Secundario:** Módulo ESP32-CAM con sensor Omnivision OV2640 configurado en resolución UXGA ($1600 \times 1200$) o HD ($1280 \times 720$).

### 3.2 Geometría y Parámetros de Disparo

```
  [ Vista Superior: Encuadre Trampa ]           [ Vista Lateral: Follaje ]
  
        Cámara USB 1080p                              Cámara USB
             [ ■ ]                                      [ ■ ]
               │                                         │
               │ Distancia: 15 cm                        │ Distancia: 25 cm
               │ Perpendicular: 90°                      │ Ángulo: 70° a 80°
               ▼                                         ▼
      ┌─────────────────┐                        \ \ \  (Hojas de papa)
      │ Trampa Adhesiva │                         \ \ \ (Evitar reflejo
      │ Amarilla 15x20cm│                                especular de rocío)
      └─────────────────┘
```

1. **Trampas Cromáticas Amarillas:**
   - **Distancia:** $15\text{ cm} \pm 2\text{ cm}$ constante.
   - **Ángulo:** Rigurosamente perpendicular ($90^\circ$) respecto a la superficie de la lámina adhesiva.
   - **Iluminación:** Difusa indirecta para evitar destellos especulares en el pegamento adhesivo.
   - **Periodicidad:** Fotografía diaria a la misma hora para monitorear la tasa de captura acumulada.
2. **Hojas y Follaje (Dosel):**
   - **Distancia:** $25\text{ cm} \pm 5\text{ cm}$.
   - **Ángulo:** Entre $70^\circ$ y $80^\circ$ respecto al plano de la hoja (evita que la luz refleje directamente en la lente cuando las hojas tienen rocío matutino).
   - **Fondo:** Fondo natural del cultivo con suelo o sustrato visible, o pantalla neutra gris si se evalúan hojas aisladas en etapa de calibración.

### 3.3 Horarios e Iluminación Estratificada
Para dotar al modelo de invariancia lumínica ante la intensa radiación de La Paz, las capturas se distribuyen en tres ventanas horarias:
- **Ventana 1 - Madrugada / Mañana (08:00 - 10:00):** Iluminación suave, temperatura en ascenso, presencia potencial de rocío foliar (crítico para tizón tardío).
- **Ventana 2 - Mediodía (12:00 - 13:30):** Radiación cenital máxima bajo agrofilm térmico, alta saturación de canal verde y sombras duras.
- **Ventana 3 - Tarde / Crepúsculo (16:30 - 18:00):** Luz rasante cálida, transición hacia enfriamiento nocturno.

---

## 4. Guía de Anotación (Bounding Boxes en Formato YOLO)

Cada imagen anotada genera un archivo `.txt` con el mismo nombre base, donde cada línea representa una detección:

```
<class_id> <x_center> <y_center> <width> <height>
```
*(Todos los valores normalizados en el rango $0.0$ a $1.0$).*

### 4.1 Criterios de Delimitación de Cajas
1. **Ajuste Ceñido (*Tight Bounding Box*):** La caja debe abarcar el contorno visible del insecto (incluyendo antenas prominentes o alas) con un margen de holgura máximo de 2 a 3 píxeles.
2. **Oclusiones Parciales:** Si un insecto o lesión foliar está cubierto parcialmente por otra hoja o residuo, se etiqueta únicamente si al menos el **$40\%$** del espécimen es visible y reconocible por sus características diagnósticas.
3. **Agrupamiento (*Clusters*):** Si hay varios pulgones juntos sobre la trampa adhesiva, **está estrictamente prohibido crear una sola caja grande**. Se debe etiquetar cada individuo por separado para que el modelo aprenda a contar especímenes individuales.
4. **Lesiones de Tizón:** Delimitar la lesión activa incluyendo el halo clorótico amarillento que bordea el tejido necrótico marrón.

---

## 5. Prevención de Fuga de Datos (*Data Leakage Prevention*)

> [!CAUTION]
> **Defensa ante el Jurado de Grado:** Una objeción clásica en tesis de visión artificial es la "fuga de datos", que ocurre cuando recortes, aumentos o fotos consecutivas de la misma hoja/trampa se reparten aleatoriamente entre entrenamiento y prueba, arrojando métricas de precisión infladas artificialmente.

### Protocolo de División 70/15/15:
1. **Partición por Unidad Física (*Group Split*):**
   - El conjunto de datos se divide por **código de planta individual** o **identificador de trampa amarilla** (`planta_01`, `planta_02`, `trampa_A1`, etc.).
   - Todas las fotos de la `planta_01` van exclusivamente a `train`.
   - La `planta_04` va exclusivamente a `val`.
   - La `planta_07` va exclusivamente a `test`.
2. **Integración de Datasets Abiertos (PlantVillage, PlantDoc, IP102):**
   - Las imágenes de **PlantVillage** (tomadas en laboratorio con fondos grises uniformes) se emplean **únicamente en el conjunto de entrenamiento (`train`)** para inicializar los pesos y acelerar la convergencia (*Transfer Learning*).
   - Los conjuntos de validación (`val`) y prueba (`test`) contienen **exclusivamente imágenes reales tomadas en el invernadero o en condiciones de cultivo real**. De este modo, la precisión reportada en la tesis refleja el desempeño real en campo, no la memorización de fondos de laboratorio.
