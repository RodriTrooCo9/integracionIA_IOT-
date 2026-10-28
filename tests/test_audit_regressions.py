"""Regression cases reproducing the audit failures, without real devices or APIs."""
import io
import json
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from django.test import Client
from django.contrib.auth import get_user_model

from server.app.core.config import settings
from server.app.main import app
from server.app.services.vision_service import vision_service, VisionUnavailable
from server.app.services.storage import guardar_imagen, ImageValidationError
from server.app.services.mqtt_client import mqtt_service, MQTTClientService


def image_file(tmp_path, brown=False):
    hsv = np.full((100, 100, 3), (17, 180, 100) if brown else (60, 180, 100), dtype=np.uint8)
    path = tmp_path / 'leaf.png'
    cv2.imwrite(str(path), cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR))
    return path


def test_no_weights_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'VISION_DEMO_MODE', False)
    with pytest.raises(VisionUnavailable):
        vision_service.procesar_imagen(str(image_file(tmp_path)))


def test_heuristic_is_explicit_consistent_and_not_sahi(tmp_path):
    result = vision_service.procesar_imagen(str(image_file(tmp_path, True)), usar_sahi=True)
    assert result['simulado'] is True
    assert result['clase_detectada'] == 'tizon_tardio'
    assert result['severidad_porcentaje'] == 100
    assert result['conteo_insectos'] == 0
    assert result['procesado_con_sahi'] is False


def test_healthy_leaf_has_no_lesion_or_insects(tmp_path, monkeypatch):
    box = SimpleNamespace(cls=np.array([2]), conf=np.array([0.99]), xyxy=np.array([[0, 0, 100, 100]]))
    monkeypatch.setattr(vision_service, 'modelo', Mock(return_value=[SimpleNamespace(boxes=[box])]))
    result = vision_service.procesar_imagen(str(image_file(tmp_path)))
    assert result['clase_detectada'] == 'hoja_sana'
    assert result['severidad_porcentaje'] == 0
    assert result['conteo_insectos'] == 0


def test_overlapping_lesions_are_counted_once(tmp_path, monkeypatch):
    boxes = [SimpleNamespace(cls=np.array([0]), conf=np.array([0.9]), xyxy=np.array([[0, 0, 50, 50]])) for _ in range(2)]
    monkeypatch.setattr(vision_service, 'modelo', Mock(return_value=[SimpleNamespace(boxes=boxes)]))
    result = vision_service.procesar_imagen(str(image_file(tmp_path)))
    assert result['severidad_porcentaje'] == 25


def test_simulation_does_not_publish_or_alert(tmp_path, monkeypatch):
    publish = Mock(return_value=True)
    monkeypatch.setattr(mqtt_service, 'publicar', publish)
    client = TestClient(app, headers={'X-API-Key': 'test-operator-key'})
    response = client.post('/api/v1/vision/inferir', files={'imagen': ('leaf.png', image_file(tmp_path, True).read_bytes(), 'image/png')})
    assert response.status_code == 200
    assert response.json()['publicado_mqtt'] is False
    assert response.json()['alerta_telegram_disparada'] is False
    publish.assert_not_called()


def test_fastapi_control_rejects_unauthenticated_request():
    response = TestClient(app).post('/api/v1/control/setpoints', json={'sp_temperatura': 18, 'sp_humedad': 75})
    assert response.status_code == 401


def test_failed_publish_reports_unavailable(monkeypatch):
    monkeypatch.setattr(mqtt_service, 'publicar', lambda *a, **kw: False)
    response = TestClient(app, headers={'X-API-Key': 'test-operator-key'}).post(
        '/api/v1/control/setpoints', json={'sp_temperatura': 18, 'sp_humedad': 75})
    assert response.status_code == 503
    assert response.json()['detail']['aplicado_confirmado'] is False


def test_django_requires_staff_and_csrf():
    client = Client()
    payload = json.dumps({'sp_temperatura': 18, 'sp_humedad': 75})
    assert client.post('/api/setpoints/', payload, content_type='application/json').status_code == 401
    User = get_user_model()
    user, _ = User.objects.get_or_create(username='audit-reader')
    client.force_login(user)
    assert client.post('/api/setpoints/', payload, content_type='application/json').status_code == 403
    user.is_staff = True
    user.save()
    secure = Client(enforce_csrf_checks=True)
    secure.force_login(user)
    assert secure.post('/api/setpoints/', payload, content_type='application/json').status_code == 403
    secure.get('/control-pid/')
    token = secure.cookies['csrftoken'].value
    assert secure.post('/api/setpoints/', payload, content_type='application/json', HTTP_X_CSRFTOKEN=token).status_code == 200


def test_pid_rejects_nan_negative_and_extreme_gains():
    client = Client()
    user, _ = get_user_model().objects.get_or_create(username='audit-staff', defaults={'is_staff': True})
    client.force_login(user)
    for bad in [float('nan'), float('inf'), -1, 10001]:
        response = client.post('/api/pid/', json.dumps({'kp': bad, 'ki': 0.1, 'kd': 1}), content_type='application/json')
        assert response.status_code == 400


def test_storage_uses_unique_names_and_checks_content(tmp_path):
    data = image_file(tmp_path).read_bytes()
    first, second = guardar_imagen(io.BytesIO(data)), guardar_imagen(io.BytesIO(data))
    assert first != second
    with pytest.raises(ImageValidationError):
        guardar_imagen(io.BytesIO(b'not an image'))


def test_seed_is_idempotent():
    from scripts.seed_experiments import poblar_ensayos
    from dashboard.models import ExperimentoEnsayo
    before = ExperimentoEnsayo.objects.count()
    poblar_ensayos()
    poblar_ensayos()
    assert ExperimentoEnsayo.objects.count() == before


def test_visitor_count_does_not_advance_simulation(monkeypatch):
    from dashboard import services
    monkeypatch.setattr(services, '_gemelo_last_step', time.monotonic())
    one = services.actualizar_gemelo_digital()
    for _ in range(20):
        two = services.actualizar_gemelo_digital()
    assert one['temp_interior'] == two['temp_interior']


def test_mqtt_waits_for_broker_ack():
    service = MQTTClientService()
    service.conectado = True
    info = Mock(rc=0)
    info.is_published.return_value = False
    service.client.publish = Mock(return_value=info)
    assert service.publicar('test/ack', {}) is False
    info.wait_for_publish.assert_called_once()


def test_sahi_counts_lesion_area(tmp_path, monkeypatch):
    import sys
    from types import ModuleType
    prediction = SimpleNamespace(category=SimpleNamespace(id=0), score=SimpleNamespace(value=0.9),
                                 bbox=SimpleNamespace(minx=0, miny=0, maxx=50, maxy=50))
    fake = ModuleType('sahi.predict')
    fake.get_sliced_prediction = lambda *a, **kw: SimpleNamespace(object_prediction_list=[prediction])
    monkeypatch.setitem(sys.modules, 'sahi', ModuleType('sahi'))
    monkeypatch.setitem(sys.modules, 'sahi.predict', fake)
    monkeypatch.setattr(vision_service, 'modelo', Mock())
    monkeypatch.setattr(vision_service, 'sahi_model', Mock())
    result = vision_service.procesar_imagen(str(image_file(tmp_path)), usar_sahi=True)
    assert result['procesado_con_sahi'] is True
    assert result['severidad_porcentaje'] == 25


def test_incompatible_weights_are_rejected(tmp_path, monkeypatch):
    import sys
    from types import ModuleType
    from server.app.services.vision_service import VisionInferenceService
    module = ModuleType('ultralytics')
    module.YOLO = Mock(return_value=SimpleNamespace(names={0: 'person', 1: 'bicycle'}))
    monkeypatch.setitem(sys.modules, 'ultralytics', module)
    weights = tmp_path / 'wrong.pt'
    weights.touch()
    service = VisionInferenceService(weights)
    assert service.modelo is None
    module.YOLO.assert_called_once_with(str(weights))


def test_django_real_detection_publishes_event(tmp_path, monkeypatch):
    box = SimpleNamespace(cls=np.array([2]), conf=np.array([0.99]), xyxy=np.array([[0, 0, 100, 100]]))
    monkeypatch.setattr(vision_service, 'modelo', Mock(return_value=[SimpleNamespace(boxes=[box])]))
    publish = Mock(return_value=True)
    monkeypatch.setattr(mqtt_service, 'publicar', publish)
    client = Client()
    user, _ = get_user_model().objects.get_or_create(username='vision-staff', defaults={'is_staff': True})
    client.force_login(user)
    with image_file(tmp_path).open('rb') as image:
        response = client.post('/api/subir-imagen/', {'imagen': image, 'tipo_origen': 'HOJA_FOLLAJE'})
    assert response.status_code == 200
    assert response.json()['simulado'] is False
    assert publish.call_args.args[0] == settings.TOPIC_VISION_DETECCIONES
    image_url = response.json()['ruta_anotada']
    image_response = client.get(image_url)
    assert image_response.status_code == 200
    image_response.close()


@pytest.mark.asyncio
async def test_audit_tracks_previous_published_value_and_failures(monkeypatch):
    from server.app.services.operations import comandar_control
    from server.app.services.database import db_service
    await comandar_control({'sp_temperatura': 20}, 'TEST_AUDIT', 'first')
    await comandar_control({'sp_temperatura': 21}, 'TEST_AUDIT', 'second')
    monkeypatch.setattr(mqtt_service, 'publicar', lambda *a, **kw: False)
    await comandar_control({'sp_temperatura': 22}, 'TEST_AUDIT', 'third')
    async with db_service.get_connection() as conn:
        cursor = await conn.execute("SELECT sp_anterior,sp_nuevo FROM auditoria_control_pid WHERE usuario_origen='TEST_AUDIT' ORDER BY id")
        rows = await cursor.fetchall()
    assert tuple(rows[-2]) == (20, 21)
    assert tuple(rows[-1]) == (21, 22)
    assert await db_service.obtener_control_publicado('sp_temperatura') == 21


def test_bootstrap_preserves_legacy_audits_and_allows_unknown_previous(tmp_path):
    import sqlite3
    from server.app.services.bootstrap import inicializar_db
    path = tmp_path / 'legacy.db'
    legacy_schema = (Path(__file__).resolve().parents[1] / 'server/app/models/schemas.sql').read_text().replace('sp_anterior REAL,', 'sp_anterior REAL NOT NULL,')
    with sqlite3.connect(path) as conn:
        conn.executescript(legacy_schema)
        conn.execute("INSERT INTO auditoria_control_pid(variable_control,sp_anterior,sp_nuevo) VALUES ('TEMP',18,20)")
    inicializar_db(path)
    inicializar_db(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT sp_nuevo FROM auditoria_control_pid').fetchone() == (20,)
        conn.execute("INSERT INTO auditoria_control_pid(variable_control,sp_anterior,sp_nuevo) VALUES ('TEMP',NULL,21)")


def test_firmware_safety_guards(tmp_path):
    import shutil
    import subprocess
    compiler = shutil.which('g++')
    if not compiler:
        pytest.skip('g++ required for native firmware safety regression')
    include = Path(__file__).resolve().parents[1] / 'firmware/esp32_control/include'
    source = tmp_path / 'safety.cpp'
    source.write_text('''#include "control_safety.h"
#include <cassert>
int main() {
    assert(!lectura_aire_valida(NAN, 70));
    assert(!lectura_aire_valida(18, INFINITY));
    assert(!control_habilitado(true, false, 0));
    assert(!control_habilitado(false, true, 0));
    assert(!control_habilitado(true, true, 2001));
    assert(control_habilitado(true, true, 100));
    assert(!setpoints_validos(50, 75));
    assert(!ganancias_validas(-1, 0, 0));
    assert(!ganancias_validas(10, NAN, 0));
}''')
    binary = tmp_path / 'safety'
    subprocess.run([compiler, '-std=c++11', '-I', str(include), str(source), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)


def test_repo_mqtt_credentials_match_broker_hashes():
    import base64
    import hashlib
    import hmac
    from dotenv import dotenv_values
    root = Path(__file__).resolve().parents[1]
    env = dotenv_values(root / '.env.example')
    passwords = {'esp32_nodo': env['ESP32_MQTT_PASSWORD'],
                 'fastapi_server': env['BACKEND_MQTT_PASSWORD'],
                 'telegraf_worker': env['TELEGRAF_MQTT_PASSWORD']}
    for line in (root / 'config/mosquitto/passwd').read_text().splitlines():
        user, encoded = line.split(':', 1)
        if user in passwords:
            _, _, iterations, salt, expected = encoded.split('$')
            actual = hashlib.pbkdf2_hmac('sha512', passwords[user].encode(), base64.b64decode(salt), int(iterations))
            assert hmac.compare_digest(actual, base64.b64decode(expected)), f'Credenciales incoherentes: {user}'


def test_firmware_and_server_share_command_contract():
    import re
    root = Path(__file__).resolve().parents[1]
    header = (root / 'firmware/esp32_control/include/config_invernadero.h').read_text()
    firmware = (root / 'firmware/esp32_control/src/main.cpp').read_text()
    topic = re.search(r'#define TOPIC_CONTROL_SP\s+"([^"]+)"', header).group(1)
    gains = re.search(r'#define TOPIC_CONTROL_GANANCIAS\s+"([^"]+)"', header).group(1)
    assert topic == settings.TOPIC_CONTROL_SETPOINTS
    assert gains == settings.TOPIC_CONTROL_GANANCIAS
    from server.app.services.operations import command_payload
    payload = command_payload({'sp_temperatura': 20, 'sp_humedad': 70}, 'TEST')
    for key in ['sp_temperatura', 'sp_humedad', 'command_id', 'expires_at']:
        assert f'doc["{key}"]' in firmware
        assert key in payload
    assert payload['expires_at'] > time.time()


def test_unauthorized_upload_rejected_before_multipart_parsing():
    response = TestClient(app).post('/api/v1/vision/inferir', content=b'invalid-multipart',
                                    headers={'Content-Type': 'multipart/form-data; boundary=missing'})
    assert response.status_code == 401


def test_oversized_multipart_body_is_bounded(monkeypatch):
    monkeypatch.setattr(settings, 'MAX_UPLOAD_BYTES', 1024)
    response = TestClient(app, headers={'X-API-Key': 'test-operator-key'}).post(
        '/api/v1/vision/inferir', files={'imagen': ('big.png', b'x' * 70000, 'image/png')})
    assert response.status_code == 413


def test_django_upload_stops_oversized_file(monkeypatch):
    from django.core.files.uploadedfile import SimpleUploadedFile
    monkeypatch.setattr(settings, 'MAX_UPLOAD_BYTES', 1024)
    client = Client()
    user, _ = get_user_model().objects.get_or_create(username='upload-staff', defaults={'is_staff': True})
    client.force_login(user)
    response = client.post('/api/subir-imagen/', {'imagen': SimpleUploadedFile('large.png', b'x' * 70000)})
    assert response.status_code == 400
