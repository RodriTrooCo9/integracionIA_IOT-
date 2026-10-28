#!/usr/bin/env python3
"""Initialize the configured SQLite database without replacing existing data."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from server.app.services.bootstrap import inicializar_db

if __name__ == '__main__':
    inicializar_db()
    print('Esquema SQLite inicializado')
