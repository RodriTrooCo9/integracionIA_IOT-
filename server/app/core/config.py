"""
Configuración Central del Servidor FastAPI y Microservicios IoT
Proyecto de Tesis - Invernadero de Papa (La Paz, Bolivia)
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file=str(BASE_DIR / ".env"), case_sensitive=False)

    PROJECT_NAME: str = "Invernadero IoT-PID-IA Papa"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    API_KEY: str = ""
    VISION_DEMO_MODE: bool = False
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024
    MAX_IMAGE_PIXELS: int = 16_000_000
    TELEMETRY_MAX_AGE_SECONDS: float = 30.0
    VISION_MAX_AGE_SECONDS: float = 3600.0
    SUPERVISOR_RECOVERY_SECONDS: float = 120.0
    SUPERVISOR_PERIOD_SECONDS: float = 15.0

    # Base de Datos Relacional SQLite
    SQLITE_DB_PATH: str = str(BASE_DIR / "data" / "invernadero_relacional.db")
    
    # Broker MQTT (Eclipse Mosquitto)
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_USERNAME: str = Field(default="fastapi_server", validation_alias=AliasChoices("BACKEND_MQTT_USERNAME", "MQTT_USERNAME"))
    MQTT_PASSWORD: str = Field(default="FastApiSecretPass2026!", validation_alias=AliasChoices("BACKEND_MQTT_PASSWORD", "MQTT_PASSWORD"))
    
    # Tópicos MQTT
    TOPIC_TELEMETRIA_CLIMA: str = "invernadero/telemetria/microclima"
    TOPIC_TELEMETRIA_PID: str = "invernadero/telemetria/pid"
    TOPIC_CONTROL_SETPOINTS: str = "invernadero/control/setpoints"
    TOPIC_CONTROL_GANANCIAS: str = "invernadero/control/ganancias"
    TOPIC_VISION_DETECCIONES: str = "invernadero/vision/detecciones"
    TOPIC_RIESGO_INDICE: str = "invernadero/riesgo/indice"
    TOPIC_ALARMAS: str = "invernadero/alarmas/eventos"
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Visión Artificial
    MODEL_WEIGHTS_PATH: str = str(BASE_DIR / "data" / "models" / "yolo11n_papa.pt")
    UPLOAD_DIR: str = str(BASE_DIR / "data" / "raw" / "uploads")
    
    # InfluxDB v2
    INFLUXDB_URL: str = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    INFLUXDB_TOKEN: str = os.getenv("INFLUXDB_TOKEN", "my-super-secret-admin-auth-token-tesis-2026-lapaz-bolivia")
    INFLUXDB_ORG: str = os.getenv("INFLUXDB_ORG", "agri_iot_tesis")
    INFLUXDB_BUCKET: str = os.getenv("INFLUXDB_BUCKET", "invernadero_data")

settings = Settings()
