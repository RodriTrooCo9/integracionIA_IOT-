# Hardware necesario: Prototipo de sistema integrado IoT–PID–Inteligencia Artificial para la regulación microclimática y detección temprana de plagas en el cultivo de papa bajo invernadero

> Los precios son **referenciales en USD** y varían según proveedor (Bolivia, AliExpress, Amazon, tiendas locales de electrónica).

---

## 1. Unidad de control (cerebro del invernadero)

| Componente | Cant. | Detalle | Precio ref. |
|---|---|---|---|
| **ESP32 DevKit V1 (30 o 38 pines)** | 1 (+1 de respaldo) | Recomendado. WiFi + 2 núcleos, 3.3 V, programable en Arduino IDE | $6-10 |
| *Alternativa:* Arduino Mega 2560 + módulo ESP-01/ESP8266 | 1 | Solo si el asesor exige Arduino. Más complejo para la parte WiFi | $15-25 |
| Placa de expansión / terminales para ESP32 (screw terminal shield) | 1 | Evita cables sueltos y falsos contactos | $4-6 |

**Nota:** el ESP32 solo trabaja en WiFi de **2.4 GHz**, no en 5 GHz.

---

## 2. Sensores (microclima)

| Sensor | Mide | Cant. | Notas | Precio ref. |
|---|---|---|---|---|
| **SHT31** (I2C) | Temperatura y humedad del aire | 2 | Más preciso que el DHT22 (±0.3 °C, ±2 % HR). Dos unidades para promediar o comparar zonas | $5-10 c/u |
| DHT22 / AM2302 | Temperatura y humedad | 1 | Opcional, económico. Útil para comparar contra el SHT31 | $4-6 |
| **Sensor capacitivo de humedad de suelo v1.2** | Humedad del sustrato | 3-4 | No usar los resistivos (YL-69), se corroen en semanas | $2-3 c/u |
| **DS18B20 sumergible** | Temperatura del suelo | 2 | Influye en la tuberización de la papa | $3-4 c/u |
| **BH1750** (I2C) | Intensidad de luz (lux) | 1 | | $2-3 |
| **MH-Z19B** o SCD30 | CO₂ | 1 (opcional) | Útil en invernadero cerrado; el SCD30 mide además temperatura y humedad | $20-35 |
| Sensor de nivel de agua (flotador) | Nivel del tanque | 1 | Protege la bomba de trabajar en seco | $2-4 |
| Pantalla de radiación / caja ventilada para sensor de aire | Protección del sensor | 1 | Evita que el sol caliente el sensor y falsee la lectura | $3-5 |
| Multiplexor I2C **TCA9548A** | Direcciones I2C | 1 (opcional) | Solo si dos SHT31 tienen la misma dirección | $3 |

---

## 3. Actuadores (lo que ejecuta el PID)

| Actuador | Función | Cant. | Notas |
|---|---|---|---|
| **Ventilador / extractor 12 V** (tipo PC de 120 mm o axial) | Bajar temperatura y humedad | 2 | Controlado por PWM, ideal para PID continuo |
| **Calefactor** (resistencia cerámica PTC 12 V/24 V o calefactor pequeño) | Subir temperatura en noches frías (crítico en La Paz) | 1 | Controlado con **SSR** usando PWM lento (time-proportional) |
| **Humidificador ultrasónico / nebulizador 24 V** | Subir humedad relativa | 1 | |
| **Bomba de agua 12 V** (diafragma o sumergible) | Riego | 1 | |
| **Electroválvula 12 V** (1/2") | Riego por goteo por zonas | 1-2 | |
| Servomotor / motorreductor 12 V | Apertura de ventana cenital o cortina | 1 (opcional) | Con finales de carrera |
| Luz LED de crecimiento | Fotoperiodo / luz suplementaria | 1 (opcional) | |

---

## 4. Etapa de potencia y protección

| Componente | Cant. | Para qué |
|---|---|---|
| **Módulo relé 4 u 8 canales** con optoacoplador | 1 | Encendido/apagado de bomba, válvulas, humidificador |
| **SSR (relé de estado sólido) 25 A** con disipador | 1 | Para calefactor con PWM lento (sin desgaste mecánico) |
| **Módulo MOSFET PWM** (IRF520 / IRLZ44N o driver de 15 A) | 2 | Control de velocidad de ventiladores DC |
| **Fuente 12 V 10 A** (switching) | 1 | Alimenta actuadores |
| **Convertidor buck LM2596 / XL4015** (12 V → 5 V) | 2 | Alimenta ESP32 y sensores |
| Fusibles + portafusibles | Varios | Protección de cada línea |
| Diodos 1N4007 (flyback) | 5-10 | Protegen contra picos de bobinas/válvulas |
| Borneras, cable AWG 18/22, terminales | Lote | Cableado general |

**Seguridad:** la red en Bolivia es de **220 V**. Todo lo que toque corriente alterna debe ir en caja cerrada, con aislamiento y, si es posible, con interruptor diferencial. Si no tienes experiencia, usa actuadores de 12 V DC y evita manipular 220 V.

---

## 5. Cámara y visión artificial

| Opción | Resolución | Pros | Contras | Precio ref. |
|---|---|---|---|---|
| **ESP32-CAM (AI Thinker, OV2640)** | 2 MP | Barata, WiFi integrado, encaja en la arquitectura | Calidad limitada, difícil enfocar de cerca; insectos pequeños (trips, mosca blanca) casi no se ven | $8-12 |
| **ESP32-S3-CAM con OV5640** | 5 MP, autofocus | Mejor calidad que la anterior | Más cara, más difícil de conseguir | $15-25 |
| **Webcam USB 1080p con autofocus** (Logitech C920 o similar) | 2 MP, buena óptica | Excelente imagen, conectada directo al servidor | Requiere cable USB hasta la PC | $30-60 |
| **Cámara USB tipo endoscopio / microscopio** | Macro | Detalle de hojas e insectos | Campo de visión muy chico | $15-30 |

**Recomendación:** usar la **webcam USB 1080p** como cámara principal para el dataset y las pruebas, y la **ESP32-CAM** como demostración de nodo inalámbrico (útil para enfermedades visibles en hojas, como el tizón). Para plagas diminutas, lo práctico es fotografiar **trampas amarillas adhesivas** con cámara fija y buena luz, y detectar los insectos atrapados.

### Complementos de cámara

- Programador **FTDI** o placa base **ESP32-CAM-MB** (para cargar el código)
- Trípode flexible o soporte fijo
- **Iluminación LED difusa** (tira LED blanca o aro de luz) para fotos consistentes
- Trampas cromáticas amarillas/azules adhesivas
- Lente macro clip-on (opcional, para celular o webcam)

---

## 6. Servidor (procesamiento de imágenes e IA)

| Elemento | Mínimo | Recomendado |
|---|---|---|
| Procesador | Intel i5 / Ryzen 5 (4 núcleos) | i7 / Ryzen 7 |
| RAM | 8 GB | 16 GB |
| Almacenamiento | 256 GB SSD | 512 GB SSD |
| GPU | No necesaria para inferencia | NVIDIA GTX/RTX (acelera inferencia y entrenamiento) |
| Sistema | Windows 10/11 o Ubuntu con Docker | Ubuntu con Docker |

- **Router WiFi 2.4 GHz** dedicado (puede ser el de la casa o laboratorio) con buena cobertura hasta el invernadero. Si la señal es mala, agregar un repetidor o un **access point**.
- **UPS pequeño** (opcional) para que el servidor no se apague en cortes de luz durante pruebas largas.
- El entrenamiento se hace en **Google Colab** (gratis), por lo que no es necesario comprar GPU.

---

## 7. Estructura física y prototipo

| Elemento | Detalle |
|---|---|
| **Mini invernadero a escala** | Aprox. 1 x 1.5 x 1.5 m, estructura de PVC/madera/metal con agrofilm. Basta para validar el control |
| Macetas o cajones de cultivo | 6-12 plantas de papa (variedad local; consultar con INIAF o un agrónomo) |
| Sustrato y semilla certificada | |
| Tanque de agua (20-50 L) | Con manguera y goteros |
| **Caja estanca IP65** | Para la electrónica (con prensaestopas) |
| Termo-higrómetro de referencia confiable | Para **calibrar y validar** los sensores (muy valioso para la tesis) |

---

## 8. Herramientas y consumibles

- Multímetro
- Soldador y estaño
- Protoboards
- Placa perforada
- Cables Dupont
- Pinzas
- Destornilladores
- Termocontraíble
- Cinta aislante
- Bridas
- Silicona
- Cables USB
- Cable de extensión de alimentación

---

## 9. Resumen de presupuesto aproximado

| Bloque | Rango estimado |
|---|---|
| Control + sensores | $60-120 |
| Actuadores + potencia | $80-150 |
| Cámara + iluminación | $40-90 |
| Estructura e invernadero a escala | $80-200 |
| Servidor | Laptop/PC propia ($0 si ya la tienes) |
| **Total aproximado** | **$260-560** |

---

## 10. Lista mínima para arrancar (versión económica)

1. ESP32 DevKit x1
2. SHT31 x1 + DS18B20 x1 + suelo capacitivo x2 + BH1750 x1
3. Módulo relé 4 canales + 1 MOSFET + 1 ventilador 12 V + 1 bomba 12 V
4. Fuente 12 V 5 A + buck a 5 V
5. Webcam USB 1080p
6. Laptop propia como servidor

Con esto se prueba toda la cadena: sensar, controlar con PID y detectar. Luego se escala con calefactor, humidificador, CO₂ y ESP32-CAM.

---

## 11. Checklist de compra

### Control
- [ ] ESP32 DevKit V1 (x2)
- [ ] Placa de expansión con terminales
- [ ] (Alternativa) Arduino Mega 2560 + ESP-01/ESP8266

### Sensores
- [ ] SHT31 (x2)
- [ ] DHT22 / AM2302 (x1)
- [ ] Sensor capacitivo de humedad de suelo v1.2 (x3-4)
- [ ] DS18B20 sumergible (x2)
- [ ] BH1750 (x1)
- [ ] MH-Z19B o SCD30 (opcional)
- [ ] Sensor de nivel de agua / flotador
- [ ] Pantalla de radiación o caja ventilada
- [ ] Multiplexor I2C TCA9548A (opcional)

### Actuadores
- [ ] Ventilador/extractor 12 V (x2)
- [ ] Calefactor PTC 12/24 V
- [ ] Humidificador ultrasónico / nebulizador 24 V
- [ ] Bomba de agua 12 V
- [ ] Electroválvula 12 V 1/2" (x1-2)
- [ ] Servomotor / motorreductor 12 V (opcional)
- [ ] LED de crecimiento (opcional)

### Potencia y protección
- [ ] Módulo relé 4 u 8 canales
- [ ] SSR 25 A con disipador
- [ ] Módulos MOSFET PWM (x2)
- [ ] Fuente 12 V 10 A
- [ ] Convertidores buck LM2596/XL4015 (x2)
- [ ] Fusibles y portafusibles
- [ ] Diodos 1N4007
- [ ] Borneras, cable AWG 18/22, terminales

### Cámara
- [ ] Webcam USB 1080p con autofocus
- [ ] ESP32-CAM (AI Thinker) o ESP32-S3-CAM OV5640
- [ ] Programador FTDI o ESP32-CAM-MB
- [ ] Cámara endoscopio/microscopio (opcional)
- [ ] Trípode flexible / soporte fijo
- [ ] Iluminación LED difusa
- [ ] Trampas cromáticas amarillas/azules
- [ ] Lente macro clip-on (opcional)

### Servidor y red
- [ ] Laptop/PC (i5/Ryzen 5, 8-16 GB RAM, SSD)
- [ ] Router WiFi 2.4 GHz
- [ ] Repetidor o access point (si hace falta)
- [ ] UPS pequeño (opcional)

### Estructura y cultivo
- [ ] Estructura de mini invernadero + agrofilm
- [ ] Macetas o cajones (6-12 plantas)
- [ ] Sustrato y semilla certificada
- [ ] Tanque de agua 20-50 L + manguera + goteros
- [ ] Caja estanca IP65 con prensaestopas
- [ ] Termo-higrómetro de referencia

### Herramientas y consumibles
- [ ] Multímetro
- [ ] Soldador y estaño
- [ ] Protoboards y placa perforada
- [ ] Cables Dupont
- [ ] Pinzas y destornilladores
- [ ] Termocontraíble, cinta aislante, bridas, silicona
- [ ] Cables USB y extensión de alimentación
