"""HTTP interface for greenhouse operations with authenticated writes."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from server.app.core.config import settings
from server.app.core.security import require_operator
from server.app.services.database import db_service
from server.app.services.mqtt_client import mqtt_service
from server.app.services.operations import comandar_control, inferir_y_registrar
from server.app.services.storage import guardar_imagen, ImageValidationError
from server.app.services.vision_service import VisionUnavailable
from server.app.services.telegram_bot import telegram_service

router = APIRouter()


class SetpointsRequest(BaseModel):
    sp_temperatura: float = Field(..., ge=5.0, le=35.0, allow_inf_nan=False)
    sp_humedad: float = Field(..., ge=30.0, le=95.0, allow_inf_nan=False)
    usuario_origen: str = Field(default='OPERADOR_API', max_length=32)
    justificacion: str = Field(default='Ajuste manual', max_length=1000)


class PIDRequest(BaseModel):
    kp: float = Field(..., ge=0, le=100, allow_inf_nan=False)
    ki: float = Field(..., ge=0, le=10, allow_inf_nan=False)
    kd: float = Field(..., ge=0, le=1000, allow_inf_nan=False)


class TelegramNotificationRequest(BaseModel):
    titulo: str = Field(..., max_length=100)
    mensaje: str = Field(..., max_length=600)
    nivel: str = Field(default='ALTO', pattern='^(BAJO|MEDIO|ALTO|CRÍTICO)$')


@router.get('/health', tags=['Sistema'])
async def health_check():
    return {'status': 'online', 'proyecto': settings.PROJECT_NAME, 'version': settings.VERSION,
            'mqtt_conectado': mqtt_service.conectado,
            'sqlite_db': Path(settings.SQLITE_DB_PATH).exists(),
            'timestamp_utc': datetime.now(timezone.utc).isoformat()}


@router.post('/vision/inferir', dependencies=[Depends(require_operator)], tags=['Visión Artificial'])
async def inferir_imagen(imagen: UploadFile = File(...), nodo_camara: str = Form('cam_invernadero_01'),
                        tipo_origen: str = Form('HOJA_FOLLAJE'), usar_sahi: bool = Form(False)):
    try:
        path = await asyncio.to_thread(guardar_imagen, imagen.file)
        return await inferir_y_registrar(path, nodo_camara, tipo_origen, usar_sahi)
    except VisionUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except (ImageValidationError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    finally:
        await imagen.close()


@router.post('/control/setpoints', dependencies=[Depends(require_operator)], tags=['Control PID'])
async def actualizar_setpoints(req: SetpointsRequest):
    result = await comandar_control(
        {'sp_temperatura': req.sp_temperatura, 'sp_humedad': req.sp_humedad},
        'OPERADOR_API', req.justificacion)
    if not result['publicado_mqtt']:
        raise HTTPException(503, detail=result)
    return result


@router.get('/vision/historial', tags=['Visión Artificial'])
async def obtener_historial_vision(limit: int = Query(20, ge=1, le=100)):
    return await db_service.obtener_ultimas_detecciones(limit)


@router.get('/alertas', tags=['Alertas'])
async def obtener_alarmas(limit: int = Query(20, ge=1, le=100)):
    return await db_service.obtener_ultimas_alarmas(limit)


@router.post('/telegram/notificar', dependencies=[Depends(require_operator)], tags=['Alertas'])
async def notificar_telegram(req: TelegramNotificationRequest):
    # A remote caller may not select arbitrary files on the server.
    response = await telegram_service.enviar_alerta_con_foto(
        req.titulo, 0.85, req.nivel, req.mensaje, 'Verificación del operador.')
    return {'status': 'sent' if response.get('ok') is True else 'not_sent', 'telegram_response': response}
