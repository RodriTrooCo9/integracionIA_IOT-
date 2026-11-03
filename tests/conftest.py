"""Use a disposable database/media directory and never contact greenhouse services."""
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
_test_directory = tempfile.TemporaryDirectory(prefix='iot-pytest-')
_test_root = Path(_test_directory.name)
os.environ.update(
    SQLITE_DB_PATH=str(_test_root / 'test.db'), UPLOAD_DIR=str(_test_root / 'uploads'),
    MODEL_WEIGHTS_PATH=str(_test_root / 'untrained-yolo26.pt'), VISION_DEMO_MODE='false',
    TELEGRAM_BOT_TOKEN='', TELEGRAM_CHAT_ID='', MQTT_BROKER_HOST='127.0.0.1',
)
with sqlite3.connect(os.environ['SQLITE_DB_PATH']) as connection:
    connection.executescript((ROOT / 'server/app/models/schemas.sql').read_text())

sys.path.insert(0, str(ROOT / 'web'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'invernadero_web.settings'
from django.conf import settings as django_settings

django_settings.DATABASES['default']['NAME'] = os.environ['SQLITE_DB_PATH']
django_settings.MEDIA_ROOT = os.environ['UPLOAD_DIR']
import django
django.setup()
from scripts import seed_experiments
seed_experiments.DB_PATH = Path(os.environ['SQLITE_DB_PATH'])
seed_experiments.poblar_ensayos()


@pytest.fixture(autouse=True)
def no_external_services(monkeypatch):
    from server.app.services.mqtt_client import mqtt_service
    monkeypatch.setattr(mqtt_service, 'iniciar', lambda: None)
    monkeypatch.setattr(mqtt_service, 'publicar', lambda *args, **kwargs: False)


def pytest_sessionfinish(session, exitstatus):
    from django.db import connections
    connections.close_all()
    _test_directory.cleanup()
