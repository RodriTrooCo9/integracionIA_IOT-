"""
Pruebas Unitarias y de Integración para Endpoints FastAPI
Proyecto de Tesis - Invernadero de Papa
"""

import io
import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient
from server.app.main import app
from server.app.core.config import settings

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "La Paz, Bolivia" in data["ubicacion"]
    assert data["docs"] == "/docs"

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["sqlite_db"] is True
    assert "timestamp_utc" in data

def test_actualizar_setpoints_valido():
    payload = {
        "sp_temperatura": 19.5,
        "sp_humedad": 68.0,
        "usuario_origen": "TEST_UNITARIO",
        "justificacion": "Prueba de setpoints control PID"
    }
    response = client.post("/api/v1/control/setpoints", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["sp_temperatura"] == 19.5
    assert data["sp_humedad"] == 68.0

def test_actualizar_setpoints_invalido():
    # Temperatura fuera de rango agronómico (50°C > 35°C máximo permitido)
    payload = {
        "sp_temperatura": 50.0,
        "sp_humedad": 70.0,
        "usuario_origen": "TEST_INVALIDO"
    }
    response = client.post("/api/v1/control/setpoints", json=payload)
    assert response.status_code == 422 # Error de validación Pydantic

def test_inferencia_vision_endpoint():
    # Crear imagen sintética en memoria (100x100 RGB)
    img_array = np.zeros((100, 100, 3), dtype=np.uint8)
    img_array[:] = (34, 139, 34) # Color verde hoja
    # Añadir parche de lesión marrón
    cv2.rectangle(img_array, (20, 20), (60, 60), (19, 69, 139), -1)
    
    _, img_encoded = cv2.imencode(".jpg", img_array)
    img_bytes = io.BytesIO(img_encoded.tobytes())

    response = client.post(
        "/api/v1/vision/inferir",
        files={"imagen": ("hoja_prueba.jpg", img_bytes, "image/jpeg")},
        data={"nodo_camara": "cam_test_01", "tipo_origen": "HOJA_FOLLAJE", "usar_sahi": "false"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["resultado"]["clase_detectada"], str)
    assert len(data["resultado"]["clase_detectada"]) > 0
    assert "tiempo_inferencia_ms" in data["resultado"]

def test_historial_vision():
    response = client.get("/api/v1/vision/historial?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_historial_alertas():
    response = client.get("/api/v1/alertas?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
