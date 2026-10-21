# ==============================================================================
# Makefile para el Proyecto de Tesis:
# Sistema Integrado IoT–PID–IA para Invernadero de Papa (La Paz, Bolivia)
# ==============================================================================

SHELL := /bin/bash
PYTHON := .venv/bin/python3
PYTEST := .venv/bin/pytest
CLOUDFLARED := $(shell which cloudflared 2>/dev/null || echo ".venv/bin/cloudflared")
PORT := 8000

.PHONY: all help init-db test check server tunnel run simulator docker-up clean

# Objetivo por defecto: muestra ayuda
help:
	@echo "========================================================================"
	@echo "Tesis IoT–PID–IA Invernadero de Papa (La Paz - 3600 msnm)"
	@echo "========================================================================"
	@echo "Comandos disponibles:"
	@echo "  make run        : Ejecuta TODO en orden (BD -> Test -> Django + Cloudflared)"
	@echo "  make init-db    : Inicializa tablas SQLite y puebla ensayos E1 a E8"
	@echo "  make test       : Ejecuta la suite completa de 23 pruebas Pytest"
	@echo "  make check      : Verifica el estado del sistema Django"
	@echo "  make server     : Inicia únicamente el servidor web Django en el puerto $(PORT)"
	@echo "  make tunnel     : Inicia únicamente el túnel seguro de Cloudflare"
	@echo "  make simulator  : Inicia el simulador de telemetría MQTT del ESP32"
	@echo "  make docker-up  : Levanta los servicios de infraestructura Docker"
	@echo "  make clean      : Limpia archivos temporales y caché de Python"
	@echo "========================================================================"

init-db:
	@echo "==> [1/4] Inicializando esquema y datos en SQLite..."
	@$(PYTHON) scripts/init_db.py
	@$(PYTHON) scripts/seed_experiments.py

test:
	@echo "==> [2/4] Ejecutando suite de 23 pruebas unitarias y de integración..."
	@$(PYTEST) tests/ -v

check:
	@echo "==> [3/4] Comprobando integridad del proyecto Django..."
	@$(PYTHON) web/manage.py check

server:
	@echo "==> Iniciando servidor Django en http://localhost:$(PORT)..."
	@$(PYTHON) web/manage.py runserver 0.0.0.0:$(PORT)

tunnel:
	@echo "==> Iniciando Cloudflare Tunnel hacia http://localhost:$(PORT)..."
	@$(CLOUDFLARED) tunnel --url http://localhost:$(PORT)

run: init-db test check
	@echo "==> [4/4] Levantando servidor web Django y enlazando Cloudflare Tunnel..."
	@bash -c '\
		trap "echo -e \"\n[!] Deteniendo servidor y túnel...\"; kill 0" EXIT SIGINT SIGTERM; \
		$(PYTHON) web/manage.py runserver 0.0.0.0:$(PORT) & \
		DJANGO_PID=$$!; \
		echo "Esperando que Django responda en http://localhost:$(PORT)..."; \
		while ! curl -s http://localhost:$(PORT)/ > /dev/null; do sleep 0.5; done; \
		echo "========================================================================"; \
		echo " Servidor Django ACTIVO en http://localhost:$(PORT)"; \
		echo " Lanzando túnel público de Cloudflare..."; \
		echo "========================================================================"; \
		$(CLOUDFLARED) tunnel --url http://localhost:$(PORT); \
	'

simulator:
	@echo "==> Iniciando simulador de ESP32 publicando telemetría MQTT..."
	@$(PYTHON) scripts/simulador_esp32_mqtt.py

docker-up:
	@echo "==> Levantando contenedores de infraestructura Docker..."
	@docker compose up -d mosquitto influxdb telegraf grafana

clean:
	@echo "==> Limpiando archivos temporales y cachés de Python..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@rm -rf .pytest_cache
