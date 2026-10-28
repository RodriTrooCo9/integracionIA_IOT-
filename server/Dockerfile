# ==============================================================================
# Dockerfile: Servidor FastAPI de Inferencia y Control IoT (Tesis Papa La Paz)
# ==============================================================================

FROM python:3.11-slim

# Evitar prompts interactivos y buffers de Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/workspace

# Instalar dependencias del sistema necesarias para OpenCV y diagnóstico de red
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copiar e instalar dependencias Python
COPY server/requirements.txt /workspace/requirements.txt
COPY server/requirements-vision.txt /workspace/requirements-vision.txt
ARG INSTALL_VISION=false
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    if [ "$INSTALL_VISION" = "true" ]; then pip install --no-cache-dir -r requirements-vision.txt; fi

# Copiar código del servidor y scripts
COPY server /workspace/server
COPY scripts/init_db.py /workspace/scripts/init_db.py

# Crear directorios para subida y procesamiento de imágenes
RUN mkdir -p /workspace/data/raw/uploads /workspace/data/processed /workspace/data/models

# Exponer puerto de la API FastAPI
EXPOSE 8000

# Comando por defecto: arrancar servidor FastAPI con Uvicorn
CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
