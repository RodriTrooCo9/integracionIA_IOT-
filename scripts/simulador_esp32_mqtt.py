#!/usr/bin/env python3
"""
simulador_esp32_mqtt.py
Simulador de nodo ESP32 con lazo térmico FOPDT para pruebas sin hardware
Proyecto: Tesis IoT-PID-IA Papa Invernadero
"""

import time
import math
import json
import random
import os
import paho.mqtt.client as mqtt

# Parámetros del Broker MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USERNAME", "esp32_nodo")
MQTT_PASS = os.getenv("MQTT_PASSWORD", "Esp32MicroclimaPass2026!")
CLIENT_ID = "simulador_esp32_la_paz"

# Tópicos
TOPIC_TELEMETRIA_CLIMA = "invernadero/telemetria/microclima"
TOPIC_TELEMETRIA_PID = "invernadero/telemetria/pid"
TOPIC_CONTROL_SP = "invernadero/control/setpoints"
TOPIC_CONTROL_MODO = "invernadero/control/modo"

# Variables de Estado del Proceso (FOPDT Térmico)
temperatura_actual = 14.5  # Noche fría típica en La Paz
humedad_actual = 78.0
setpoint_temp = 20.0
modo_operativo = "AUTO"

# Parámetros FOPDT para simular la inercia del invernadero
# dT/dt = ( - (T - T_amb) + K * CV ) / tau
K_ganancia = 0.15          # °C por % de calefactor
tau_constante_tiempo = 45.0 # segundos (acelerado para pruebas)
temp_ambiente_ext = 8.0    # Exterior frío en La Paz

# Parámetros PID discretos
kp = 6.0
ki = 0.08
kd = 1.2
error_acumulado = 0.0
error_previo = 0.0
dt = 1.0  # periodo de muestreo en segundos

def calcular_vpd(temp, hum):
    """Calcula el Déficit de Presión de Vapor en kPa."""
    vp_sat = 0.61078 * math.exp((17.27 * temp) / (temp + 237.3))
    vp_act = vp_sat * (hum / 100.0)
    return round(vp_sat - vp_act, 3)

def calcular_punto_rocio(temp, hum):
    """Aproximación de Magnus para punto de rocío en °C."""
    a = 17.27
    b = 237.7
    alpha = ((a * temp) / (b + temp)) + math.log(max(hum, 1.0) / 100.0)
    return round((b * alpha) / (a - alpha), 2)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[✔] Conectado exitosamente al broker MQTT en {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(TOPIC_CONTROL_SP)
        client.subscribe(TOPIC_CONTROL_MODO)
        print(f"[*] Suscrito a {TOPIC_CONTROL_SP} y {TOPIC_CONTROL_MODO}")
    else:
        print(f"[⚠] Falla al conectar con código {rc}")

def on_message(client, userdata, msg):
    global setpoint_temp, modo_operativo
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        if msg.topic == TOPIC_CONTROL_SP:
            val_sp = payload.get("sp_temperatura", payload.get("sp_temp", None))
            if val_sp is not None:
                setpoint_temp = float(val_sp)
                print(f"[INFO] Nuevo setpoint de temperatura recibido: {setpoint_temp} °C")
        elif msg.topic == TOPIC_CONTROL_MODO:
            if "modo" in payload:
                modo_operativo = payload["modo"]
                print(f"[INFO] Nuevo modo operativo: {modo_operativo}")
    except Exception as e:
        print(f"[ERROR] Error al procesar mensaje MQTT: {e}")

def main():
    global temperatura_actual, humedad_actual, error_acumulado, error_previo
    
    print("=" * 60)
    print("Iniciando Simulador de ESP32 para Invernadero de Papa")
    print(f"Destino Broker: {MQTT_BROKER}:{MQTT_PORT} (Usuario: {MQTT_USER})")
    print("=" * 60)

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
    except AttributeError:
        client = mqtt.Client(client_id=CLIENT_ID)
        
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"[ERROR] No se pudo conectar al broker ({e}). Verifica que Mosquitto esté corriendo.")
        return

    client.loop_start()

    try:
        while True:
            t_inicio = time.time()
            
            # 1. Cálculo de Error y PID (Temperatura)
            error = setpoint_temp - temperatura_actual
            
            # Anti-windup condicional
            if -100.0 <= error_acumulado <= 100.0:
                error_acumulado += error * dt
            
            derivada = (error - error_previo) / dt
            p_term = kp * error
            i_term = ki * error_acumulado
            d_term = kd * derivada
            
            cv_salida = p_term + i_term + d_term
            cv_salida = max(-100.0, min(100.0, cv_salida))  # Saturación [-100, 100]
            error_previo = error
            
            # Split-range de actuadores
            pwm_calefactor = max(0.0, cv_salida)
            pwm_extractor = abs(min(0.0, cv_salida))
            
            # 2. Dinámica del Invernadero FOPDT simulada
            # Pérdida térmica hacia el exterior + aporte del calefactor - enfriamiento del extractor
            delta_calor = ( - (temperatura_actual - temp_ambiente_ext) + 
                            (K_ganancia * pwm_calefactor) - 
                            (0.10 * pwm_extractor) ) / tau_constante_tiempo
            
            temperatura_actual += delta_calor * dt + random.uniform(-0.02, 0.02)
            
            # Dinámica simple de humedad relativa (inversa a temperatura + ruido)
            humedad_actual = max(40.0, min(95.0, humedad_actual - (delta_calor * 1.5) + random.uniform(-0.1, 0.1)))
            
            vpd = calcular_vpd(temperatura_actual, humedad_actual)
            rocio = calcular_punto_rocio(temperatura_actual, humedad_actual)
            ts_ms = int(time.time() * 1000)
            
            # 3. Empaquetar y Publicar Telemetría Microclimática
            payload_clima = {
                "nodo_id": "esp32_invernadero_01",
                "zona": "zona_a_central",
                "timestamp_ms": ts_ms,
                "temp_aire": round(temperatura_actual, 2),
                "hum_aire": round(humedad_actual, 2),
                "temp_suelo": round(temperatura_actual - 1.8, 2),
                "hum_suelo": 63.5,
                "luz_lux": 31500.0 if 6 <= time.localtime().tm_hour <= 18 else 0.0,
                "co2_ppm": 415.0,
                "vpd_kpa": vpd,
                "punto_rocio": rocio,
                "sensores_ok": True
            }
            client.publish(TOPIC_TELEMETRIA_CLIMA, json.dumps(payload_clima), qos=1)
            
            # 4. Empaquetar y Publicar Telemetría PID
            payload_pid = {
                "nodo_id": "esp32_invernadero_01",
                "timestamp_ms": ts_ms,
                "variable": "TEMPERATURA",
                "sp_temp": round(setpoint_temp, 2),
                "pv_temp": round(temperatura_actual, 2),
                "error": round(error, 2),
                "cv_salida": round(cv_salida, 2),
                "termino_p": round(p_term, 2),
                "termino_i": round(i_term, 2),
                "termino_d": round(d_term, 2),
                "modo": modo_operativo,
                "pwm_calefactor": round(pwm_calefactor, 2),
                "pwm_extractor": round(pwm_extractor, 2),
                "antiwindup_activo": abs(cv_salida) >= 99.9
            }
            client.publish(TOPIC_TELEMETRIA_PID, json.dumps(payload_pid), qos=1)
            
            print(f"[PUB] T: {temperatura_actual:.2f}°C (SP: {setpoint_temp:.1f}°C) | CV: {cv_salida:+.1f}% (Cal: {pwm_calefactor:.0f}%, Ext: {pwm_extractor:.0f}%) | VPD: {vpd} kPa", end="\r")
            
            # Respetar periodo dt
            t_ejecucion = time.time() - t_inicio
            time.sleep(max(0.05, dt - t_ejecucion))

    except KeyboardInterrupt:
        print("\n[!] Deteniendo simulador.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
