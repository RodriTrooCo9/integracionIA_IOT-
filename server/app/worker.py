"""
Worker Asíncrono de Inferencia y Lazo Supervisor en Cascada
Proyecto de Tesis - Invernadero de Papa (La Paz, Bolivia)

Funcionalidad:
1. Suscribe a telemetría de microclima y detecciones de visión en MQTT.
2. Mantiene una ventana temporal deslizante.
3. Ejecuta periódicamente la función de Fusión Multimodal de Riesgo.
4. Si el nivel pasa a ALTO o CRÍTICO, comanda nuevos setpoints al ESP32 vía MQTT
   y dispara alertas al bot de Telegram.
"""

import time
import json
import logging
import asyncio
from datetime import datetime
from collections import deque
import numpy as np

import paho.mqtt.client as mqtt
from server.app.core.config import settings
from server.app.services.telegram_bot import telegram_service
from server.app.services.database import db_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [WORKER]: %(message)s"
)
logger = logging.getLogger("inference_worker")

class SupervisorWorker:
    def __init__(self):
        self.buffer_clima = deque(maxlen=48) # Buffer de 48 horas / muestras
        self.ultima_deteccion_vision = {
            "severidad_porcentaje": 0.0,
            "conteo_insectos": 0,
            "timestamp": time.time()
        }
        self.score_riesgo_actual = 0.15
        self.nivel_actual = "BAJO"
        
        # Cliente MQTT dedicado para el Worker
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="supervisor_inference_worker")
        except AttributeError:
            self.client = mqtt.Client(client_id="supervisor_inference_worker")
            
        if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
            
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.running = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("Worker conectado a Mosquitto. Suscribiendo a telemetría y visión...")
            client.subscribe(settings.TOPIC_TELEMETRIA_CLIMA, qos=1)
            client.subscribe(settings.TOPIC_VISION_DETECCIONES, qos=1)
        else:
            logger.warning(f"Error conectando worker a MQTT: {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if msg.topic == settings.TOPIC_TELEMETRIA_CLIMA:
                self.buffer_clima.append({
                    "timestamp": time.time(),
                    "temp_in": float(payload.get("temp_aire", payload.get("temp_in", 18.0))),
                    "hum_in": float(payload.get("hum_aire", payload.get("hum_in", 70.0))),
                    "vpd_kpa": float(payload.get("vpd_kpa", 0.8)),
                    "lwh": float(payload.get("lwh_continuo_horas", 0.0))
                })
            elif msg.topic == settings.TOPIC_VISION_DETECCIONES:
                self.ultima_deteccion_vision = {
                    "severidad_porcentaje": float(payload.get("severidad_porcentaje", 0.0)),
                    "conteo_insectos": int(payload.get("conteo_insectos", 0)),
                    "timestamp": time.time()
                }
        except Exception as e:
            logger.error(f"Error parseando mensaje MQTT en tópico {msg.topic}: {e}")

    def calcular_fusion_multimodal(self) -> tuple:
        """
        Calcula la Fusión Multimodal:
        Score = 0.45 * Clima + 0.35 * Visión + 0.20 * Tendencia
        """
        # 1. Componente Climática (Blight Units / Horas de hoja húmeda continuas)
        if len(self.buffer_clima) >= 6:
            recientes = list(self.buffer_clima)[-12:]
            hum_media = np.mean([m["hum_in"] for m in recientes])
            lwh_max = np.max([m["lwh"] for m in recientes])
            vpd_min = np.min([m["vpd_kpa"] for m in recientes])
            
            # Estimación heurística de riesgo fúngico
            p_clima = 0.0
            if lwh_max >= 10:
                p_clima += 0.50
            if hum_media >= 88.0:
                p_clima += 0.30
            if vpd_min <= 0.20:
                p_clima += 0.20
            p_clima = float(np.clip(p_clima, 0.0, 1.0))
        else:
            p_clima = 0.20 # Valor nominal por defecto

        # 2. Componente de Visión
        sev = self.ultima_deteccion_vision["severidad_porcentaje"]
        conteo = self.ultima_deteccion_vision["conteo_insectos"]
        score_vision = min(1.0, (sev / 20.0) * 0.65 + (conteo / 25.0) * 0.35)

        # 3. Componente de Tendencia Temporal (derivada en buffer)
        if len(self.buffer_clima) >= 12:
            hums = [m["hum_in"] for m in self.buffer_clima]
            derivada_hum = (hums[-1] - hums[0]) / len(hums)
            score_tend = float(np.clip(derivada_hum / 15.0, 0.0, 1.0))
        else:
            score_tend = 0.10

        # Fusión ponderada
        score_total = (0.45 * p_clima) + (0.35 * score_vision) + (0.20 * score_tend)
        score_total = float(np.clip(score_total, 0.0, 1.0))

        # Determinar nivel y setpoints recomendados
        if score_total < 0.30:
            nivel = "BAJO"
            sp_temp, sp_hum = 18.0, 75.0
            accion = "Monitoreo rutinario."
        elif score_total < 0.55:
            nivel = "MEDIO"
            sp_temp, sp_hum = 18.5, 70.0
            accion = "Ventilación preventiva diurna."
        elif score_total < 0.75:
            nivel = "ALTO"
            sp_temp, sp_hum = 19.5, 65.0
            accion = "Deshumidificación activa nocturna; inhibición de rocío."
        else:
            nivel = "CRÍTICO"
            sp_temp, sp_hum = 20.0, 60.0
            accion = "Protocolo de choque fitosanitario: extracción forzada y biofungicida."

        return score_total, nivel, sp_temp, sp_hum, accion

    async def ciclo_supervision(self):
        """Bucle periódico de evaluación y control en cascada."""
        self.running = True
        logger.info("Iniciando bucle de supervisión en cascada (período: 30 segundos)...")
        
        while self.running:
            try:
                score, nivel, sp_t, sp_h, accion = self.calcular_fusion_multimodal()
                self.score_riesgo_actual = score
                
                # Publicar índice de riesgo en MQTT
                payload_riesgo = {
                    "timestamp": datetime.now().isoformat(),
                    "score_riesgo": round(score, 3),
                    "nivel": nivel,
                    "sp_temperatura_sugerido": sp_t,
                    "sp_humedad_sugerido": sp_h,
                    "accion": accion
                }
                self.client.publish(settings.TOPIC_RIESGO_INDICE, json.dumps(payload_riesgo), qos=1)

                # Si el nivel es ALTO o CRÍTICO, comanda setpoints en cascada
                if nivel in ["ALTO", "CRÍTICO"] and nivel != self.nivel_actual:
                    logger.warning(f"¡Cambio de estado fitosanitario a {nivel}! Score: {score:.3f}. Ajustando setpoints...")
                    
                    # 1. Comandar setpoints al ESP32 vía MQTT
                    payload_sp = {
                        "sp_temperatura": sp_t,
                        "sp_humedad": sp_h,
                        "usuario_origen": "SISTEMA_IA_SUPERVISOR",
                        "timestamp": datetime.now().isoformat()
                    }
                    self.client.publish(settings.TOPIC_CONTROL_SETPOINTS, json.dumps(payload_sp), qos=1, retain=True)

                    # 2. Registrar en base de datos
                    await db_service.registrar_auditoria_setpoint(
                        variable_control="TEMPERATURA_Y_HUMEDAD",
                        sp_anterior=18.0,
                        sp_nuevo=sp_t,
                        usuario_origen="SISTEMA_IA_SUPERVISOR",
                        justificacion=f"Lazo externo IA por riesgo {nivel} (Score: {score:.3f}) | SP_Hum: {sp_h}%"
                    )
                    await db_service.registrar_evento_alarma(
                        tipo_evento=f"RIESGO_FITOSANITARIO_{nivel}",
                        nivel_severidad=nivel,
                        mensaje=f"Riesgo fúngico elevado. Setpoint temp ajustado a {sp_t}°C y humedad a {sp_h}%.",
                        valor_disparador=score,
                        accion_ejecutada="AJUSTE_SETPOINTS_Y_TELEGRAM",
                        notificado_telegram=True
                    )

                    # 3. Notificar a Telegram
                    resumen_clima = f"• Nivel: `{nivel}` | Score: `{score:.3f}`\n• SP Temp comandado: `{sp_t}°C`\n• SP Hum comandado: `{sp_h}%`"
                    await telegram_service.enviar_alerta_con_foto(
                        titulo=f"Transición a Riesgo {nivel}",
                        score_riesgo=score,
                        nivel=nivel,
                        clima_resumen=resumen_clima,
                        accion_recomendada=accion
                    )

                self.nivel_actual = nivel

            except Exception as e:
                logger.error(f"Error en ciclo de supervisión: {e}")

            await asyncio.sleep(15) # Evaluación periódica

    def iniciar(self):
        try:
            self.client.connect_async(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=60)
            self.client.loop_start()
            asyncio.run(self.ciclo_supervision())
        except KeyboardInterrupt:
            logger.info("Deteniendo worker...")
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    worker = SupervisorWorker()
    worker.iniciar()
