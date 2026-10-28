"""
Servicio Asíncrono de Persistencia Relacional (SQLite + aiosqlite)
Proyecto de Tesis - Invernadero de Papa
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiosqlite

from server.app.core.config import settings

class DatabaseService:
    def __init__(self, db_path: str = settings.SQLITE_DB_PATH):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    @asynccontextmanager
    async def get_connection(self):
        conn = await aiosqlite.connect(self.db_path, timeout=15)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            await conn.close()

    async def registrar_deteccion(
        self,
        nodo_camara: str,
        tipo_origen: str,
        ruta_original: str,
        ruta_anotada: Optional[str],
        clase_detectada: str,
        confianza: float,
        bbox_json: str,
        conteo_insectos: int = 1,
        severidad_porcentaje: float = 0.0,
        tiempo_inferencia_ms: float = 0.0,
        procesado_con_sahi: bool = False,
        simulado: bool = True,
        motor: str = "desconocido"
    ) -> int:
        async with self.get_connection() as conn:
            # Auto-registrar el nodo de cámara si aún no existe en nodos_sensores
            await conn.execute(
                """
                INSERT OR IGNORE INTO nodos_sensores (nodo_id, nombre, descripcion)
                VALUES (?, 'Cámara Invernadero', 'Dispositivo de captura de visión artificial');
                """,
                (nodo_camara,)
            )
            cursor = await conn.execute(
                """
                INSERT INTO detecciones_vision (
                    nodo_camara, tipo_origen, ruta_imagen_original, ruta_imagen_anotada,
                    clase_detectada, confianza, bbox_json, conteo_insectos,
                    severidad_porcentaje, tiempo_inferencia_ms, procesado_con_sahi, simulado, motor
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    nodo_camara, tipo_origen, ruta_original, ruta_anotada,
                    clase_detectada, confianza, bbox_json, conteo_insectos,
                    severidad_porcentaje, tiempo_inferencia_ms, int(procesado_con_sahi), int(simulado), motor
                )
            )
            await conn.commit()
            return cursor.lastrowid

    async def registrar_evento_alarma(
        self,
        tipo_evento: str,
        nivel_severidad: str,
        mensaje: str,
        valor_disparador: Optional[float] = None,
        accion_ejecutada: Optional[str] = None,
        notificado_telegram: bool = False
    ) -> int:
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                """
                INSERT INTO eventos_alarmas (
                    tipo_evento, nivel_severidad, mensaje,
                    valor_disparador, accion_ejecutada, notificado_telegram
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    tipo_evento, nivel_severidad, mensaje,
                    valor_disparador, accion_ejecutada, int(notificado_telegram)
                )
            )
            await conn.commit()
            return cursor.lastrowid

    async def registrar_auditoria_setpoint(
        self,
        variable_control: str,
        sp_anterior: Optional[float],
        sp_nuevo: float,
        usuario_origen: str = "SISTEMA_IA",
        kp: Optional[float] = None,
        ki: Optional[float] = None,
        kd: Optional[float] = None,
        justificacion: Optional[str] = None
    ) -> int:
        async with self.get_connection() as conn:
            cursor = await conn.execute(
                """
                INSERT INTO auditoria_control_pid (
                    usuario_origen, variable_control, sp_anterior, sp_nuevo,
                    kp, ki, kd, justificacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    usuario_origen, variable_control, sp_anterior, sp_nuevo,
                    kp, ki, kd, justificacion
                )
            )
            await conn.commit()
            return cursor.lastrowid

    async def obtener_control_publicado(self, variable):
        async with self.get_connection() as conn:
            cursor = await conn.execute("SELECT valor FROM control_publicado WHERE variable=?", (variable,))
            row = await cursor.fetchone()
            return row[0] if row else None

    async def guardar_control_publicado(self, variables):
        async with self.get_connection() as conn:
            for variable, value in variables.items():
                await conn.execute("""INSERT INTO control_publicado(variable,valor) VALUES (?,?)
                    ON CONFLICT(variable) DO UPDATE SET valor=excluded.valor,timestamp=CURRENT_TIMESTAMP""",
                    (variable, value))
            await conn.commit()

    async def obtener_ultimas_detecciones(self, limit: int = 20) -> List[Dict[str, Any]]:
        async with self.get_connection() as conn:
            async with conn.execute(
                """
                SELECT id, timestamp, nodo_camara, tipo_origen, clase_detectada,
                       confianza, conteo_insectos, severidad_porcentaje,
                       tiempo_inferencia_ms, procesado_con_sahi, simulado, motor
                FROM detecciones_vision
                ORDER BY timestamp DESC
                LIMIT ?;
                """,
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def obtener_ultimas_alarmas(self, limit: int = 20) -> List[Dict[str, Any]]:
        async with self.get_connection() as conn:
            async with conn.execute(
                """
                SELECT id, timestamp, tipo_evento, nivel_severidad, mensaje,
                       valor_disparador, accion_ejecutada, notificado_telegram
                FROM eventos_alarmas
                ORDER BY timestamp DESC
                LIMIT ?;
                """,
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

db_service = DatabaseService()
