// ==============================================================================
// main.cpp - Firmware del Nodo ESP32: Control PID Local y Conectividad IoT
// Proyecto: Tesis IoT-PID-IA Papa bajo Invernadero (La Paz, Bolivia)
// ==============================================================================

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <SHT31.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <BH1750.h>
#include <esp_task_wdt.h>
#include "config_invernadero.h"

// ------------------------------------------------------------------------------
// Instancias de Hardware y Sensores
// ------------------------------------------------------------------------------
WiFiClient espClient;
PubSubClient mqttClient(espClient);
SHT31 sht31;
OneWire oneWireBus(PIN_ONEWIRE_DS18B20);
DallasTemperature sensorSuelo(&oneWireBus);
BH1750 luxometro;

// ------------------------------------------------------------------------------
// Variables de Estado del Proceso y Filtros
// ------------------------------------------------------------------------------
float temp_aire_raw = 18.0f, temp_aire_filtrada = 18.0f;
float hum_aire_raw = 70.0f, hum_aire_filtrada = 70.0f;
float temp_suelo_filtrada = 16.0f;
float hum_suelo_pct = 60.0f;
float luz_lux_val = 0.0f;
float vpd_kpa = 0.6f;
float punto_rocio = 12.0f;
bool sensores_ok = true;

// Filtro EMA (Exponential Moving Average): y[k] = alpha * x[k] + (1 - alpha) * y[k-1]
const float EMA_ALPHA_TEMP = 0.15f;
const float EMA_ALPHA_HUM = 0.15f;
const float EMA_ALPHA_SUELO = 0.10f;

// Filtro Hampel simplificado para rechazo de picos atípicos (ventana de 3 muestras)
float buffer_temp[3] = {18.0f, 18.0f, 18.0f};
uint8_t buffer_idx = 0;

// ------------------------------------------------------------------------------
// Variables del Controlador PID (Lazo Interno Rápido)
// ------------------------------------------------------------------------------
float setpoint_temperatura = DEFAULT_SETPOINT_TEMP;
float setpoint_humedad = DEFAULT_SETPOINT_HUM;
float kp = DEFAULT_KP;
float ki = DEFAULT_KI;
float kd = DEFAULT_KD;

float error_actual = 0.0f;
float termino_p = 0.0f;
float termino_i = 0.0f;
float termino_d = 0.0f;
float cv_salida = 0.0f;
float pv_previa = 18.0f; // Para derivada sobre la medida (anti-derivative kick)
bool antiwindup_activo = false;
String modo_operativo = "AUTO"; // "AUTO", "MANUAL", "AUTOTUNE", "SAFE"

// ------------------------------------------------------------------------------
// Temporizadores y Ventanas de Modulación
// ------------------------------------------------------------------------------
unsigned long t_ultimo_pid = 0;
unsigned long t_ultimo_telemetria = 0;
unsigned long t_inicio_ventana_ssr = 0;
unsigned long t_ultimo_intento_mqtt = 0;
unsigned long t_ultimo_heartbeat = 0;
bool led_heartbeat_estado = false;

// ==============================================================================
// 1. FUNCIONES PSICROMÉTRICAS Y FILTRADO DE SENSORES
// ==============================================================================

float aplicar_filtro_hampel(float nueva_muestra) {
    buffer_temp[buffer_idx] = nueva_muestra;
    buffer_idx = (buffer_idx + 1) % 3;

    // Calcular mediana de 3 muestras
    float a = buffer_temp[0], b = buffer_temp[1], c = buffer_temp[2];
    float mediana = (a > b) ? ((b > c) ? b : ((a > c) ? c : a)) : ((a > c) ? a : ((b > c) ? c : b));

    // Si la muestra difiere más de 3.5 °C de la mediana, se descarta el pico y se usa la mediana
    if (abs(nueva_muestra - mediana) > 3.5f) {
        return mediana;
    }
    return nueva_muestra;
}

float calcular_vpd(float temp, float hum) {
    // Ecuación de Tetens para presión de vapor saturada (kPa)
    float vp_sat = 0.61078f * exp((17.27f * temp) / (temp + 237.3f));
    float vp_act = vp_sat * (hum / 100.0f);
    float vpd = vp_sat - vp_act;
    return (vpd < 0.0f) ? 0.0f : vpd;
}

float calcular_punto_rocio(float temp, float hum) {
    // Ecuación de Magnus
    const float a = 17.27f;
    const float b = 237.7f;
    float hum_acotada = (hum < 1.0f) ? 1.0f : hum;
    float alpha = ((a * temp) / (b + temp)) + log(hum_acotada / 100.0f);
    return (b * alpha) / (a - alpha);
}

void leer_sensores() {
    // 1. SHT31 (Temperatura y Humedad del aire por I2C)
    if (sht31.read()) {
        temp_aire_raw = sht31.getTemperature();
        hum_aire_raw = sht31.getHumidity();

        // Aplicar filtro Hampel seguido de filtro EMA
        float temp_sin_picos = aplicar_filtro_hampel(temp_aire_raw);
        temp_aire_filtrada = (EMA_ALPHA_TEMP * temp_sin_picos) + ((1.0f - EMA_ALPHA_TEMP) * temp_aire_filtrada);
        hum_aire_filtrada = (EMA_ALPHA_HUM * hum_aire_raw) + ((1.0f - EMA_ALPHA_HUM) * hum_aire_filtrada);
        sensores_ok = true;
    } else {
        sensores_ok = false;
        Serial.println(F("[ERROR] Falla de lectura en sensor SHT31"));
    }

    // 2. DS18B20 (Temperatura edáfica en suelo)
    sensorSuelo.requestTemperatures();
    float temp_suelo_raw = sensorSuelo.getTempCByIndex(0);
    if (temp_suelo_raw > -50.0f && temp_suelo_raw < 80.0f) {
        temp_suelo_filtrada = (EMA_ALPHA_SUELO * temp_suelo_raw) + ((1.0f - EMA_ALPHA_SUELO) * temp_suelo_filtrada);
    }

    // 3. Sensor capacitivo de humedad de suelo (ADC1_CH6)
    int adc_suelo = analogRead(PIN_ADC_SUELO);
    // Mapeo lineal restringido entre calibración de aire seco y saturación de agua
    float hum_calc = map(adc_suelo, ADC_SUELO_AIRE_SECO, ADC_SUELO_AGUA_SAT, 0, 100);
    hum_suelo_pct = constrain(hum_calc, 0.0f, 100.0f);

    // 4. BH1750 (Luxómetro I2C)
    luz_lux_val = luxometro.readLightLevel();

    // 5. Cálculos psicrométricos derivados
    vpd_kpa = calcular_vpd(temp_aire_filtrada, hum_aire_filtrada);
    punto_rocio = calcular_punto_rocio(temp_aire_filtrada, hum_aire_filtrada);
}

// ==============================================================================
// 2. CONTROLADOR PID DISCRETO CON SPLIT-RANGE Y ANTI-WINDUP
// ==============================================================================

void ejecutar_control_pid() {
    float dt = PERIODO_PID_MS / 1000.0f; // dt = 0.1 s
    error_actual = setpoint_temperatura - temp_aire_filtrada;

    // Aplicación de banda muerta para evitar oscilación innecesaria de actuadores
    if (abs(error_actual) < PID_DEADBAND_TEMP) {
        error_actual = 0.0f;
    }

    // 1. Término Proporcional
    termino_p = kp * error_actual;

    // 2. Término Derivativo sobre la Medida (Anti-Derivative Kick)
    // d(error)/dt = d(SP - PV)/dt = - d(PV)/dt cuando SP es constante
    float derivada_pv = (temp_aire_filtrada - pv_previa) / dt;
    termino_d = -kd * derivada_pv;
    pv_previa = temp_aire_filtrada;

    // 3. Término Integral con Anti-Windup (Clamping Condicional)
    // Solo integrar si la salida no está saturada o si el error empuja hacia la desaturación
    bool saturado_alto = (cv_salida >= PID_CV_MAX && error_actual > 0);
    bool saturado_bajo = (cv_salida <= PID_CV_MIN && error_actual < 0);

    if (!saturado_alto && !saturado_bajo) {
        termino_i += ki * error_actual * dt;
        antiwindup_activo = false;
    } else {
        antiwindup_activo = true;
    }
    // Acotar el término integral a los límites de la variable de control
    termino_i = constrain(termino_i, PID_CV_MIN, PID_CV_MAX);

    // Salida no acotada
    float cv_tentativa = termino_p + termino_i + termino_d;

    // Saturación de la variable de control [-100% a +100%]
    cv_salida = constrain(cv_tentativa, PID_CV_MIN, PID_CV_MAX);

    // ==========================================================================
    // Asignación de Actuadores (Split-Range)
    // ==========================================================================
    float pwm_calefactor = 0.0f;
    float pwm_extractor = 0.0f;

    if (cv_salida > 0.0f) {
        // Modo Calefacción: El calefactor toma la salida positiva, extractor apagado
        pwm_calefactor = cv_salida;
        pwm_extractor = 0.0f;
    } else if (cv_salida < 0.0f) {
        // Modo Enfriamiento / Extracción: El extractor toma la magnitud negativa
        pwm_calefactor = 0.0f;
        pwm_extractor = abs(cv_salida);
    } else {
        pwm_calefactor = 0.0f;
        pwm_extractor = 0.0f;
    }

    // A. Extractor PWM (LEDC a 25 kHz, 8 bits: 0 a 255)
    uint32_t duty_extractor = (uint32_t)((pwm_extractor / 100.0f) * 255.0f);
    ledcWrite(PWM_LEDC_CHANNEL, duty_extractor);

    // B. Calefactor SSR (Modulación por Ancho de Pulso en Ventana de Tiempo)
    unsigned long t_actual = millis();
    if (t_actual - t_inicio_ventana_ssr >= SSR_VENTANA_TIEMPO_MS) {
        t_inicio_ventana_ssr = t_actual;
    }

    unsigned long tiempo_encendido_ssr = (unsigned long)((pwm_calefactor / 100.0f) * SSR_VENTANA_TIEMPO_MS);
    if ((t_actual - t_inicio_ventana_ssr) < tiempo_encendido_ssr) {
        digitalWrite(PIN_SSR_CALEFACTOR, HIGH); // SSR Encendido
    } else {
        digitalWrite(PIN_SSR_CALEFACTOR, LOW);  // SSR Apagado
    }
}

// ==============================================================================
// 3. COMUNICACIÓN MQTT, CALLBACKS Y RECONEXIÓN
// ==============================================================================

void callback_mqtt(char* topic, byte* payload, unsigned int length) {
    char mensaje_str[length + 1];
    memcpy(mensaje_str, payload, length);
    mensaje_str[length] = '\0';

    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, mensaje_str);

    if (error) {
        Serial.print(F("[ERROR] JSON inválido en tópico: "));
        Serial.println(topic);
        return;
    }

    String topico_recibido = String(topic);

    // 1. Recepción de nuevo Setpoint desde lazo externo (IA o Web)
    if (topico_recibido == TOPIC_CONTROL_SP) {
        if (doc.containsKey("sp_temp")) {
            setpoint_temperatura = doc["sp_temp"].as<float>();
            Serial.print(F("[MQTT] Setpoint Temp actualizado: "));
            Serial.print(setpoint_temperatura);
            Serial.println(F(" °C"));
        }
        if (doc.containsKey("sp_hum")) {
            setpoint_humedad = doc["sp_hum"].as<float>();
            Serial.print(F("[MQTT] Setpoint Humedad actualizado: "));
            Serial.println(setpoint_humedad);
        }
    }
    // 2. Recepción de nuevas Ganancias PID
    else if (topico_recibido == TOPIC_CONTROL_GANANCIAS) {
        if (doc.containsKey("kp")) kp = doc["kp"].as<float>();
        if (doc.containsKey("ki")) ki = doc["ki"].as<float>();
        if (doc.containsKey("kd")) kd = doc["kd"].as<float>();
        Serial.printf("[MQTT] Ganancias actualizadas -> Kp: %.2f, Ki: %.4f, Kd: %.2f\n", kp, ki, kd);
    }
    // 3. Recepción de Modo Operativo
    else if (topico_recibido == TOPIC_CONTROL_MODO) {
        if (doc.containsKey("modo")) {
            modo_operativo = doc["modo"].as<String>();
            Serial.printf("[MQTT] Modo operativo fijado a: %s\n", modo_operativo.c_str());
        }
    }
}

void reconectar_mqtt() {
    if (mqttClient.connected()) return;

    unsigned long t_ahora = millis();
    // Reintentar conexión cada 5 segundos de forma no bloqueante
    if (t_ahora - t_ultimo_intento_mqtt > 5000) {
        t_ultimo_intento_mqtt = t_ahora;
        Serial.print(F("[*] Conectando a Broker MQTT... "));

        if (mqttClient.connect(MQTT_CLIENT_ID)) {
            Serial.println(F("Conectado con éxito."));
            mqttClient.subscribe(TOPIC_CONTROL_SP);
            mqttClient.subscribe(TOPIC_CONTROL_GANANCIAS);
            mqttClient.subscribe(TOPIC_CONTROL_MODO);
        } else {
            Serial.print(F("Fallo, rc="));
            Serial.print(mqttClient.state());
            Serial.println(F(". El PID continúa operando en modo local seguro."));
        }
    }
}

void publicar_telemetria() {
    if (!mqttClient.connected()) return;

    // 1. Mensaje de Microclima
    StaticJsonDocument<512> doc_clima;
    doc_clima["nodo_id"] = MQTT_CLIENT_ID;
    doc_clima["zona"] = "zona_a_central";
    doc_clima["timestamp_ms"] = (uint64_t)millis();
    doc_clima["temp_aire"] = round(temp_aire_filtrada * 100.0f) / 100.0f;
    doc_clima["hum_aire"] = round(hum_aire_filtrada * 100.0f) / 100.0f;
    doc_clima["temp_suelo"] = round(temp_suelo_filtrada * 100.0f) / 100.0f;
    doc_clima["hum_suelo"] = round(hum_suelo_pct * 10.0f) / 10.0f;
    doc_clima["luz_lux"] = round(luz_lux_val);
    doc_clima["vpd_kpa"] = round(vpd_kpa * 1000.0f) / 1000.0f;
    doc_clima["punto_rocio"] = round(punto_rocio * 100.0f) / 100.0f;
    doc_clima["sensores_ok"] = sensores_ok;

    char buffer_clima[512];
    serializeJson(doc_clima, buffer_clima);
    mqttClient.publish(TOPIC_TELEMETRIA_CLIMA, buffer_clima);

    // 2. Mensaje de Control PID
    StaticJsonDocument<512> doc_pid;
    doc_pid["nodo_id"] = MQTT_CLIENT_ID;
    doc_pid["timestamp_ms"] = (uint64_t)millis();
    doc_pid["variable"] = "TEMPERATURA";
    doc_pid["sp_temp"] = setpoint_temperatura;
    doc_pid["pv_temp"] = round(temp_aire_filtrada * 100.0f) / 100.0f;
    doc_pid["error"] = round(error_actual * 100.0f) / 100.0f;
    doc_pid["cv_salida"] = round(cv_salida * 10.0f) / 10.0f;
    doc_pid["termino_p"] = round(termino_p * 10.0f) / 10.0f;
    doc_pid["termino_i"] = round(termino_i * 10.0f) / 10.0f;
    doc_pid["termino_d"] = round(termino_d * 10.0f) / 10.0f;
    doc_pid["modo"] = modo_operativo;
    doc_pid["pwm_calefactor"] = (cv_salida > 0.0f) ? round(cv_salida * 10.0f) / 10.0f : 0.0f;
    doc_pid["pwm_extractor"] = (cv_salida < 0.0f) ? round(abs(cv_salida) * 10.0f) / 10.0f : 0.0f;
    doc_pid["antiwindup_activo"] = antiwindup_activo;

    char buffer_pid[512];
    serializeJson(doc_pid, buffer_pid);
    mqttClient.publish(TOPIC_TELEMETRIA_PID, buffer_pid);
}

// ==============================================================================
// 4. SETUP Y BUCLE PRINCIPAL (SUPERLOOP CON WDT)
// ==============================================================================

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println(F("\n========================================================"));
    Serial.println(F("ESP32 Control Invernadero Papa - Tesis La Paz 2026"));
    Serial.println(F("========================================================"));

    // Inicialización de Pines
    pinMode(PIN_LED_ESTADO, OUTPUT);
    pinMode(PIN_SSR_CALEFACTOR, OUTPUT);
    pinMode(PIN_RELE_HUMIDIF, OUTPUT);
    pinMode(PIN_RELE_BOMBA, OUTPUT);
    pinMode(PIN_ADC_SUELO, INPUT);
    pinMode(PIN_DIGITAL_FLOTADOR, INPUT_PULLUP);

    // Estados seguros iniciales (todo apagado)
    digitalWrite(PIN_SSR_CALEFACTOR, LOW);
    digitalWrite(PIN_RELE_HUMIDIF, HIGH); // Relé apagado (Active-LOW)
    digitalWrite(PIN_RELE_BOMBA, HIGH);   // Relé apagado (Active-LOW)

    // Configurar canal PWM LEDC para Extractor (25 kHz, 8 bits)
    ledcSetup(PWM_LEDC_CHANNEL, PWM_LEDC_FREQ_HZ, PWM_LEDC_RESOLUTION);
    ledcAttachPin(PIN_PWM_EXTRACTOR, PWM_LEDC_CHANNEL);
    ledcWrite(PWM_LEDC_CHANNEL, 0); // Extractor apagado

    // Inicializar buses I2C y OneWire
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    sht31.begin(0x44);
    sensorSuelo.begin();
    luxometro.begin(BH1750::CONTINUOUS_HIGH_RES_MODE);

    // Conexión WiFi
    Serial.print(F("[*] Conectando a WiFi: "));
    Serial.println(WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    // Configuración MQTT
    mqttClient.setServer(MQTT_BROKER_IP, MQTT_PORT);
    mqttClient.setCallback(callback_mqtt);

    // Inicialización del Hardware Watchdog Timer (WDT)
    esp_task_wdt_init(WDT_TIMEOUT_SECONDS, true); // true = reinicio de hardware ante timeout
    esp_task_wdt_add(NULL);                      // Agregar hilo principal al WDT

    t_inicio_ventana_ssr = millis();
    Serial.println(F("[✔] Inicialización completada. Iniciando lazo de control local a 10 Hz."));
}

void loop() {
    // 1. Refrescar el Watchdog Timer
    esp_task_wdt_reset();

    // 2. Gestión de Conectividad de Red
    if (WiFi.status() == WL_CONNECTED) {
        reconectar_mqtt();
        mqttClient.loop();
    }

    // 3. Ejecución Periódica de Sensores y Lazo PID (10 Hz = cada 100 ms)
    unsigned long t_actual = millis();
    if (t_actual - t_ultimo_pid >= PERIODO_PID_MS) {
        t_ultimo_pid = t_actual;
        leer_sensores();
        ejecutar_control_pid();
    }

    // 4. Publicación Periódica de Telemetría (1 Hz = cada 1000 ms)
    if (t_actual - t_ultimo_telemetria >= PERIODO_TELEMETRIA_MS) {
        t_ultimo_telemetria = t_actual;
        publicar_telemetria();
    }

    // 5. Heartbeat LED de Diagnóstico
    if (t_actual - t_ultimo_heartbeat >= 500) {
        t_ultimo_heartbeat = t_actual;
        led_heartbeat_estado = !led_heartbeat_estado;
        digitalWrite(PIN_LED_ESTADO, led_heartbeat_estado ? HIGH : LOW);
    }
}
