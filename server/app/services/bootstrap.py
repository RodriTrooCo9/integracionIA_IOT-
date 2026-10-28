"""Idempotent schema initialization, also usable by Docker and Django."""
import sqlite3
from pathlib import Path
from server.app.core.config import settings, BASE_DIR


def inicializar_db(path=None):
    path = Path(path or settings.SQLITE_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path, timeout=15) as conn:
        conn.executescript((BASE_DIR / 'server/app/models/schemas.sql').read_text())
        conn.execute('BEGIN IMMEDIATE')
        columns = conn.execute('PRAGMA table_info(auditoria_control_pid)').fetchall()
        if any(row[1] == 'sp_anterior' and row[3] for row in columns):
            # Preserve all historic audit rows while allowing an unknown previous state.
            conn.execute('ALTER TABLE auditoria_control_pid RENAME TO auditoria_control_pid_legacy')
            conn.execute("""CREATE TABLE auditoria_control_pid (
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_origen VARCHAR(32), variable_control VARCHAR(32) NOT NULL,
                sp_anterior REAL, sp_nuevo REAL NOT NULL, kp REAL, ki REAL, kd REAL,
                justificacion TEXT)""")
            conn.execute('INSERT INTO auditoria_control_pid SELECT * FROM auditoria_control_pid_legacy')
            conn.execute('DROP TABLE auditoria_control_pid_legacy')
        vision_columns = {row[1] for row in conn.execute('PRAGMA table_info(detecciones_vision)')}
        if 'simulado' not in vision_columns:
            conn.execute('ALTER TABLE detecciones_vision ADD COLUMN simulado BOOLEAN NOT NULL DEFAULT 1')
        if 'motor' not in vision_columns:
            conn.execute("ALTER TABLE detecciones_vision ADD COLUMN motor TEXT NOT NULL DEFAULT 'desconocido'")
        conn.commit()
        conn.execute('PRAGMA journal_mode=WAL')
