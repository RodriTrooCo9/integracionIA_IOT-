"""
Servidor Principal FastAPI: Invernadero IoT-PID-IA Papa
Tesis de Grado - La Paz, Bolivia
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from server.app.core.config import settings
from server.app.api.endpoints import router as api_router
from server.app.services.mqtt_client import mqtt_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("fastapi_main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    from server.app.services.bootstrap import inicializar_db
    inicializar_db()
    # Inicio de ciclo de vida
    logger.info(f"Iniciando {settings.PROJECT_NAME} v{settings.VERSION}...")
    try:
        mqtt_service.iniciar()
    except Exception as e:
        logger.warning(f"No se pudo iniciar MQTT en arranque: {e}")
    yield
    # Fin de ciclo de vida
    logger.info("Deteniendo servidor y desconectando clientes MQTT...")
    try:
        mqtt_service.detener()
    except Exception as e:
        logger.warning(f"Error deteniendo MQTT: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend de Inferencia YOLO11n + SAHI, Supervisión de Riesgo y Control de Setpoints IoT.",
    lifespan=lifespan
)

# Habilitar CORS para integración con la aplicación web y dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from server.app.core.security import RequestGuardMiddleware
app.add_middleware(RequestGuardMiddleware)

# Incluir rutas bajo prefijo /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["General"])
async def root():
    return {
        "mensaje": "Servidor IoT-PID-IA de Regulación Microclimática en Invernadero de Papa",
        "ubicacion": "La Paz, Bolivia (~3600 msnm)",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app.main:app", host="0.0.0.0", port=8000, reload=True)
