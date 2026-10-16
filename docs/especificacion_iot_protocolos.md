# Especificación de Arquitectura de Datos, Protocolo MQTT y Esquemas de Base de Datos

> **Proyecto:** Prototipo de Sistema Integrado IoT–PID–IA para la Regulación Microclimática y Detección Temprana de Plagas en el Cultivo de Papa bajo Invernadero (La Paz, Bolivia).  
> **Fase:** 0 – Estructura del Repositorio y Definición de Protocolos.

---

## 1. Topología y Arquitectura MQTT

El sistema implementa un modelo desacoplado basado en publicación/suscripción (*Publish/Subscribe*) utilizando el protocolo **MQTT v3.1.1/v5** sobre TCP (puerto 1883) y WebSockets (puerto 9001).

```
   ┌────────────────────────────────────────────────────────┐
   │                  ESP32 (Nodo Local)                    │
   └─────────────┬────────────────────────────▲─────────────┘
                 │ Telemetría                 │ Setpoints / Comandos
                 │ (QoS 0/1)                  │ (QoS 1, Retain)
                 ▼                            │
   ┌──────────────────────────────────────────┴─────────────┐
   │             Broker MQTT (Eclipse Mosquitto)            │
   └───────┬────────────────────┬────────────────────┬──────┘
           │                    │                    │
           ▼                    ▼                    ▼
   ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
   │   Telegraf    │    │ FastAPI (IA)  │    │  Web/Grafana  │
   │ (Ingesta DB)  │    │(Toma Decisión)│    │ (Monitoreo)   │
   └───────┬───────┘    └───────┬───────┘    └───────────────┘
           ▼                    │
   ┌───────────────┐            │ Ajuste de Setpoints
   │ InfluxDB v2   │◄───────────┘ (Lazo Externo)
   └───────────────┘
```

---

## 2. Jerarquía de Tópicos MQTT

Todos los tópicos utilizan un prefijo raíz unificado `invernadero/`.

| Tópico MQTT | Emisor | Receptores | QoS | Retained | Propósito |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `invernadero/telemetria/microclima` | ESP32 | Telegraf, FastAPI, Web | 1 | No | Mediciones ambientales brutas y filtradas (temp, hum, luz, etc.) a 1–2 Hz. |
| `invernadero/telemetria/pid` | ESP32 | Telegraf, FastAPI, Web | 1 | No | Variables de estado del control PID (SP, PV, CV, P, I, D, PWM) a 1–2 Hz. |
| `invernadero/telemetria/actuadores` | ESP32 | Telegraf, Web | 1 | No | Estados discretos y porcentuales de actuadores (bomba, ventilador, SSR). |
| `invernadero/control/setpoint` | FastAPI / Web | ESP32 | 1 | Sí | Modificación de valores deseados (Temperatura, Humedad) desde lazo IA o usuario. |
| `invernadero/control/ganancias` | FastAPI / Web | ESP32 | 1 | Sí | Ajuste dinámico de parámetros PID ($K_p, K_i, K_d$). |
| `invernadero/control/modo` | Web / Asesor | ESP32 | 1 | Sí | Cambio de modo operativo: `AUTO`, `MANUAL`, `AUTOTUNE`, `SAFE`. |
| `invernadero/vision/deteccion` | FastAPI (Worker)| Telegraf, Web, SQLite | 1 | No | Resultados de inferencia YOLO+SAHI (clases, coordenadas, conteo, severidad). |
| `invernadero/riesgo/indice` | FastAPI (Worker)| Telegraf, Web, Bot | 1 | Sí | Cálculo integrado de riesgo epidemiológico (0.0 a 1.0) y recomendaciones. |
| `invernadero/alerta` | ESP32 / Server | Bot Telegram, Web | 2 | No | Eventos críticos de seguridad (helada inminente, sobrecalentamiento, falla de sensor). |

---

## 3. Esquemas de Mensajes JSON

Todos los mensajes se serializan en cadenas JSON UTF-8 compactas, empleando notación técnica estándar en minúsculas y unidades del Sistema Internacional.

### 3.1. Telemetría Microclimática (`invernadero/telemetria/microclima`)

```json
{
  "nodo_id": "esp32_invernadero_01",
  "zona": "zona_a_central",
  "timestamp_ms": 1792160400000,
  "temp_aire": 18.42,
  "hum_aire": 72.85,
  "temp_suelo": 15.10,
  "hum_suelo": 64.30,
  "luz_lux": 28450.0,
  "co2_ppm": 420.0,
  "vpd_kpa": 0.58,
  "punto_rocio": 13.35,
  "sensores_ok": true
}
```

*Definición de campos:*
- `nodo_id` (string): Identificador único del nodo de hardware.
- `temp_aire` (float, °C): Temperatura del aire medida por SHT31 tras filtro EMA. Rango válido: $-5.0$ a $50.0$.
- `hum_aire` (float, % HR): Humedad relativa del aire medida por SHT31. Rango válido: $0.0$ a $100.0$.
- `temp_suelo` (float, °C): Temperatura edáfica medida por DS18B20 sumergible.
- `hum_suelo` (float, %): Humedad volumétrica/sustrato calibrada (0 = seco al aire, 100 = saturado).
- `luz_lux` (float, Lux): Iluminancia fotosintética por BH1750.
- `vpd_kpa` (float, kPa): Déficit de Presión de Vapor calculado: $VPD = VP_{sat} \times (1 - HR/100)$.
- `punto_rocio` (float, °C): Temperatura de rocío calculada por aproximación de Magnus.

### 3.2. Telemetría de Control PID (`invernadero/telemetria/pid`)

```json
{
  "nodo_id": "esp32_invernadero_01",
  "timestamp_ms": 1792160400000,
  "variable": "TEMPERATURA",
  "sp_temp": 20.00,
  "pv_temp": 18.42,
  "error": 1.58,
  "cv_salida": 42.50,
  "termino_p": 25.20,
  "termino_i": 17.30,
  "termino_d": 0.00,
  "modo": "AUTO",
  "pwm_calefactor": 42.50,
  "pwm_extractor": 0.00,
  "antiwindup_activo": false
}
```

*Definición de campos:*
- `sp_temp` (float, °C): Setpoint objetivo actual.
- `pv_temp` (float, °C): Variable de proceso (Process Variable) medida y filtrada.
- `error` (float, °C): Diferencia $e(t) = SP - PV$.
- `cv_salida` (float, %): Variable de control (Control Variable) normalizada de $-100.0$ a $+100.0\%$ (Split-range: $> 0$ calefacción, $< 0$ extracción/enfriamiento).
- `pwm_calefactor` (float, %): Ciclo de trabajo efectivo asignado al SSR por modulación de ventana temporal.
- `antiwindup_activo` (boolean): Flag que indica si la acción integral ha sido acotada por saturación de actuador.

### 3.3. Comandos de Control de Setpoints (`invernadero/control/setpoint`)

```json
{
  "origen": "IA_SUPERVISORA",
  "timestamp_ms": 1792160400000,
  "sp_temp": 19.5,
  "sp_hum": 70.0,
  "justificacion": "Reduccion de setpoint termico para abatir condensacion foliar preventiva"
}
```

### 3.4. Detección de Visión Artificial (`invernadero/vision/deteccion`)

```json
{
  "nodo_camara": "cam_webcam_01",
  "timestamp_ms": 1792160400000,
  "tipo_origen": "TRAMPA_AMARILLA",
  "imagen_id": "img_20261016_143000.jpg",
  "tiempo_inferencia_ms": 184.5,
  "sahi_activo": true,
  "total_plagas": 3,
  "detecciones": [
    {
      "clase": "pulgon",
      "confianza": 0.91,
      "bbox": [140, 210, 168, 245]
    },
    {
      "clase": "mosca_minadora",
      "confianza": 0.86,
      "bbox": [510, 320, 542, 358]
    }
  ],
  "severidad_foliar_pct": 0.0
}
```

### 3.5. Índice de Riesgo Epidemiológico (`invernadero/riesgo/indice`)

```json
{
  "timestamp_ms": 1792160400000,
  "enfermedad": "tizon_tardio_phytophthora",
  "indice_riesgo": 0.78,
  "nivel_alerta": "ALTO",
  "horas_hoja_humeda_acumuladas": 7.5,
  "factores_principales": {
    "humedad_elevada": 0.45,
    "temperatura_optima_espora": 0.35,
    "presencia_vector_vision": 0.20
  },
  "accion_recomendada": "Activar ventilacion forzada para descender humedad bajo 70% e inspeccionar cuadrante A"
}
```

---

## 4. Esquemas de Bases de Datos

### 4.1. InfluxDB v2 (Series de Tiempo Microclimáticas y Control)

- **Organización:** `agri_iot_tesis`
- **Bucket Principal:** `invernadero_data`
- **Política de Retención (RP):** Infinita para entorno experimental / tesis (o 90 días en producción).

#### Estructura de Medición 1: `clima`
- **Tags:**
  - `nodo_id`: ID del dispositivo emisor (`esp32_invernadero_01`).
  - `zona`: Sector dentro del invernadero (`central`, `perimetral`, `norte`).
- **Fields:**
  - `temp_aire` (float, °C)
  - `hum_aire` (float, %)
  - `temp_suelo` (float, °C)
  - `hum_suelo` (float, %)
  - `luz_lux` (float, Lux)
  - `co2_ppm` (float, ppm)
  - `vpd_kpa` (float, kPa)
  - `punto_rocio` (float, °C)

#### Estructura de Medición 2: `pid_control`
- **Tags:**
  - `nodo_id`: ID del dispositivo.
  - `variable`: `temperatura` / `humedad`.
  - `modo`: `AUTO`, `MANUAL`, `AUTOTUNE`.
- **Fields:**
  - `sp` (float)
  - `pv` (float)
  - `error` (float)
  - `cv` (float, -100 a +100%)
  - `p_term` (float)
  - `i_term` (float)
  - `d_term` (float)
  - `pwm_calefactor` (float, 0 a 100%)
  - `pwm_extractor` (float, 0 a 100%)

#### Estructura de Medición 3: `riesgo_epidemiologico`
- **Tags:**
  - `patogeno`: `phytophthora_infestans`, `alternaria_solani`.
  - `nivel`: `BAJO`, `MEDIO`, `ALTO`, `CRITICO`.
- **Fields:**
  - `score_riesgo` (float, 0.0 a 1.0)
  - `horas_hoja_humeda` (float, horas continuas con HR > 90%)

---

### 4.2. SQLite (Datos Relacionales, Visión, Alarmas y Ensayos)

Ubicación del archivo: `data/invernadero_relacional.db`  
Definido e inicializado desde [schemas.sql](file:///home/rodrigo/Desktop/IOTtesis/server/app/models/schemas.sql).

- **`nodos_sensores`**: Registro de hardware, direcciones IP, MAC y versiones de firmware.
- **`detecciones_vision`**: Historial de cada inferencia con coordenadas delimitadoras (bounding boxes), clases de insectos y porcentaje de área afectada.
- **`eventos_alarmas`**: Bitácora de incidentes y disparo de protecciones.
- **`auditoria_control_pid`**: Trazabilidad completa de modificaciones en setpoints y ganancias, indispensable para validar ante el jurado quién originó cada cambio (operador o IA).
- **`experimentos_ensayos`**: Metadatos de los ensayos experimentales E1 a E8 para cálculo de métricas agregadas ($IAE, ITAE, M_p, t_s$).
