"""
Servicio del Bot de Telegram para Notificaciones de Alerta y Fotos
Proyecto de Tesis - Invernadero de Papa (La Paz, Bolivia)
"""

import os
import logging
import httpx
from pathlib import Path
from typing import Optional, Dict, Any
from server.app.core.config import settings

logger = logging.getLogger("telegram_bot")

class TelegramService:
    def __init__(self, token: str = settings.TELEGRAM_BOT_TOKEN, chat_id: str = settings.TELEGRAM_CHAT_ID):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""

    @property
    def esta_configurado(self) -> bool:
        if not self.token or not self.chat_id:
            return False
        token_str = str(self.token).lower()
        if "tu_" in token_str or "token" in token_str or token_str == "none":
            return False
        return True

    async def enviar_mensaje(self, texto: str, parse_mode: str = "Markdown") -> Dict[str, Any]:
        """
        Envía un mensaje de texto formateado a Telegram.
        Si las credenciales no están presentes, opera en modo simulación (mock).
        """
        if not self.esta_configurado:
            logger.info(f"[SIMULACIÓN TELEGRAM] Mensaje enviado a {self.chat_id or 'SIN_CHAT_ID'}:\n{texto}")
            return {"status": "mock_sent", "chat_id": self.chat_id, "texto": texto}

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": texto,
            "parse_mode": parse_mode
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Error al enviar mensaje a Telegram: {e}")
                return {"status": "error", "detalle": str(e)}

    async def enviar_alerta_con_foto(
        self,
        titulo: str,
        score_riesgo: float,
        nivel: str,
        clima_resumen: str,
        accion_recomendada: str,
        ruta_foto: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envía un reporte fitosanitario estructurado con fotografía adjunta anotada por YOLO+SAHI.
        """
        emojis = {
            "BAJO": "🟢",
            "MEDIO": "🟡",
            "ALTO": "🟠",
            "CRÍTICO": "🔴"
        }
        emoji = emojis.get(nivel.upper(), "⚠️")
        
        caption = (
            f"{emoji} *ALERTA FITOSANITARIA INVERNADERO PAPA*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"*Nivel:* `{nivel.upper()}` | *Score:* `{score_riesgo:.3f}`\n"
            f"*Evento:* {titulo}\n"
            f"*Condiciones Microclima:*\n{clima_resumen}\n"
            f"*Acción Automatizada:* {accion_recomendada}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 _Estación Experimental La Paz (~3600 msnm)_"
        )

        if not self.esta_configurado:
            logger.info(f"[SIMULACIÓN TELEGRAM CON FOTO] Foto: {ruta_foto}\nCaption:\n{caption}")
            return {"status": "mock_sent_with_photo", "ruta_foto": ruta_foto, "caption": caption}

        if ruta_foto and Path(ruta_foto).exists():
            url = f"{self.base_url}/sendPhoto"
            async with httpx.AsyncClient(timeout=20.0) as client:
                try:
                    with open(ruta_foto, "rb") as f:
                        files = {"photo": (Path(ruta_foto).name, f, "image/jpeg")}
                        data = {"chat_id": self.chat_id, "caption": caption, "parse_mode": "Markdown"}
                        resp = await client.post(url, data=data, files=files)
                        resp.raise_for_status()
                        return resp.json()
                except Exception as e:
                    logger.error(f"Error al enviar foto a Telegram: {e}. Reintentando solo texto.")
                    return await self.enviar_mensaje(caption)
        else:
            return await self.enviar_mensaje(caption)

telegram_service = TelegramService()
