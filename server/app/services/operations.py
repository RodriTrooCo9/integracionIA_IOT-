"""Application operations shared by Django, FastAPI and the supervisor."""
import asyncio
import time
from uuid import uuid4
from server.app.core.config import settings
from server.app.services.database import db_service
from server.app.services.mqtt_client import mqtt_service
from server.app.services.vision_service import vision_service
from server.app.services.telegram_bot import telegram_service


def command_payload(values, origin):
    return {**values, 'usuario_origen': origin, 'command_id': uuid4().hex,
            'timestamp': time.time(), 'expires_at': int(time.time()) + 120}


async def comandar_control(values, origin, reason, topic=None, publisher=None):
    payload = command_payload(values, origin)
    # Serialize publishers across processes so the previous value and audit remain consistent.
    async with db_service.get_connection() as conn:
        await conn.execute('BEGIN IMMEDIATE')
        previous = {}
        for key in values:
            cursor = await conn.execute('SELECT valor FROM control_publicado WHERE variable=?', (key,))
            row = await cursor.fetchone()
            previous[key] = row[0] if row else None
        published = await asyncio.to_thread(publisher or mqtt_service.publicar,
                                            topic or settings.TOPIC_CONTROL_SETPOINTS,
                                            payload, qos=1, retain=False)
        for variable, value in values.items():
            await conn.execute("""INSERT INTO auditoria_control_pid
                (usuario_origen,variable_control,sp_anterior,sp_nuevo,justificacion)
                VALUES (?,?,?,?,?)""", (origin, variable, previous[variable], value,
                f'{reason} | entrega={"PUBLICADO_BROKER" if published else "FALLIDA"}; '
                f'command_id={payload["command_id"]}; aplicación en nodo no confirmada'))
            if published:
                await conn.execute("""INSERT INTO control_publicado(variable,valor) VALUES (?,?)
                    ON CONFLICT(variable) DO UPDATE SET valor=excluded.valor,timestamp=CURRENT_TIMESTAMP""",
                    (variable, value))
        await conn.commit()
    return {'status': 'published' if published else 'unavailable',
            **values, 'message': 'Publicado al broker; aplicación no confirmada' if published else 'Broker no disponible; orden no publicada',
            'publicado_mqtt': published, 'aplicado_confirmado': False,
            'command_id': payload['command_id'], 'timestamp': str(payload['timestamp'])}


async def inferir_y_registrar(path, nodo_camara, tipo_origen, usar_sahi):
    result = await asyncio.to_thread(vision_service.procesar_imagen, str(path), tipo_origen, usar_sahi)
    record_id = await db_service.registrar_deteccion(
        nodo_camara=nodo_camara, tipo_origen=tipo_origen,
        ruta_original=result['ruta_imagen_original'], ruta_anotada=result['ruta_imagen_anotada'],
        clase_detectada=result['clase_detectada'], confianza=result['confianza'],
        bbox_json=result['bbox_json'], conteo_insectos=result['conteo_insectos'],
        severidad_porcentaje=result['severidad_porcentaje'], tiempo_inferencia_ms=result['tiempo_inferencia_ms'],
        procesado_con_sahi=result['procesado_con_sahi'], simulado=result['simulado'], motor=result['motor'])
    published = False
    alert_sent = False
    # Simulation stays visible to the operator but never enters the control loop.
    if not result['simulado']:
        payload = {**result, 'id': record_id, 'timestamp': time.time(),
                   'nodo_camara': nodo_camara, 'tipo_origen': tipo_origen}
        published = await asyncio.to_thread(mqtt_service.publicar, settings.TOPIC_VISION_DETECCIONES, payload)
        if result['severidad_porcentaje'] >= 15 or result['conteo_insectos'] >= 15:
            level = 'CRÍTICO' if result['severidad_porcentaje'] >= 25 or result['conteo_insectos'] >= 25 else 'ALTO'
            response = await telegram_service.enviar_alerta_con_foto(
                titulo=f'Detección de {result["clase_detectada"]}',
                score_riesgo=min(1.0, result['severidad_porcentaje'] / 30), nivel=level,
                clima_resumen=f'Severidad: {result["severidad_porcentaje"]}%; insectos: {result["conteo_insectos"]}',
                accion_recomendada='Inspección visual y evaluación del operador.',
                ruta_foto=result['ruta_imagen_anotada'])
            alert_sent = response.get('ok') is True
            await db_service.registrar_evento_alarma(
                tipo_evento='DETECCION_PATOGENO_ALTA', nivel_severidad=level,
                mensaje=f'{result["clase_detectada"]}: {result["severidad_porcentaje"]}%',
                notificado_telegram=alert_sent, accion_ejecutada='INFERENCIA_Y_SOLICITUD_ALERTA')
    return {'id_registro': record_id, 'resultado': result, 'publicado_mqtt': published,
            'alerta_telegram_disparada': alert_sent}
