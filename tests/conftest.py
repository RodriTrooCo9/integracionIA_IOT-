"""Isolate the entire test session before importing application singletons."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

_workspace = Path(__file__).resolve().parent.parent
_test_directory = tempfile.TemporaryDirectory(prefix='iot-pytest-')
os.environ.update(
    SQLITE_DB_PATH=str(Path(_test_directory.name) / 'test.db'),
    UPLOAD_DIR=str(Path(_test_directory.name) / 'uploads'),
    API_KEY='test-operator-key', DJANGO_SECRET_KEY='test-key-only-not-used-outside-tests',
    DJANGO_ALLOWED_HOSTS='testserver,localhost,127.0.0.1',
    TELEGRAM_BOT_TOKEN='', TELEGRAM_CHAT_ID='', VISION_DEMO_MODE='true',
    MQTT_BROKER_HOST='127.0.0.1',
)
sys.path.insert(0, str(_workspace / 'web'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'invernadero_web.settings'
from server.app.services.bootstrap import inicializar_db
inicializar_db()
import django
django.setup()
from django.core.management import call_command
call_command('migrate', run_syncdb=True, verbosity=0)
from scripts.seed_experiments import poblar_ensayos
poblar_ensayos()


@pytest.fixture(autouse=True)
def isolate_external_services(monkeypatch):
    from server.app.services.mqtt_client import mqtt_service
    from server.app.services.vision_service import vision_service
    from server.app.services.telegram_bot import telegram_service
    monkeypatch.setattr(mqtt_service, 'iniciar', lambda: None)
    monkeypatch.setattr(mqtt_service, 'publicar', lambda *args, **kwargs: True)
    monkeypatch.setattr(vision_service, 'modelo', None)
    monkeypatch.setattr(vision_service, 'sahi_model', None)
    monkeypatch.setattr(telegram_service, 'token', '')


def pytest_sessionfinish(session, exitstatus):
    from django.db import connections
    connections.close_all()
    _test_directory.cleanup()
