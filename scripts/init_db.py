#!/usr/bin/env python3
"""
init_db.py
Script de inicialización de la base de datos relacional SQLite
Proyecto de Tesis: IoT-PID-IA Papa Invernadero
"""

import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "invernadero_relacional.db"
SCHEMA_PATH = BASE_DIR / "server" / "app" / "models" / "schemas.sql"

def inicializar_base_datos():
    print(f"[*] Creando directorio de datos si no existe: {DB_DIR}")
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"[*] Conectando a SQLite en: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"[*] Leyendo esquema desde: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        
    print("[*] Ejecutando sentencias DDL...")
    cursor.executescript(schema_sql)
    
    # Insertar nodo sensor inicial de prueba
    cursor.execute("""
    INSERT OR IGNORE INTO nodos_sensores (nodo_id, nombre, descripcion, ip_asignada, mac_address, firmware_version, estado)
    VALUES ('esp32_invernadero_01', 'ESP32 Control Principal', 'Nodo de microclima y control PID split-range', '192.168.1.150', '24:6F:28:AB:CD:EF', 'v1.0.0', 'ACTIVO');
    """)
    
    conn.commit()
    conn.close()
    print("[✔] Base de datos relacional SQLite inicializada exitosamente.")

if __name__ == "__main__":
    inicializar_base_datos()
