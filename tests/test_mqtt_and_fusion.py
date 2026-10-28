import json
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from server.app.core.config import settings
from server.app.worker import SupervisorWorker
from server.app.services.mqtt_client import MQTTClientService


def climate(worker, stamp, humidity=65, valid=True):
    worker._on_message(None, None, SimpleNamespace(topic=settings.TOPIC_TELEMETRIA_CLIMA,
        payload=json.dumps({'timestamp': stamp, 'temp_aire': 18, 'hum_aire': humidity,
                            'vpd_kpa': 0.1 if humidity >= 90 else 0.8, 'sensores_ok': valid}).encode()))


def test_supervisor_fusion_riesgo_bajo():
    worker = SupervisorWorker()
    climate(worker, time.time())
    assert worker.calcular_fusion_multimodal()[1] == 'BAJO'


def test_supervisor_fusion_riesgo_critico(monkeypatch):
    worker = SupervisorWorker()
    start = time.time() - 11 * 3600
    # Eleven real hours of wet readings, not eleven messages labelled as hours.
    for step in range(11 * 3600 // 20 + 1):
        stamp = start + step * 20
        with monkeypatch.context() as m:
            m.setattr('server.app.worker.time.time', lambda: stamp)
            climate(worker, stamp, 95)
    worker.ultima_deteccion_vision = {'timestamp': time.time(), 'severidad_porcentaje': 100, 'conteo_insectos': 25}
    assert worker.calcular_fusion_multimodal()[1] == 'CRÍTICO'
    assert worker.wet_hours == pytest.approx(11)


def test_one_second_messages_are_not_hours():
    worker = SupervisorWorker()
    now = time.time()
    for step in range(48):
        climate(worker, now - 20 + step * 0.4, 95)
    assert worker.wet_hours < 0.01
    assert len(worker.buffer_clima) <= 2


def test_stale_climate_blocks_commands(monkeypatch):
    worker = SupervisorWorker()
    now = time.time()
    climate(worker, now)
    monkeypatch.setattr('server.app.worker.time.time', lambda: now + 60)
    assert worker.calcular_fusion_multimodal()[1] == 'SIN_DATOS'


def test_invalid_sensor_invalidates_previous_state():
    worker = SupervisorWorker()
    now = time.time()
    climate(worker, now - 1)
    climate(worker, now, valid=False)
    assert worker.calcular_fusion_multimodal()[1] == 'SIN_DATOS'


def test_stale_vision_is_ignored():
    worker = SupervisorWorker()
    climate(worker, time.time())
    worker.ultima_deteccion_vision = {'timestamp': 1, 'severidad_porcentaje': 100, 'conteo_insectos': 25}
    assert worker.calcular_fusion_multimodal()[1] == 'BAJO'


def test_mqtt_client_serialization():
    client = MQTTClientService()
    assert client.publicar('test/topic', {'temp': 20}) is False


def test_v2_disconnect_callback():
    service = MQTTClientService()
    service.conectado = True
    service._on_disconnect(None, None, object(), 0, None)
    assert not service.conectado


@pytest.mark.asyncio
async def test_supervisor_retries_and_restores(monkeypatch):
    import server.app.worker as module
    worker = SupervisorWorker()
    worker.transport.publicar = Mock(return_value=True)
    publish = AsyncMock(side_effect=[{'publicado_mqtt': False}, {'publicado_mqtt': True}, {'publicado_mqtt': True}])
    monkeypatch.setattr(module, 'comandar_control', publish)
    monkeypatch.setattr(module.telegram_service, 'enviar_alerta_con_foto', AsyncMock(return_value={'status': 'error'}))
    monkeypatch.setattr(module.db_service, 'registrar_evento_alarma', AsyncMock())
    monkeypatch.setattr(worker, 'calcular_fusion_multimodal', lambda: (0.7, 'ALTO', 19.5, 65, 'risk'))
    await worker.evaluar_ciclo()
    assert worker.applied_level is None
    await worker.evaluar_ciclo()
    assert worker.applied_level == 'ALTO'
    monkeypatch.setattr(worker, 'calcular_fusion_multimodal', lambda: (0.1, 'BAJO', 18, 75, 'recovery'))
    monkeypatch.setattr(settings, 'SUPERVISOR_RECOVERY_SECONDS', 0)
    await worker.evaluar_ciclo()
    assert publish.call_args.args[0] == {'sp_temperatura': 18, 'sp_humedad': 75}
    assert worker.applied_level == 'BAJO'
    assert module.db_service.registrar_evento_alarma.call_args.kwargs['notificado_telegram'] is False
