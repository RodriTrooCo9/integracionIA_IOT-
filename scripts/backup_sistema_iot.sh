#!/usr/bin/env bash
# ==============================================================================
# Script de Respaldo Automatizado del Sistema IoT Invernadero Papa
# Proyecto de Tesis - La Paz, Bolivia
# Respalda: Base SQLite, Configuraciones Docker, Dashboards y Datos InfluxDB
# ==============================================================================

set -euo pipefail

BASE_DIR="/home/rodrigo/Desktop/IOTtesis"
BACKUP_DIR="${BASE_DIR}/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="backup_invernadero_${TIMESTAMP}"
DEST_TAR="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
TEMP_DIR=$(mktemp -d /tmp/backup_iot_XXXXXX)

echo "======================================================================"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando respaldo automatizado IoT..."
echo "======================================================================"

mkdir -p "${BACKUP_DIR}"
mkdir -p "${TEMP_DIR}/data"
mkdir -p "${TEMP_DIR}/config"

# 1. Respaldo consistente de Base de Datos SQLite (WAL Flush)
if [ -f "${BASE_DIR}/data/invernadero_relacional.db" ]; then
    echo "• Respaldando base de datos relacional SQLite (API nativa WAL)..."
    python3 -c "import sqlite3; s = sqlite3.connect('${BASE_DIR}/data/invernadero_relacional.db'); d = sqlite3.connect('${TEMP_DIR}/data/invernadero_relacional.db'); s.backup(d); d.close(); s.close()"
fi

# 2. Respaldo de Archivos de Configuración y Credenciales
echo "• Respaldando configuraciones (Mosquitto, Telegraf, Grafana, Docker)..."
cp -r "${BASE_DIR}/config" "${TEMP_DIR}/"
cp "${BASE_DIR}/docker-compose.yml" "${TEMP_DIR}/"
if [ -f "${BASE_DIR}/.env" ]; then
    cp "${BASE_DIR}/.env" "${TEMP_DIR}/"
fi

# 3. Exportar metadatos del estado del sistema
cat <<EOF > "${TEMP_DIR}/metadata.json"
{
  "timestamp": "${TIMESTAMP}",
  "proyecto": "Tesis IoT-PID-IA Invernadero Papa La Paz",
  "archivos_incluidos": [
    "data/invernadero_relacional.db",
    "config/mosquitto",
    "config/telegraf",
    "config/grafana",
    "docker-compose.yml"
  ]
}
EOF

# 4. Comprimir archivo tar.gz
echo "• Comprimiendo archivo de respaldo..."
tar -czf "${DEST_TAR}" -C "${TEMP_DIR}" .
rm -rf "${TEMP_DIR}"

BACKUP_SIZE=$(du -h "${DEST_TAR}" | cut -f1)
echo "✔ Respaldo completado con éxito: ${DEST_TAR} (${BACKUP_SIZE})"

# 5. Política de Retención: Eliminar respaldos con más de 7 días
echo "• Aplicando política de retención (conservar últimos 7 días)..."
find "${BACKUP_DIR}" -type f -name "backup_invernadero_*.tar.gz" -mtime +7 -delete

echo "======================================================================"
echo "Instalación en Crontab recomendada (ejecución diaria a las 02:00 AM):"
echo "0 2 * * * /bin/bash ${BASE_DIR}/scripts/backup_sistema_iot.sh >> ${BASE_DIR}/backups/backup.log 2>&1"
echo "======================================================================"
