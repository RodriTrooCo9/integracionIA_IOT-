"""Timestamp-based supervisor with stale-data protection and retryable commands."""
import asyncio
import json
import logging
import math
import threading
import time
from collections import deque

from server.app.core.config import settings
from server.app.services.database import db_service
from server.app.services.mqtt_client import MQTTClientService
from server.app.services.operations import comandar_control
from server.app.services.telegram_bot import telegram_service

logger = logging.getLogger('inference_worker')


class SupervisorWorker:
    def __init__(self):
        self.buffer_clima = deque(maxlen=48 * 60)
        self.ultima_deteccion_vision = {'severidad_porcentaje': 0.0, 'conteo_insectos': 0, 'timestamp': 0}
        self.transport = MQTTClientService()
        self.client = self.transport.client
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.lock = threading.RLock()
        self.last_climate = None
        self.wet_hours = 0.0
        self.score_riesgo_actual = 0.0
        self.nivel_actual = 'SIN_DATOS'
        self.applied_level = None  # Last broker-confirmed command, not device acknowledgement.
        self.recovery_since = None
        self.recovery_level = None
        self.running = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        self.transport._on_connect(client, userdata, flags, rc, properties)
        if rc == 0:
            client.subscribe(settings.TOPIC_TELEMETRIA_CLIMA, qos=1)
            client.subscribe(settings.TOPIC_VISION_DETECCIONES, qos=1)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            now = time.time()
            # Source time prevents replayed/retained packets from becoming fresh.
            stamp = float(payload.get('timestamp', 0))
            if not math.isfinite(stamp) or stamp > now + 10:
                return
            with self.lock:
                if msg.topic == settings.TOPIC_TELEMETRIA_CLIMA:
                    if now - stamp > settings.TELEMETRY_MAX_AGE_SECONDS:
                        return
                    if self.last_climate and stamp <= self.last_climate['timestamp']:
                        return
                    if payload.get('sensores_ok') is not True:
                        self.last_climate = None
                        self.wet_hours = 0.0
                        return
                    temp = float(payload['temp_aire'])
                    hum = float(payload['hum_aire'])
                    vpd = float(payload['vpd_kpa'])
                    if not all(math.isfinite(v) for v in (temp, hum, vpd)) or not (-20 <= temp <= 60 and 0 <= hum <= 100 and 0 <= vpd <= 10):
                        self.last_climate = None
                        self.wet_hours = 0.0
                        return
                    previous = self.last_climate
                    continuous = previous and 0 < stamp - previous['timestamp'] <= settings.TELEMETRY_MAX_AGE_SECONDS
                    if continuous and hum >= 90 and previous['hum_in'] >= 90:
                        self.wet_hours += (stamp - previous['timestamp']) / 3600
                    else:
                        self.wet_hours = 0.0
                    sample = {'timestamp': stamp, 'temp_in': temp, 'hum_in': hum,
                              'vpd_kpa': vpd, 'lwh': self.wet_hours}
                    self.last_climate = sample
                    cutoff = stamp - 48 * 3600
                    while self.buffer_clima and self.buffer_clima[0]['timestamp'] < cutoff:
                        self.buffer_clima.popleft()
                    if self.buffer_clima and int(self.buffer_clima[-1]['timestamp'] // 60) == int(stamp // 60):
                        self.buffer_clima[-1] = sample
                    else:
                        self.buffer_clima.append(sample)
                elif msg.topic == settings.TOPIC_VISION_DETECCIONES:
                    if payload.get('simulado', True) or now - stamp > settings.VISION_MAX_AGE_SECONDS:
                        return
                    if stamp <= self.ultima_deteccion_vision['timestamp']:
                        return
                    severity, count = float(payload['severidad_porcentaje']), int(payload['conteo_insectos'])
                    if math.isfinite(severity) and 0 <= severity <= 100 and 0 <= count <= 100000:
                        self.ultima_deteccion_vision = {'severidad_porcentaje': severity,
                                                      'conteo_insectos': count, 'timestamp': stamp}
        except (ValueError, TypeError, KeyError, UnicodeError):
            logger.warning('Mensaje de supervisión inválido en %s', msg.topic)

    def calcular_fusion_multimodal(self):
        now = time.time()
        with self.lock:
            latest = dict(self.last_climate) if self.last_climate else None
            recent = [dict(m) for m in self.buffer_clima if now - m['timestamp'] <= 12 * 3600]
            vision = dict(self.ultima_deteccion_vision)
        if latest is None or not 0 <= now - latest['timestamp'] <= settings.TELEMETRY_MAX_AGE_SECONDS:
            return 0.0, 'SIN_DATOS', None, None, 'Telemetría no válida o vencida; sin órdenes automáticas.'
        p_climate = (0.5 if latest['lwh'] >= 10 else 0)
        p_climate += 0.3 if latest['hum_in'] >= 88 else 0
        p_climate += 0.2 if latest['vpd_kpa'] <= 0.2 else 0
        p_vision = 0.0
        if 0 <= now - vision['timestamp'] <= settings.VISION_MAX_AGE_SECONDS:
            p_vision = min(1.0, (vision['severidad_porcentaje'] / 20) * 0.65 + (vision['conteo_insectos'] / 25) * 0.35)
        trend = 0.0
        if len(recent) >= 2:
            hours = (recent[-1]['timestamp'] - recent[0]['timestamp']) / 3600
            if hours >= 1:
                trend = max(0.0, min(1.0, (recent[-1]['hum_in'] - recent[0]['hum_in']) / hours / 15))
        score = 0.45 * p_climate + 0.35 * p_vision + 0.20 * trend
        if score < 0.30:
            return score, 'BAJO', 18.0, 75.0, 'Monitoreo rutinario.'
        if score < 0.55:
            return score, 'MEDIO', 18.5, 70.0, 'Ventilación preventiva.'
        if score < 0.75:
            return score, 'ALTO', 19.5, 65.0, 'Deshumidificación activa; inspección del operador.'
        return score, 'CRÍTICO', 20.0, 60.0, 'Extracción y evaluación fitosanitaria por el operador.'

    async def evaluar_ciclo(self):
        score, level, temp, hum, action = self.calcular_fusion_multimodal()
        self.score_riesgo_actual, self.nivel_actual = score, level
        await asyncio.to_thread(self.transport.publicar, settings.TOPIC_RIESGO_INDICE,
                                {'timestamp': time.time(), 'score_riesgo': round(score, 3),
                                 'nivel': level, 'datos_validos': level != 'SIN_DATOS',
                                 'vision_vigente': time.time() - self.ultima_deteccion_vision['timestamp'] <= settings.VISION_MAX_AGE_SECONDS,
                                 'horas_hoja_humeda': self.wet_hours, 'accion': action})
        if level == 'SIN_DATOS':
            self.recovery_since = None
            return
        ranks = {'BAJO': 0, 'MEDIO': 1, 'ALTO': 2, 'CRÍTICO': 3}
        if self.applied_level is None and level not in {'ALTO', 'CRÍTICO'}:
            return
        if self.applied_level == level:
            self.recovery_since = None
            self.recovery_level = None
            return
        if self.applied_level and ranks[level] < ranks[self.applied_level]:
            if self.recovery_since is None or self.recovery_level != level:
                self.recovery_since = time.monotonic()
                self.recovery_level = level
            if time.monotonic() - self.recovery_since < settings.SUPERVISOR_RECOVERY_SECONDS:
                return
        else:
            self.recovery_since = None
            self.recovery_level = None
        result = await comandar_control({'sp_temperatura': temp, 'sp_humedad': hum},
                                        'SISTEMA_IA_SUPERVISOR', f'Riesgo {level}: {score:.3f}',
                                        publisher=self.transport.publicar)
        if not result['publicado_mqtt']:
            return  # Leave command pending for the next evaluation.
        self.applied_level = level
        await db_service.guardar_control_publicado({'supervisor_level': ranks[level]})
        response = await telegram_service.enviar_alerta_con_foto(
            titulo=f'Riesgo {level}', score_riesgo=score, nivel=level,
            clima_resumen=f'Consigna publicada: {temp} °C / {hum}%. Aplicación no confirmada.',
            accion_recomendada=action)
        await db_service.registrar_evento_alarma(
            tipo_evento=f'RIESGO_FITOSANITARIO_{level}', nivel_severidad=level,
            mensaje=action, valor_disparador=score,
            accion_ejecutada='SETPOINT_PUBLICADO_BROKER', notificado_telegram=response.get('ok') is True)

    async def ciclo_supervision(self):
        self.running = True
        stored = await db_service.obtener_control_publicado('supervisor_level')
        if stored is not None:
            self.applied_level = {0: 'BAJO', 1: 'MEDIO', 2: 'ALTO', 3: 'CRÍTICO'}.get(stored)
        while self.running:
            try:
                await self.evaluar_ciclo()
            except Exception:
                logger.exception('Error en supervisión')
            await asyncio.sleep(settings.SUPERVISOR_PERIOD_SECONDS)

    def iniciar(self):
        from server.app.services.bootstrap import inicializar_db
        inicializar_db()
        self.transport.iniciar()
        try:
            asyncio.run(self.ciclo_supervision())
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self.transport.detener()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    SupervisorWorker().iniciar()
