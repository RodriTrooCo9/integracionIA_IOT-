"""
Pruebas Unitarias para el Lazo Supervisor de Fusión y Mensajería MQTT
Proyecto de Tesis - Invernadero de Papa
"""

import pytest
import numpy as np
from server.app.worker import SupervisorWorker
from server.app.services.mqtt_client import MQTTClientService

def test_supervisor_fusion_riesgo_bajo():
    worker = SupervisorWorker()
    # Sin detecciones ni alta humedad
    worker.buffer_clima.clear()
    for _ in range(12):
        worker.buffer_clima.append({
            "temp_in": 18.5,
            "hum_in": 65.0,
            "vpd_kpa": 0.85,
            "lwh": 2.0
        })
    worker.ultima_deteccion_vision = {
        "severidad_porcentaje": 0.0,
        "conteo_insectos": 0,
        "timestamp": 0
    }
    score, nivel, sp_t, sp_h, accion = worker.calcular_fusion_multimodal()
    assert score < 0.30
    assert nivel == "BAJO"
    assert sp_t == 18.0
    assert sp_h == 75.0

def test_supervisor_fusion_riesgo_critico():
    worker = SupervisorWorker()
    # Simular temporal severo y alta severidad fúngica
    worker.buffer_clima.clear()
    for _ in range(12):
        worker.buffer_clima.append({
            "temp_in": 16.0,
            "hum_in": 95.0,
            "vpd_kpa": 0.10,
            "lwh": 18.0
        })
    worker.ultima_deteccion_vision = {
        "severidad_porcentaje": 28.5,
        "conteo_insectos": 15,
        "timestamp": 0
    }
    score, nivel, sp_t, sp_h, accion = worker.calcular_fusion_multimodal()
    assert score >= 0.70
    assert nivel in ["ALTO", "CRÍTICO"]
    assert sp_t >= 19.5
    assert sp_h <= 65.0
    assert "deshumidificación" in accion.lower() or "choque" in accion.lower()

def test_mqtt_client_serialization():
    client = MQTTClientService()
    # Verificar que el método de formateo y publicación no falle con diccionarios
    payload = {"temp": 20.0, "hum": 60.0}
    # En entorno desconectado, retornar False de forma segura sin excepciones no controladas
    res = client.publicar("test/topico", payload)
    assert isinstance(res, bool)
