"""
Endpoints RESTful de la API FastAPI para Invernadero IoT-PID-IA
Proyecto de Tesis - Cultivo de Papa (La Paz, Bolivia)
"""

import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Query, status
from pydantic import BaseModel, Field

from server.app.core.config import settings
from server.app.services.database import db_service
from server.app.services.vision_service import vision_service
from server.app.services.mqtt_client import mqtt_service
from server.app.services.telegram_bot import telegram_service

router = APIRouter()

# ------------------------------------------------------------------------------
# Modelos Pydantic para Validación de Esquemas
# ------------------------------------------------------------------------------
class SetpointsRequest(BaseModel):
    sp_temperatura: float = Field(..., ge=5.0, le=35.0, description="Setpoint de temperatura en °C")
    sp_humedad: float = Field(..., ge=30.0, le=95.0, description="Setpoint de humedad relativa en %")
    usuario_origen: str = Field(default="OPERADOR_WEB", description="SISTEMA_IA, OPERADOR_WEB o VALOR_DEFECTO")
    justificacion: Optional[str] = Field(default="Ajuste manual desde dashboard", description="Motivo del cambio")

class SetpointsResponse(BaseModel):
    status: str
    sp_temperatura: float
    sp_humedad: float
    timestamp: str
    publicado_mqtt: bool

class TelegramNotificationRequest(BaseModel):
    titulo: str = Field(..., description="Encabezado del reporte")
    mensaje: str = Field(..., description="Cuerpo del mensaje")
    nivel: str = Field(default="ALTO", description="BAJO, MEDIO, ALTO, CRÍTICO")
    ruta_foto: Optional[str] = Field(default=None, description="Ruta local opcional de imagen a adjuntar")

# ------------------------------------------------------------------------------
# 1. Healthcheck
# ------------------------------------------------------------------------------
@router.get("/health", tags=["Sistema"])
async def health_check():
    """Verifica estado de salud del backend, base de datos y conexión MQTT."""
    return {
        "status": "online",
        "proyecto": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "mqtt_conectado": mqtt_service.conectado,
        "sqlite_db": Path(settings.SQLITE_DB_PATH).exists(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }

# ------------------------------------------------------------------------------
# 2. Inferencia de Visión Artificial (YOLO11n + SAHI)
# ------------------------------------------------------------------------------
@router.post("/vision/inferir", tags=["Visión Artificial"])
async def inferir_imagen(
    imagen: UploadFile = File(..., description="Archivo de imagen (JPEG, PNG)"),
    nodo_camara: str = Form("cam_invernadero_01"),
    tipo_origen: str = Form("HOJA_FOLLAJE", description="HOJA_FOLLAJE o TRAMPA_AMARILLA"),
    usar_sahi: bool = Form(False, description="Forzar segmentación SAHI")
):
    """
    Recibe una imagen, ejecuta detección (YOLO11n / SAHI), guarda en BD,
    publica evento en MQTT y genera alerta a Telegram si la severidad es crítica.
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_limpio = f"{timestamp_str}_{imagen.filename.replace(' ', '_')}"
    ruta_destino = upload_dir / nombre_limpio

    # Guardar archivo temporal en disco
    try:
        with open(ruta_destino, "wb") as buffer:
            shutil.copyfileobj(imagen.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando imagen subida: {e}")

    # Ejecutar inferencia de visión
    try:
        resultado = vision_service.procesar_imagen(
            ruta_imagen=str(ruta_destino),
            tipo_origen=tipo_origen,
            usar_sahi=usar_sahi
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en inferencia de visión: {e}")

    # Persistir en SQLite
    id_registro = await db_service.registrar_deteccion(
        nodo_camara=nodo_camara,
        tipo_origen=tipo_origen,
        ruta_original=resultado["ruta_imagen_original"],
        ruta_anotada=resultado["ruta_imagen_anotada"],
        clase_detectada=resultado["clase_detectada"],
        confianza=resultado["confianza"],
        bbox_json=resultado["bbox_json"],
        conteo_insectos=resultado["conteo_insectos"],
        severidad_porcentaje=resultado["severidad_porcentaje"],
        tiempo_inferencia_ms=resultado["tiempo_inferencia_ms"],
        procesado_con_sahi=resultado["procesado_con_sahi"]
    )

    # Publicar resultado en MQTT
    mqtt_payload = {
        "id": id_registro,
        "timestamp": datetime.now().isoformat(),
        "nodo_camara": nodo_camara,
        "tipo_origen": tipo_origen,
        "clase_detectada": resultado["clase_detectada"],
        "confianza": resultado["confianza"],
        "conteo_insectos": resultado["conteo_insectos"],
        "severidad_porcentaje": resultado["severidad_porcentaje"],
        "tiempo_ms": resultado["tiempo_inferencia_ms"]
    }
    publicado_mqtt = mqtt_service.publicar(settings.TOPIC_VISION_DETECCIONES, mqtt_payload)

    # Evaluar disparo de alarma a Telegram ante severidad crítica
    disparo_alerta = False
    if resultado["severidad_porcentaje"] >= 15.0 or resultado["conteo_insectos"] >= 15:
        disparo_alerta = True
        nivel_alerta = "CRÍTICO" if (resultado["severidad_porcentaje"] >= 25.0 or resultado["conteo_insectos"] >= 25) else "ALTO"
        
        await db_service.registrar_evento_alarma(
            tipo_evento="DETECCION_PATOGENO_ALTA",
            nivel_severidad=nivel_alerta,
            mensaje=f"Detección visual de {resultado['clase_detectada']}: Severidad {resultado['severidad_porcentaje']}% | Conteo {resultado['conteo_insectos']}",
            valor_disparador=resultado["severidad_porcentaje"],
            accion_ejecutada="NOTIFICACION_TELEGRAM",
            notificado_telegram=True
        )
        
        # Enviar Telegram en segundo plano
        resumen_clima = f"• Clase: {resultado['clase_detectada']}\n• Severidad: {resultado['severidad_porcentaje']}%\n• Conteo: {resultado['conteo_insectos']} insectos"
        await telegram_service.enviar_alerta_con_foto(
            titulo=f"Detección de {resultado['clase_detectada'].replace('_', ' ').capitalize()}",
            score_riesgo=min(1.0, resultado["severidad_porcentaje"] / 30.0),
            nivel=nivel_alerta,
            clima_resumen=resumen_clima,
            accion_recomendada="Inspección visual inmediata y preparación de aplicación dirigida.",
            ruta_foto=resultado["ruta_imagen_anotada"]
        )

    return {
        "id_registro": id_registro,
        "resultado": resultado,
        "publicado_mqtt": publicado_mqtt,
        "alerta_telegram_disparada": disparo_alerta
    }

# ------------------------------------------------------------------------------
# 3. Control de Setpoints y Auditoría PID
# ------------------------------------------------------------------------------
@router.post("/control/setpoints", response_model=SetpointsResponse, tags=["Control PID"])
async def actualizar_setpoints(req: SetpointsRequest):
    """
    Actualiza los setpoints de temperatura y humedad, audita la transacción
    en SQLite y publica en el tópico MQTT para comando del ESP32.
    """
    timestamp_actual = datetime.now().isoformat()

    # Registrar en auditoría
    await db_service.registrar_auditoria_setpoint(
        usuario_origen=req.usuario_origen,
        variable_control="TEMPERATURA_Y_HUMEDAD",
        sp_anterior=18.0, # Valor nominal base
        sp_nuevo=req.sp_temperatura,
        justificacion=f"{req.justificacion} | SP_Hum: {req.sp_humedad}%"
    )

    # Publicar comando hacia el ESP32
    payload_mqtt = {
        "sp_temperatura": req.sp_temperatura,
        "sp_humedad": req.sp_humedad,
        "usuario_origen": req.usuario_origen,
        "timestamp": timestamp_actual
    }
    publicado = mqtt_service.publicar(settings.TOPIC_CONTROL_SETPOINTS, payload_mqtt, qos=1, retain=True)

    return SetpointsResponse(
        status="success",
        sp_temperatura=req.sp_temperatura,
        sp_humedad=req.sp_humedad,
        timestamp=timestamp_actual,
        publicado_mqtt=publicado
    )

# ------------------------------------------------------------------------------
# 4. Consultas Históricas y Alarmas
# ------------------------------------------------------------------------------
@router.get("/vision/historial", tags=["Visión Artificial"])
async def obtener_historial_vision(limit: int = Query(20, ge=1, le=100)):
    """Obtiene las últimas detecciones de visión registradas en SQLite."""
    return await db_service.obtener_ultimas_detecciones(limit=limit)

@router.get("/alertas", tags=["Alertas"])
async def obtener_alarmas(limit: int = Query(20, ge=1, le=100)):
    """Obtiene el historial de eventos críticos y alarmas del invernadero."""
    return await db_service.obtener_ultimas_alarmas(limit=limit)

# ------------------------------------------------------------------------------
# 5. Telegram Notificación Directa
# ------------------------------------------------------------------------------
@router.post("/telegram/notificar", tags=["Alertas"])
async def notificar_telegram(req: TelegramNotificationRequest):
    """Permite el envío manual o de prueba de alertas a Telegram."""
    resp = await telegram_service.enviar_alerta_con_foto(
        titulo=req.titulo,
        score_riesgo=0.85,
        nivel=req.nivel,
        clima_resumen=req.mensaje,
        accion_recomendada="Verificación de sistema.",
        ruta_foto=req.ruta_foto
    )
    return {"status": "ok", "telegram_response": resp}
