"""
Pruebas Unitarias para el Servicio de Notificaciones de Telegram
Proyecto de Tesis - Invernadero de Papa
"""

import pytest
import tempfile
from pathlib import Path
from server.app.services.telegram_bot import TelegramService

@pytest.mark.asyncio
async def test_telegram_mock_envio_mensaje():
    # Instancia sin token real para pruebas locales / CI
    tg = TelegramService(token="", chat_id="123456789")
    assert tg.esta_configurado is False
    
    resp = await tg.enviar_mensaje("Alerta de prueba unitaria")
    assert resp["status"] == "mock_sent"
    assert "Alerta de prueba" in resp["texto"]

@pytest.mark.asyncio
async def test_telegram_mock_envio_foto():
    tg = TelegramService(token="", chat_id="123456789")
    
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(b"fake_image_bytes")
        tmp_path = tmp.name

    try:
        resp = await tg.enviar_alerta_con_foto(
            titulo="Brote de Tizón Tardío",
            score_riesgo=0.88,
            nivel="CRÍTICO",
            clima_resumen="• Humedad: 96%\n• LWH: 16h",
            accion_recomendada="Deshumidificación forzada inmediata.",
            ruta_foto=tmp_path
        )
        assert resp["status"] == "mock_sent_with_photo"
        assert resp["ruta_foto"] == tmp_path
        assert "CRÍTICO" in resp["caption"]
        assert "0.880" in resp["caption"]
    finally:
        Path(tmp_path).unlink(missing_ok=True)
