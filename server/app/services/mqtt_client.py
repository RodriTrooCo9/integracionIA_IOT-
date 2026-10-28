"""
Cliente Asíncrono / Threaded de Comunicación MQTT (paho-mqtt)
Proyecto de Tesis - Invernadero de Papa
"""

import json
import logging
import threading
import os
from uuid import uuid4
from typing import Dict, Any, Optional, Callable
import paho.mqtt.client as mqtt
from server.app.core.config import settings

logger = logging.getLogger("mqtt_client")

class MQTTClientService:
    def __init__(self):
        self.host = settings.MQTT_BROKER_HOST
        self.port = settings.MQTT_BROKER_PORT
        self.username = settings.MQTT_USERNAME
        self.password = settings.MQTT_PASSWORD
        
        self._started = False
        self._start_lock = threading.Lock()
        self._client_id = f"backend_{os.getpid()}_{uuid4().hex[:8]}"
        # Compatibilidad con paho-mqtt v1 y v2
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self._client_id)
        except AttributeError:
            self.client = mqtt.Client(client_id=self._client_id)
            
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
            
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.conectado = False
        self._suscripciones = {}

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.conectado = True
            logger.info(f"[MQTT] Conectado exitosamente al broker {self.host}:{self.port}")
            # Resuscribir tópicos
            for topico, qos in self._suscripciones.items():
                self.client.subscribe(topico, qos=qos)
        else:
            self.conectado = False
            logger.warning(f"[MQTT] Fallo de conexión al broker. Código retorno: {rc}")

    def _on_disconnect(self, client, userdata, *args):
        rc = args[-2] if len(args) == 3 else args[0]
        self.conectado = False
        logger.warning(f"[MQTT] Desconectado del broker (código {rc}). Intentando reconexión automática...")

    def iniciar(self):
        """Inicia el bucle de red en segundo plano (non-blocking)."""
        with self._start_lock:
            if self._started:
                return
            self.client.connect_async(self.host, self.port, keepalive=60)
            self.client.loop_start()
            self._started = True

    def detener(self):
        with self._start_lock:
            if self._started:
                self.client.disconnect()
                self.client.loop_stop()
                self._started = False
            self.conectado = False

    def publicar(self, topico: str, payload: Any, qos: int = 1, retain: bool = False) -> bool:
        """
        Publica un payload JSON o string en el tópico MQTT especificado.
        """
        try:
            if not self.conectado:
                return False
            if isinstance(payload, (dict, list)):
                msg_str = json.dumps(payload)
            else:
                msg_str = str(payload)
            res = self.client.publish(topico, msg_str, qos=qos, retain=retain)
            if res.rc != mqtt.MQTT_ERR_SUCCESS:
                return False
            res.wait_for_publish(timeout=3.0)
            return res.is_published()
        except Exception as e:
            logger.error(f"[MQTT] Error publicando en {topico}: {e}")
            return False

    def suscribir(self, topico: str, callback: Callable, qos: int = 1):
        self._suscripciones[topico] = qos
        self.client.message_callback_add(topico, callback)
        if self.conectado:
            self.client.subscribe(topico, qos=qos)

mqtt_service = MQTTClientService()
