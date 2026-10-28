#ifndef CONFIG_INVERNADERO_H
#define CONFIG_INVERNADERO_H

// ==============================================================================
// 1. ASIGNACIÓN FÍSICA DE PINES (ESP32 DevKit V1 30 pines)
// ==============================================================================
#define PIN_I2C_SDA         21  // Bus I2C para SHT31 y BH1750
#define PIN_I2C_SCL         22  // Bus I2C para SHT31 y BH1750
#define PIN_ONEWIRE_DS18B20  4  // Bus OneWire para DS18B20 (Temperatura suelo)
#define PIN_ADC_SUELO       34  // Entrada analógica ADC1_CH6 (Humedad suelo)
#define PIN_DIGITAL_FLOTADOR 35  // Entrada digital con pull-up externa (Nivel agua)

#define PIN_SSR_CALEFACTOR  23  // Salida digital SSR 220V (PWM proporcional a tiempo)
#define PIN_PWM_EXTRACTOR   19  // Salida PWM 25 kHz hacia Gate de MOSFET 12V
#define PIN_RELE_HUMIDIF    18  // Canal 1 módulo relé (Active-LOW)
#define PIN_RELE_BOMBA      26  // Canal 2 módulo relé (Active-LOW)
#define PIN_LED_ESTADO       2  // LED onboard para diagnóstico y heartbeat

// ==============================================================================
// 2. PARÁMETROS DE PWM Y TEMPORIZACIÓN
// ==============================================================================
#define PWM_LEDC_CHANNEL     0
#define PWM_LEDC_FREQ_HZ 25000  // 25 kHz (frecuencia ultrasónica sin zumbido audible)
#define PWM_LEDC_RESOLUTION  8  // Resolución de 8 bits (rango 0 a 255)

#define SSR_VENTANA_TIEMPO_MS 2000  // Ventana de 2.0 s para modulación de tiempo del SSR
#define PERIODO_PID_MS         100  // Frecuencia del lazo de control local = 10 Hz
#define PERIODO_TELEMETRIA_MS 1000  // Publicación MQTT a 1 Hz
#define WDT_TIMEOUT_SECONDS     10  // Hardware Watchdog de 10 segundos

// ==============================================================================
// 3. PARÁMETROS PID Y LÍMITES POR DEFECTO (CULTIVO DE PAPA - LA PAZ)
// ==============================================================================
#define DEFAULT_SETPOINT_TEMP 20.0f  // °C diurno óptimo para papa
#define DEFAULT_SETPOINT_HUM  75.0f  // % HR óptimo
#define DEFAULT_KP             6.5f  // Ganancia proporcional estimada
#define DEFAULT_KI             0.08f // Ganancia integral
#define DEFAULT_KD             1.2f  // Ganancia derivativa

#define PID_DEADBAND_TEMP      0.25f // Banda muerta de ±0.25 °C para reposo de actuadores
#define PID_CV_MIN          -100.0f // Máxima extracción / enfriamiento
#define PID_CV_MAX           100.0f // Máxima calefacción

// Calibración Sensor Capacitivo de Suelo v1.2 (ADC 12 bits: 0 a 4095)
#define ADC_SUELO_AIRE_SECO   3100
#define ADC_SUELO_AGUA_SAT    1450

// ==============================================================================
// 4. CREDENCIALES DE RED Y CONFIGURACIÓN MQTT
// ==============================================================================
#define WIFI_SSID             "Invernadero_WiFi_2.4G"
#define WIFI_PASSWORD         "TesisPapa2026!"
#define MQTT_BROKER_IP        "192.168.1.100"  // IP de la laptop/servidor en la red local
#define MQTT_PORT             1883
#define MQTT_USERNAME         "esp32_nodo"
#define MQTT_PASSWORD         "Esp32MicroclimaPass2026!"
#define TOPIC_CONTROL_ESTADO   "invernadero/control/estado"
#define PIN_FLOTADOR_AGUA_OK   LOW  // Contacto cerrado a GND cuando hay agua
#define MQTT_CLIENT_ID        "esp32_invernadero_nodo01"

// Tópicos MQTT según especificación Fase 0
#define TOPIC_TELEMETRIA_CLIMA "invernadero/telemetria/microclima"
#define TOPIC_TELEMETRIA_PID   "invernadero/telemetria/pid"
#define TOPIC_CONTROL_SP       "invernadero/control/setpoints"
#define TOPIC_CONTROL_GANANCIAS "invernadero/control/ganancias"
#define TOPIC_CONTROL_MODO     "invernadero/control/modo"
#define TOPIC_ALERTA           "invernadero/alerta"

#endif // CONFIG_INVERNADERO_H
