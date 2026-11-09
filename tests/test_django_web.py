"""
Pruebas Unitarias e Integración para el Panel Web Django de Tesis
Verifica vistas, APIs interactivas, auditorías y exportación CSV.
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Configurar entorno Django
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "web"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "invernadero_web.settings")

import django
django.setup()

from django.test import Client
from dashboard.models import AuditoriaControlPID, ExperimentoEnsayo, DeteccionVision

@pytest.fixture
def client():
    return Client()

def test_django_index_view(client):
    """Verifica que la página principal cargue correctamente con código 200."""
    response = client.get("/")
    assert response.status_code == 200
    contenido = response.content.decode("utf-8")
    assert "AgriControl IoT" in contenido
    assert "Temp. Interior" in contenido
    assert "Déficit Presión (VPD)" in contenido

def test_django_control_pid_view(client):
    """Verifica vista de control PID y setpoints."""
    response = client.get("/control-pid/")
    assert response.status_code == 200
    contenido = response.content.decode("utf-8")
    assert "Control PID" in contenido
    assert "Cohen-Coon" in contenido or "Optuna" in contenido

def test_django_vision_view(client):
    """Verifica vista de visión artificial YOLO26 y compatibilidad YOLO11."""
    response = client.get("/vision/")
    assert response.status_code == 200
    contenido = response.content.decode("utf-8")
    assert "YOLO26" in contenido
    assert "YOLO11" in contenido
    assert "SAHI" in contenido

def test_django_gemelo_digital_view(client):
    """Verifica vista del gemelo digital y esquema 2D."""
    response = client.get("/gemelo-digital/")
    assert response.status_code == 200
    contenido = response.content.decode("utf-8")
    assert "Gemelo Digital" in contenido
    assert "Inyector de Perturbaciones" in contenido

def test_django_experimentos_view(client):
    """Verifica vista de experimentos E1 a E8."""
    response = client.get("/experimentos/")
    assert response.status_code == 200
    contenido = response.content.decode("utf-8")
    assert "E1" in contenido
    assert "E8" in contenido

def test_django_exportar_csv(client):
    """Verifica exportación de ensayos en formato CSV."""
    response = client.get("/experimentos/exportar-csv/")
    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    contenido = response.content.decode("utf-8")
    assert "Codigo,Nombre Ensayo,Tratamiento" in contenido
    assert "E1" in contenido
    assert "E8" in contenido

def test_api_telemetria(client):
    """Verifica API JSON de telemetría dinámica."""
    response = client.get("/api/telemetria/")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "estado" in data
    assert "explicacion" in data
    assert "temp_interior" in data["estado"]
    assert "vpd_kpa" in data["estado"]

def test_api_actualizar_setpoints(client):
    """Verifica actualización de setpoints y auditoría."""
    payload = {
        "sp_temperatura": 19.5,
        "sp_humedad": 72.0,
        "justificacion": "Prueba Unitaria Pytest"
    }
    response = client.post(
        "/api/setpoints/",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["sp_temperatura"] == 19.5
    assert data["sp_humedad"] == 72.0

    # Comprobar registro en base de datos
    registro = AuditoriaControlPID.objects.filter(justificacion__contains="Prueba Unitaria Pytest").last()
    assert registro is not None
    assert registro.sp_nuevo == 19.5

def test_api_actualizar_pid(client):
    """Verifica actualización de ganancias PID."""
    payload = {"kp": 16.5, "ki": 0.140, "kd": 1.62}
    response = client.post(
        "/api/pid/",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["kp"] == 16.5

def test_api_autotune(client):
    """Verifica API de simulación de autotuning."""
    response = client.get("/api/autotune/?metodo=OPTUNA")
    assert response.status_code == 200
    data = response.json()
    assert "Optuna" in data["metodo"]
    assert "kp" in data
    assert "ki" in data
    assert "kd" in data

def test_api_modo_gemelo(client):
    """Verifica inyección de perturbación en el gemelo digital."""
    response = client.post(
        "/api/modo-gemelo/",
        data=json.dumps({"modo": "HELADA"}),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["modo"] == "HELADA"


def test_api_fenologia(client):
    """Verifica aplicación de perfil fenológico de la papa."""
    response = client.post(
        "/api/fenologia/",
        data=json.dumps({"fase": "TUBERIZACION"}),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["fase"] == "TUBERIZACION"
    assert data["perfil"]["sp_temperatura"] == 16.5


def test_api_modelos_vision(client):
    """Verifica endpoint de catálogo de modelos entrenados en Colab."""
    response = client.get("/api/modelos-vision/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["modelos"]) >= 3


def test_api_subir_imagen_muestra_real(client):
    """Verifica inferencia en vivo desde muestra verificada del dataset y generación de URL anotada."""
    response = client.post(
        "/api/subir-imagen/",
        data={
            "muestra_id": "plantdoc_tizon_tardio",
            "modelo_id": "yolo26n_plantdoc_detect",
            "tipo_origen": "HOJA_FOLLAJE",
            "usar_sahi": "false",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["clase_detectada"] == "tizon_tardio"
    assert data["url_anotada"].startswith("/media/anotada_")
    assert "recomendacion_mip" in data
    # Limpiar archivo temporal generado en MEDIA_ROOT durante el test
    Path(data["ruta_original"]).unlink(missing_ok=True)
    Path(data["ruta_anotada"]).unlink(missing_ok=True)
    DeteccionVision.objects.filter(id=data["id"]).delete()


def test_servir_figura_tesis(client):
    """Verifica servicio de figuras científicas desde thesis/figuras/."""
    response = client.get("/tesis-figura/fig_fopdt_ajuste_escalon.png/")
    assert response.status_code == 200
    assert response["Content-Type"] == "image/png"
    response.close()

