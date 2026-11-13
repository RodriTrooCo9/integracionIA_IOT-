#!/usr/bin/env python3
"""
Generador de diagramas técnicos y mapa de delimitación espacial (300 dpi)
para la memoria de tesis en Ingeniería de Sistemas (USB, La Paz, Bolivia).

Regla de integridad: todos los componentes, pines, tópicos MQTT, servicios Docker,
modelos de visión, algoritmos y coordenadas reflejan exclusivamente el código real
del repositorio /home/rodrigo/Desktop/IOTtesis y la ubicación declarada
16°31'20.1"S 68°07'25.6"W (-16.52225, -68.12378).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon as MplPolygon
from matplotlib.lines import Line2D
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
FIG_DIR = BASE_DIR / "tesis" / "figuras"
GEO_BUNDLE = Path(__file__).resolve().parent / "geo_lapaz_bolivia.json"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Liberation Sans", "Arial"],
    "axes.edgecolor": "#334155",
    "axes.linewidth": 0.9,
})


# ==============================================================================
# UTILIDADES GRÁFICAS
# ==============================================================================

def draw_box(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str = "",
    body: str = "",
    fc: str = "#F8FAFC",
    ec: str = "#334155",
    lw: float = 1.4,
    header_fc: str | None = None,
    header_h: float = 0.0,
    title_color: str = "#0F172A",
    body_color: str = "#1E293B",
    title_size: float = 9.0,
    body_size: float = 7.4,
    rounding: float = 0.16,
    zorder: int = 3,
    linestyle: str = "-",
    alpha: float = 1.0,
):
    """Dibuja un bloque rectangular redondeado con cabecera opcional y texto centrado."""
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.02,rounding_size={rounding}",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        linestyle=linestyle,
        alpha=alpha,
        zorder=zorder,
    )
    ax.add_patch(box)

    if header_fc and header_h > 0:
        hdr = FancyBboxPatch(
            (x, y + h - header_h),
            w,
            header_h,
            boxstyle=f"round,pad=0.02,rounding_size={min(rounding, header_h * 0.45)}",
            facecolor=header_fc,
            edgecolor=ec,
            linewidth=lw,
            zorder=zorder + 0.5,
        )
        ax.add_patch(hdr)
        ax.text(
            x + w / 2,
            y + h - header_h / 2,
            title,
            ha="center",
            va="center",
            fontsize=title_size,
            fontweight="bold",
            color=title_color,
            zorder=zorder + 1,
        )
        if body:
            ax.text(
                x + w / 2,
                y + (h - header_h) / 2,
                body,
                ha="center",
                va="center",
                fontsize=body_size,
                color=body_color,
                linespacing=1.26,
                zorder=zorder + 1,
            )
    else:
        if title and body:
            ax.text(
                x + w / 2,
                y + h * 0.72,
                title,
                ha="center",
                va="center",
                fontsize=title_size,
                fontweight="bold",
                color=title_color,
                zorder=zorder + 1,
            )
            ax.text(
                x + w / 2,
                y + h * 0.34,
                body,
                ha="center",
                va="center",
                fontsize=body_size,
                color=body_color,
                linespacing=1.24,
                zorder=zorder + 1,
            )
        elif title:
            ax.text(
                x + w / 2,
                y + h / 2,
                title,
                ha="center",
                va="center",
                fontsize=title_size,
                fontweight="bold",
                color=title_color,
                linespacing=1.24,
                zorder=zorder + 1,
            )
        elif body:
            ax.text(
                x + w / 2,
                y + h / 2,
                body,
                ha="center",
                va="center",
                fontsize=body_size,
                color=body_color,
                linespacing=1.24,
                zorder=zorder + 1,
            )


def draw_arrow(
    ax,
    p1: tuple[float, float],
    p2: tuple[float, float],
    color: str = "#334155",
    lw: float = 1.5,
    style: str = "-|>",
    ls: str = "-",
    rad: float = 0.0,
    mutation: float = 13,
    zorder: int = 4,
    label: str = "",
    label_pos: tuple[float, float] | None = None,
    label_bg: str = "white",
    label_size: float = 7.3,
    label_color: str = "#0F172A",
):
    """Dibuja una flecha estilizada con etiqueta opcional legible."""
    conn = f"arc3,rad={rad}" if rad != 0 else "arc3,rad=0.0"
    arr = FancyArrowPatch(
        p1,
        p2,
        arrowstyle=style,
        mutation_scale=mutation,
        color=color,
        linewidth=lw,
        linestyle=ls,
        connectionstyle=conn,
        zorder=zorder,
    )
    ax.add_patch(arr)
    if label:
        lx, ly = label_pos if label_pos else ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        ax.text(
            lx,
            ly,
            label,
            ha="center",
            va="center",
            fontsize=label_size,
            color=label_color,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.22", facecolor=label_bg, edgecolor=color, linewidth=0.7, alpha=0.96),
            zorder=zorder + 1,
        )


def draw_ortho_arrow(
    ax,
    points: list[tuple[float, float]],
    color: str = "#334155",
    lw: float = 1.5,
    ls: str = "-",
    mutation: float = 13,
    zorder: int = 4,
    label: str = "",
    label_pos: tuple[float, float] | None = None,
    label_bg: str = "white",
    label_size: float = 7.2,
    label_color: str = "#0F172A",
):
    """Dibuja una polilínea ortogonal terminada en punta de flecha sin cruzar cajas."""
    if len(points) >= 3:
        xs = [p[0] for p in points[:-1]]
        ys = [p[1] for p in points[:-1]]
        ax.plot(xs, ys, color=color, linewidth=lw, linestyle=ls, solid_capstyle="round", zorder=zorder)
    arr = FancyArrowPatch(
        points[-2],
        points[-1],
        arrowstyle="-|>",
        mutation_scale=mutation,
        color=color,
        linewidth=lw,
        linestyle=ls,
        zorder=zorder,
    )
    ax.add_patch(arr)
    if label and label_pos:
        ax.text(
            label_pos[0],
            label_pos[1],
            label,
            ha="center",
            va="center",
            fontsize=label_size,
            color=label_color,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.20", facecolor=label_bg, edgecolor=color, linewidth=0.7, alpha=0.97),
            zorder=zorder + 2,
        )


def _plot_geojson_geom(ax, geom: dict, **kwargs):
    """Dibuja un Polygon o MultiPolygon GeoJSON en un eje matplotlib."""
    gtype = geom.get("type")
    coords = geom.get("coordinates", [])
    if gtype == "Polygon":
        if coords:
            poly = MplPolygon(coords[0], closed=True, **kwargs)
            ax.add_patch(poly)
    elif gtype == "MultiPolygon":
        for part in coords:
            if part:
                poly = MplPolygon(part[0], closed=True, **kwargs)
                ax.add_patch(poly)
    elif gtype == "GeometryCollection":
        for sub in geom.get("geometries", []):
            _plot_geojson_geom(ax, sub, **kwargs)


# ==============================================================================
# FIGURA 1: MODELO EN V ADAPTADO A SISTEMAS CIBERFÍSICOS (VDI/VDE 2206)
# ==============================================================================

def generar_modelo_v():
    fig, ax = plt.subplots(figsize=(16.0, 9.8), dpi=300)
    ax.set_xlim(0, 16.0)
    ax.set_ylim(0, 9.8)
    ax.axis("off")

    # Fondos por etapa
    ax.add_patch(FancyBboxPatch((0.22, 1.00), 5.80, 7.80, boxstyle="round,pad=0.05,rounding_size=0.20",
                                facecolor="#EFF6FF", edgecolor="#BFDBFE", linewidth=1.1, zorder=0))
    ax.add_patch(FancyBboxPatch((6.18, 0.95), 3.64, 2.38, boxstyle="round,pad=0.05,rounding_size=0.20",
                                facecolor="#FEFCE8", edgecolor="#FDE047", linewidth=1.1, zorder=0))
    ax.add_patch(FancyBboxPatch((9.98, 1.00), 5.80, 7.80, boxstyle="round,pad=0.05,rounding_size=0.20",
                                facecolor="#ECFDF5", edgecolor="#A7F3D0", linewidth=1.1, zorder=0))

    # Título y subtítulo
    ax.text(8.0, 9.45, "Modelo de Desarrollo en V para Sistemas Ciberfísicos (VDI/VDE 2206)",
            ha="center", va="center", fontsize=14.2, fontweight="bold", color="#0F172A")
    ax.text(8.0, 9.10, "Ciclo de diseño, implementación y validación del prototipo IoT–PID–IA para papa bajo invernadero (La Paz, Bolivia)",
            ha="center", va="center", fontsize=9.8, color="#475569")

    ax.text(3.12, 8.58, "BRAZO DESCENDENTE: DESCOMPOSICIÓN Y DISEÑO",
            ha="center", va="center", fontsize=9.4, fontweight="bold", color="#1D4ED8")
    ax.text(12.88, 8.58, "BRAZO ASCENDENTE: INTEGRACIÓN Y VALIDACIÓN",
            ha="center", va="center", fontsize=9.4, fontweight="bold", color="#047857")

    # --- BRAZO IZQUIERDO ---
    draw_box(
        ax, 0.40, 6.60, 5.20, 1.70,
        title="1. Especificación Bio-Agronómica y Requisitos",
        body=(
            "• Cultivo: Solanum tuberosum (La Paz, ~3.600 m s. n. m., 67,5 kPa)\n"
            "• Ventana psicrométrica: T óptima, HR y VPD (0,8 – 1,2 kPa)\n"
            "• Riesgo sanitario: Phytophthora infestans y Alternaria solani\n"
            "• Requisitos: lazo local autónomo 10 Hz + supervisión externa IA"
        ),
        fc="#FFFFFF", ec="#1D4ED8", lw=1.6,
        header_fc="#1D4ED8", header_h=0.38, title_color="#FFFFFF",
        title_size=9.0, body_size=7.4, rounding=0.14
    )

    draw_box(
        ax, 0.90, 4.48, 4.88, 1.74,
        title="2. Arquitectura Sistémica IoT–PID–IA",
        body=(
            "• Cascada: lazo interno ESP32 (10 Hz) + lazo externo (30 s)\n"
            "• Bus MQTT autenticado (Mosquitto) -> Telegraf -> InfluxDB v2\n"
            "• Fusión multimodal: 0,45·Clima + 0,35·Visión + 0,20·Tend.\n"
            "• Alertas críticas (Bot Telegram) y plataforma web (Django)"
        ),
        fc="#FFFFFF", ec="#2563EB", lw=1.6,
        header_fc="#2563EB", header_h=0.38, title_color="#FFFFFF",
        title_size=9.0, body_size=7.4, rounding=0.14
    )

    draw_box(
        ax, 1.45, 2.28, 4.42, 1.84,
        title="3. Diseño Detallado de Subsistemas",
        body=(
            "• Hardware ESP32: SHT31, DS18B20, BH1750, Cap. v1.2,\n"
            "  Flotador; SSR 220V, MOSFET 25 kHz, Relés humid./bomba\n"
            "• Firmware C++/PlatformIO (Hampel+EMA, Tetens, PID)\n"
            "• Docker (6 servicios) + SQLite WAL + Datasets reales:\n"
            "  PlantVillage (2.152 imgs) y PlantDoc (219 imgs)"
        ),
        fc="#FFFFFF", ec="#3B82F6", lw=1.6,
        header_fc="#3B82F6", header_h=0.38, title_color="#FFFFFF",
        title_size=8.9, body_size=7.2, rounding=0.14
    )

    # --- VÉRTICE INFERIOR ---
    draw_box(
        ax, 6.32, 1.08, 3.36, 2.08,
        title="4. Implementación Integrada",
        body=(
            "• Firmware compilado (PlatformIO .bin)\n"
            "  y esquema virtual (Wokwi / ESPHome)\n"
            "• Stack Docker: Mosquitto 2.0.18, Telegraf,\n"
            "  InfluxDB 2.7.5, Grafana 10.4.1, FastAPI, Worker\n"
            "• Entrenamiento GPU Colab: YOLO26n / YOLO11n\n"
            "• Prototipo físico: [Pendiente de campo]"
        ),
        fc="#FFFFFF", ec="#B45309", lw=1.9,
        header_fc="#D97706", header_h=0.38, title_color="#FFFFFF",
        title_size=9.0, body_size=7.2, rounding=0.15
    )

    # --- BRAZO DERECHO ---
    draw_box(
        ax, 10.13, 2.28, 4.42, 1.84,
        title="5. Pruebas Unitarias e Integración SW",
        body=(
            "• Compilación PlatformIO ESP32 y linting flake8\n"
            "• Suite Pytest: 117 pruebas aprobadas (API FastAPI,\n"
            "  Django ORM/vistas, MQTT, Telegram, YOLO26)\n"
            "• Verificación SHA-256 de datasets y pesos best.pt\n"
            "• Verificación banco eléctrico físico: [Pendiente]"
        ),
        fc="#FFFFFF", ec="#059669", lw=1.6,
        header_fc="#059669", header_h=0.38, title_color="#FFFFFF",
        title_size=8.9, body_size=7.2, rounding=0.14
    )

    draw_box(
        ax, 10.22, 4.48, 4.88, 1.74,
        title="6. Validación de Lazo FOPDT/PID y MQTT",
        body=(
            "• FOPDT sim. (K=0,1639; τ=242,96 s; θ=33,33 s)\n"
            "• PID Optuna vs ZN/CC/IMC/On-Off (-29,9% IAE)\n"
            "• Bus MQTT QoS 1, InfluxDB v2 y SQLite WAL\n"
            "• Riesgo sintético 90 d: XGBoost AUC=0,7123 / Brier=0,1878\n"
            "• Respuesta al escalón en invernadero físico: [Pendiente]"
        ),
        fc="#FFFFFF", ec="#047857", lw=1.6,
        header_fc="#047857", header_h=0.38, title_color="#FFFFFF",
        title_size=9.0, body_size=7.3, rounding=0.14
    )

    draw_box(
        ax, 10.40, 6.60, 5.20, 1.70,
        title="7. Validación Piloto IA y Ensayos E1–E8",
        body=(
            "• Piloto real Colab: YOLO26n-cls (Top-1 100%, 323 test imgs)\n"
            "  y YOLO26n PlantDoc (test mAP@0.50 = 49,26%, 33 imgs)\n"
            "• Protocolo experimental E1–E8 (Nivel 0 manual vs Nivel 1)\n"
            "• Captura en invernadero La Paz y SAHI en campo: [Pendiente]"
        ),
        fc="#FFFFFF", ec="#065F46", lw=1.6,
        header_fc="#065F46", header_h=0.38, title_color="#FFFFFF",
        title_size=9.0, body_size=7.4, rounding=0.14
    )

    # Flechas de flujo V
    draw_arrow(ax, (3.00, 6.58), (3.18, 6.25), color="#1D4ED8", lw=2.2, mutation=15)
    draw_arrow(ax, (3.42, 4.46), (3.58, 4.15), color="#2563EB", lw=2.2, mutation=15)
    draw_arrow(ax, (3.85, 2.26), (6.30, 1.98), color="#B45309", lw=2.2, rad=0.12, mutation=15)

    draw_arrow(ax, (9.70, 1.98), (12.15, 2.26), color="#059669", lw=2.2, rad=0.12, mutation=15)
    draw_arrow(ax, (12.42, 4.15), (12.58, 4.46), color="#047857", lw=2.2, mutation=15)
    draw_arrow(ax, (12.82, 6.25), (13.00, 6.58), color="#065F46", lw=2.2, mutation=15)

    # Flechas horizontales de correspondencia VDI/VDE 2206
    draw_arrow(
        ax, (5.63, 7.45), (10.37, 7.45),
        color="#475569", lw=1.4, ls="--", style="<|-|>", mutation=12,
        label="Validación Operacional y Agronómica (E1–E8)",
        label_pos=(8.00, 7.73), label_bg="#F8FAFC", label_size=7.6
    )
    draw_arrow(
        ax, (5.81, 5.35), (10.19, 5.35),
        color="#475569", lw=1.4, ls="--", style="<|-|>", mutation=12,
        label="Verificación de Integración, Lazo PID y Mensajería",
        label_pos=(8.00, 5.63), label_bg="#F8FAFC", label_size=7.6
    )
    draw_arrow(
        ax, (5.90, 3.45), (10.10, 3.45),
        color="#475569", lw=1.4, ls="--", style="<|-|>", mutation=12,
        label="Verificación Unitaria de Componentes (117 tests)",
        label_pos=(8.00, 3.74), label_bg="#F8FAFC", label_size=7.5
    )

    ax.text(
        8.0, 0.45,
        "Estado probatorio: Software, firmware compilado, arquitectura Docker (6 servicios), 117 pruebas Pytest y entrenamiento piloto en Colab verificados en repositorio; "
        "ensamblaje físico, escalón térmico real y ensayos E1–E8 en invernadero marcados como [Pendiente de campo].",
        ha="center", va="center", fontsize=7.9, color="#334155",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#F1F5F9", edgecolor="#CBD5E1", linewidth=1.0)
    )

    out_path = FIG_DIR / "fig_flujo_modelo_v.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight", pad_inches=0.15, facecolor="white")
    plt.close(fig)
    return out_path


# ==============================================================================
# FIGURA 2: ARQUITECTURA REAL DEL SISTEMA IoT–PID–IA
# ==============================================================================

def generar_arquitectura_real():
    fig, ax = plt.subplots(figsize=(16.8, 10.6), dpi=300)
    ax.set_xlim(0, 16.8)
    ax.set_ylim(0, 10.6)
    ax.axis("off")

    ax.text(8.40, 10.22, "Arquitectura Real del Sistema Integrado IoT–PID–IA para Invernadero de Papa",
            ha="center", va="center", fontsize=14.2, fontweight="bold", color="#0F172A")
    ax.text(8.40, 9.85, "Implementación verificada en firmware (ESP32 DevKit V1), bus MQTT, contenedores Docker (net_invernadero_iot), visión IA y plataforma web",
            ha="center", va="center", fontsize=9.6, color="#475569")

    # Contenedores de capas (dejando corredor inferior y=0.25..0.72 para ruta óptica limpia)
    ax.add_patch(FancyBboxPatch((0.25, 0.85), 5.00, 8.65, boxstyle="round,pad=0.05,rounding_size=0.22",
                                facecolor="#F0FDF4", edgecolor="#15803D", linewidth=1.6, zorder=0))
    ax.text(2.75, 9.24, "CAPA FÍSICA Y BORDE (INVERNADERO)",
            ha="center", va="center", fontsize=9.7, fontweight="bold", color="#14532D")

    ax.add_patch(FancyBboxPatch((5.85, 0.85), 4.55, 8.65, boxstyle="round,pad=0.05,rounding_size=0.22",
                                facecolor="#EFF6FF", edgecolor="#1D4ED8", linewidth=1.6, zorder=0))
    ax.text(8.12, 9.24, "BUS IoT Y SERIES TEMPORALES (DOCKER)",
            ha="center", va="center", fontsize=9.7, fontweight="bold", color="#1E3A8A")

    ax.add_patch(FancyBboxPatch((10.95, 0.85), 5.55, 8.65, boxstyle="round,pad=0.05,rounding_size=0.22",
                                facecolor="#FAF5FF", edgecolor="#6D28D9", linewidth=1.6, zorder=0))
    ax.text(13.72, 9.24, "CAPA IA, SUPERVISIÓN Y APLICACIÓN WEB",
            ha="center", va="center", fontsize=9.7, fontweight="bold", color="#4C1D95")

    # ================= CAPA 1: FÍSICA Y BORDE =================
    draw_box(
        ax, 0.45, 6.80, 4.60, 2.10,
        title="Instrumentación Ambiental, Edáfica y Nivel",
        body=(
            "• SHT31 (I2C 0x44, SDA GPIO21 / SCL GPIO22): T y HR aire\n"
            "• BH1750 (I2C, GPIO21 / GPIO22): Iluminancia [lux]\n"
            "• DS18B20 (OneWire GPIO4, pull-up 4,7 kΩ): T suelo [°C]\n"
            "• Sensor Capacitivo v1.2 (ADC1_CH6 GPIO34): Humedad suelo\n"
            "• Interruptor Flotador (GPI35, pull-up ext.): Nivel reservorio"
        ),
        fc="#FFFFFF", ec="#16A34A", lw=1.4,
        header_fc="#16A34A", header_h=0.38, title_color="#FFFFFF",
        title_size=8.6, body_size=7.3, rounding=0.14
    )

    draw_box(
        ax, 0.45, 4.35, 4.60, 2.10,
        title="ESP32 DevKit V1 — Lazo Interno Autónomo (10 Hz)",
        body=(
            "• Filtrado digital: Hampel (ventana 3) + EMA (α=0,10–0,15)\n"
            "• Psicrometría en borde: Tetens/Magnus (VPD y Punto de Rocío)\n"
            "• Control PID discreto (dt=0,1 s) Split-Range [-100%, +100%]:\n"
            "  Banda muerta ±0,25 °C, derivada en PV, anti-windup clamping\n"
            "• Resiliencia: Watchdog WDT 10 s y operación autónoma offline"
        ),
        fc="#FFFFFF", ec="#15803D", lw=1.6,
        header_fc="#15803D", header_h=0.38, title_color="#FFFFFF",
        title_size=8.6, body_size=7.3, rounding=0.14
    )

    draw_box(
        ax, 0.45, 2.12, 4.60, 1.88,
        title="Actuadores y Etapa de Potencia",
        body=(
            "• Calefactor 220 V AC: SSR optoaislado 4000 V (GPIO23, 2000 ms)\n"
            "• Extractor 12 V DC: MOSFET IRLZ44N (GPIO19, PWM 25 kHz, 8 bits)\n"
            "• Humidificador: Módulo Relé Active-LOW (GPIO18)\n"
            "• Bomba de riego 12 V: Relé Active-LOW + 1N4007 (GPIO26)"
        ),
        fc="#FFFFFF", ec="#166534", lw=1.4,
        header_fc="#166534", header_h=0.36, title_color="#FFFFFF",
        title_size=8.6, body_size=7.25, rounding=0.14
    )

    draw_box(
        ax, 0.45, 1.02, 4.60, 0.82,
        title="Óptica / Captura de Follaje y Trampas",
        body="Cámara USB 1080p (principal) / ESP32-CAM OV2640 (auxiliar)",
        fc="#ECFDF5", ec="#0D9488", lw=1.4,
        title_size=8.5, body_size=7.4, rounding=0.12
    )

    draw_arrow(ax, (2.75, 6.78), (2.75, 6.48), color="#15803D", lw=1.7)
    draw_arrow(ax, (2.75, 4.33), (2.75, 4.03), color="#166534", lw=1.7)

    # ================= CAPA 2: BUS Y SERIES TEMPORALES =================
    draw_box(
        ax, 6.05, 6.55, 4.15, 2.35,
        title="Eclipse Mosquitto 2.0.18 (Broker MQTT)",
        body=(
            "Puertos 1883 / 9001 | Autenticación PBKDF2-SHA512\n"
            "• Pub ESP32 (1 Hz): invernadero/telemetria/microclima\n"
            "  invernadero/telemetria/pid | invernadero/alerta\n"
            "• Pub IA/Worker: invernadero/vision/detecciones\n"
            "  invernadero/riesgo/indice | .../alarmas/eventos\n"
            "• Cmd Cascada -> ESP32: .../control/setpoint(s)"
        ),
        fc="#FFFFFF", ec="#1D4ED8", lw=1.6,
        header_fc="#1D4ED8", header_h=0.38, title_color="#FFFFFF",
        title_size=8.6, body_size=7.2, rounding=0.14
    )

    draw_box(
        ax, 6.05, 4.78, 4.15, 1.38,
        title="Telegraf 1.30.0 (Agente Colector)",
        body=(
            "Suscriptor MQTT autenticado (telegraf_worker)\n"
            "Parsing JSON de telemetría microclima, PID y riesgo\n"
            "Enrutamiento batch hacia InfluxDB v2"
        ),
        fc="#FFFFFF", ec="#2563EB", lw=1.4,
        header_fc="#2563EB", header_h=0.36, title_color="#FFFFFF",
        title_size=8.6, body_size=7.3, rounding=0.14
    )

    draw_box(
        ax, 6.05, 2.98, 4.15, 1.38,
        title="InfluxDB 2.7.5-alpine (Series Temporales)",
        body=(
            "Puerto 8086 | Org: agri_iot_tesis | Bucket: invernadero_data\n"
            "Almacenamiento histórico de alta resolución\n"
            "(T, HR, VPD, punto de rocío, T/H suelo, lux, CV PID)"
        ),
        fc="#FFFFFF", ec="#0284C7", lw=1.4,
        header_fc="#0284C7", header_h=0.36, title_color="#FFFFFF",
        title_size=8.6, body_size=7.3, rounding=0.14
    )

    draw_box(
        ax, 6.05, 1.05, 4.15, 1.48,
        title="Grafana 10.4.1 (Analítica Temporal)",
        body=(
            "Puerto 3001 -> 3000 | Provisioning declarativo\n"
            "Tableros de monitoreo térmico, VPD, acción\n"
            "de actuadores y evolución histórica de riesgo"
        ),
        fc="#FFFFFF", ec="#0369A1", lw=1.4,
        header_fc="#0369A1", header_h=0.36, title_color="#FFFFFF",
        title_size=8.6, body_size=7.3, rounding=0.14
    )

    draw_arrow(ax, (8.12, 6.53), (8.12, 6.19), color="#2563EB", lw=1.7)
    draw_arrow(ax, (8.12, 4.76), (8.12, 4.39), color="#0284C7", lw=1.7)
    draw_arrow(ax, (8.12, 2.96), (8.12, 2.56), color="#0369A1", lw=1.7)

    # ================= CAPA 3: IA, SUPERVISIÓN Y WEB =================
    draw_box(
        ax, 11.25, 6.80, 4.90, 2.10,
        title="FastAPI + Uvicorn (Puerto 8000, Python 3.11)",
        body=(
            "• API REST /api/v1/* (health, telemetría, detección, setpoints)\n"
            "• VisionInferenceService: YOLO26n / YOLO11n + SAHI 0.12.8\n"
            "  Soporte dual detect/classify con verificación SHA-256\n"
            "  (PlantDoc hoja completa: severidad_disponible=false)\n"
            "• Publica detecciones en MQTT y registra en SQLite WAL"
        ),
        fc="#FFFFFF", ec="#6D28D9", lw=1.6,
        header_fc="#6D28D9", header_h=0.38, title_color="#FFFFFF",
        title_size=8.6, body_size=7.2, rounding=0.14
    )

    draw_box(
        ax, 11.25, 4.55, 4.90, 1.85,
        title="Worker Supervisor (server.app.worker, ciclo 30 s)",
        body=(
            "• Ventana deslizante (48 muestras clima + última visión)\n"
            "• Fusión Multimodal: Score = 0,45·Clima + 0,35·Visión + 0,20·Tend.\n"
            "• Niveles: BAJO (<0,30) | MEDIO | ALTO | CRÍTICO (>=0,75)\n"
            "• Lazo Externo en Cascada: envía nuevos SP (T_sp, HR_sp) a ESP32"
        ),
        fc="#FFFFFF", ec="#7C3AED", lw=1.6,
        header_fc="#7C3AED", header_h=0.38, title_color="#FFFFFF",
        title_size=8.6, body_size=7.2, rounding=0.14
    )

    draw_box(
        ax, 11.25, 2.78, 2.35, 1.40,
        title="SQLite (Modo WAL)",
        body=(
            "invernadero_relacional.db\n"
            "5 tablas: nodos, visión,\n"
            "alarmas, PID, E1–E8"
        ),
        fc="#FFFFFF", ec="#4F46E5", lw=1.4,
        header_fc="#4F46E5", header_h=0.34, title_color="#FFFFFF",
        title_size=8.3, body_size=7.2, rounding=0.13
    )

    draw_box(
        ax, 13.80, 2.78, 2.35, 1.40,
        title="Bot de Telegram",
        body=(
            "Cliente httpx asíncrono\n"
            "Alertas ante nivel ALTO /\n"
            "CRÍTICO y fallos de red"
        ),
        fc="#FFFFFF", ec="#0EA5E9", lw=1.4,
        header_fc="#0EA5E9", header_h=0.34, title_color="#FFFFFF",
        title_size=8.3, body_size=7.2, rounding=0.13
    )

    draw_box(
        ax, 11.25, 1.05, 4.90, 1.40,
        title="Aplicación Web Django 6.1 (web/ — Tailwind + Chart.js)",
        body=(
            "• 5 vistas operativas + Gemelo Digital interactivo + Auditoría E1–E8\n"
            "• Consumo de SQLite WAL, exportación CSV y túneles HTTPS seguros"
        ),
        fc="#FFFFFF", ec="#4338CA", lw=1.5,
        header_fc="#4338CA", header_h=0.36, title_color="#FFFFFF",
        title_size=8.5, body_size=7.35, rounding=0.14
    )

    # ================= CONEXIONES LIMPIAS SIN CRUCES =================
    # ESP32 <-> Mosquitto en el pasillo entre Capa 1 y Capa 2 (x = 5.05 .. 6.05)
    draw_ortho_arrow(
        ax,
        [(5.07, 5.75), (5.55, 5.75), (5.55, 7.90), (6.03, 7.90)],
        color="#15803D", lw=1.8,
        label="WiFi/MQTT 1 Hz", label_pos=(5.55, 7.02), label_size=6.9
    )
    draw_ortho_arrow(
        ax,
        [(6.03, 7.20), (5.42, 7.20), (5.42, 5.05), (5.07, 5.05)],
        color="#7C3AED", lw=1.7, ls="--",
        label="Setpoints SP", label_pos=(5.55, 5.95), label_size=6.9
    )

    # Mosquitto <-> FastAPI y Worker en el pasillo entre Capa 2 y Capa 3 (x = 10.20 .. 11.25)
    draw_arrow(
        ax, (10.22, 7.85), (11.23, 7.85),
        color="#6D28D9", lw=1.6, style="<|-|>",
        label="MQTT", label_pos=(10.72, 8.12), label_size=7.0
    )
    draw_ortho_arrow(
        ax,
        [(10.22, 7.10), (10.68, 7.10), (10.68, 5.65), (11.23, 5.65)],
        color="#7C3AED", lw=1.7,
        label="Sub/Pub", label_pos=(10.72, 6.45), label_size=6.9
    )

    # FastAPI -> SQLite por canal izquierdo interno de Capa 3 (x = 11.08), sin tocar Worker
    draw_ortho_arrow(
        ax,
        [(11.23, 7.20), (11.07, 7.20), (11.07, 3.55), (11.23, 3.55)],
        color="#4F46E5", lw=1.4, ls=":"
    )

    # Worker -> SQLite y Worker -> Telegram
    draw_arrow(ax, (12.42, 4.53), (12.42, 4.21), color="#4F46E5", lw=1.6)
    draw_arrow(ax, (14.97, 4.53), (14.97, 4.21), color="#0EA5E9", lw=1.6)

    # SQLite <-> Django
    draw_arrow(ax, (12.42, 2.76), (12.42, 2.48), color="#4338CA", lw=1.6, style="<|-|>")

    # Cámara USB -> FastAPI por el CORREDOR EXTERIOR INFERIOR Y DERECHO (0 cruces sobre bloques)
    draw_ortho_arrow(
        ax,
        [(2.75, 1.00), (2.75, 0.42), (16.36, 0.42), (16.36, 7.85), (16.17, 7.85)],
        color="#0D9488", lw=1.7, ls="-.",
        label="Frames / Upload de imágenes (HTTP POST hacia FastAPI /api/v1/vision)",
        label_pos=(9.30, 0.42), label_bg="#ECFDF5", label_size=7.5
    )

    out_path = FIG_DIR / "fig_arq_sistema_real.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight", pad_inches=0.15, facecolor="white")
    plt.close(fig)
    return out_path


# ==============================================================================
# FIGURA 3: MAPA DE DELIMITACIÓN ESPACIAL (LA PAZ, BOLIVIA)
# ==============================================================================

def _add_north_arrow(ax, x_frac: float, y_frac: float, size: float = 0.07):
    """Dibuja una flecha Norte limpia usando coordenadas relativas del eje (0..1)."""
    ax.annotate(
        "N",
        xy=(x_frac, y_frac + size),
        xytext=(x_frac, y_frac),
        xycoords="axes fraction",
        textcoords="axes fraction",
        ha="center",
        va="center",
        fontsize=10.5,
        fontweight="bold",
        color="#0F172A",
        arrowprops=dict(arrowstyle="-|>", lw=2.1, color="#0F172A", mutation_scale=15),
        zorder=25,
    )


def _add_scale_bar(ax, lon_start: float, lat_pos: float, length_km: float, label: str, segments: int = 2):
    """Dibuja una barra de escala geodésica precisa a la latitud indicada."""
    km_per_deg_lon = 111.320 * math.cos(math.radians(lat_pos))
    dlon = length_km / km_per_deg_lon
    seg_len = dlon / segments
    bar_h = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.015

    pad_x = dlon * 0.12
    pad_y = bar_h * 1.4
    ax.add_patch(
        patches.Rectangle(
            (lon_start - pad_x, lat_pos - pad_y * 0.5),
            dlon + pad_x * 2.3,
            bar_h * 3.9,
            facecolor="white",
            edgecolor="#94A3B8",
            linewidth=0.8,
            alpha=0.95,
            zorder=22,
        )
    )
    for i in range(segments):
        fc = "#0F172A" if i % 2 == 0 else "#FFFFFF"
        ax.add_patch(
            patches.Rectangle(
                (lon_start + i * seg_len, lat_pos),
                seg_len,
                bar_h,
                facecolor=fc,
                edgecolor="#0F172A",
                linewidth=0.9,
                zorder=23,
            )
        )
    ax.text(lon_start, lat_pos + bar_h * 1.55, "0", ha="center", va="bottom", fontsize=7.5, color="#0F172A", zorder=24)
    ax.text(lon_start + dlon, lat_pos + bar_h * 1.55, label, ha="center", va="bottom",
            fontsize=7.5, fontweight="bold", color="#0F172A", zorder=24)


def generar_mapa_lapaz():
    geo = json.loads(GEO_BUNDLE.read_text(encoding="utf-8"))

    site_lat = -16.522250   # 16°31'20.1"S
    site_lon = -68.123778   # 68°07'25.6"W

    fig, (ax_nat, ax_loc) = plt.subplots(
        1, 2, figsize=(15.6, 7.8), dpi=300,
        gridspec_kw={"width_ratios": [1.0, 1.15], "wspace": 0.22}
    )

    fig.suptitle(
        "Delimitación Espacial del Área de Estudio: Zona Achachicala / Universidad Salesiana de Bolivia, La Paz",
        fontsize=13.5, fontweight="bold", color="#0F172A", y=0.97
    )

    # ---------------- PANEL (a): CONTEXTO NACIONAL Y DEPARTAMENTAL ----------------
    ax_nat.set_facecolor("#E0F2FE")
    for iso, geoms in geo["neighbors"].items():
        for g in geoms:
            _plot_geojson_geom(ax_nat, g, facecolor="#E2E8F0", edgecolor="#94A3B8", linewidth=0.7, zorder=1)

    for dept in geo["departments"]:
        is_lp = dept["name"] == "La Paz"
        fc = "#BFDBFE" if is_lp else "#F8FAFC"
        ec = "#1D4ED8" if is_lp else "#64748B"
        lw = 1.4 if is_lp else 0.8
        _plot_geojson_geom(ax_nat, dept["geom"], facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2 if not is_lp else 3)

    for lake in geo["lakes"]:
        _plot_geojson_geom(ax_nat, lake["geom"], facecolor="#60A5FA", edgecolor="#1D4ED8", linewidth=0.8, zorder=4)

    halo = [pe.withStroke(linewidth=2.5, foreground="white")]
    ax_nat.text(-70.2, -14.0, "PERÚ", fontsize=8.5, fontweight="bold", color="#64748B", ha="center", path_effects=halo)
    ax_nat.text(-69.8, -19.8, "CHILE", fontsize=8.5, fontweight="bold", color="#64748B", ha="center", path_effects=halo)
    ax_nat.text(-63.5, -22.5, "ARGENTINA", fontsize=8.5, fontweight="bold", color="#64748B", ha="center", path_effects=halo)
    ax_nat.text(-58.8, -14.0, "BRASIL", fontsize=8.5, fontweight="bold", color="#64748B", ha="center", path_effects=halo)
    ax_nat.text(-59.8, -21.2, "PARAGUAY", fontsize=8.0, fontweight="bold", color="#64748B", ha="center", path_effects=halo)
    ax_nat.text(-69.95, -15.30, "Lago\nTiticaca", fontsize=7.1, style="italic", color="#1E3A8A",
                ha="center", zorder=6, path_effects=halo)
    ax_nat.text(-67.95, -13.65, "Dpto.\nLa Paz", fontsize=8.3, fontweight="bold", color="#1E3A8A",
                ha="center", zorder=6, path_effects=halo)

    ref_offsets = {
        "Santa Cruz": (0.25, -0.25),
        "Cochabamba": (0.20, 0.22),
        "Sucre": (0.20, 0.18),
        "Oruro": (0.28, -0.10),
        "Potosí": (0.25, -0.20),
        "Tarija": (0.22, -0.15),
    }
    for c in geo["cities"]:
        if c["name"] in ref_offsets:
            dx, dy = ref_offsets[c["name"]]
            ax_nat.scatter(c["lon"], c["lat"], s=16, color="#334155", zorder=7)
            ax_nat.text(c["lon"] + dx, c["lat"] + dy, c["name"], fontsize=7.0, color="#334155", zorder=7, path_effects=halo)

    ax_nat.scatter(site_lon, site_lat, s=75, color="#DC2626", edgecolor="white", linewidth=1.2, zorder=9, marker="*")
    zoom_rect = patches.Rectangle((-68.55, -16.85), 0.85, 0.65, linewidth=1.4, edgecolor="#DC2626", facecolor="none", zorder=8)
    ax_nat.add_patch(zoom_rect)
    ax_nat.annotate(
        "Área de Estudio\n(La Paz)",
        xy=(site_lon, site_lat),
        xytext=(-65.4, -15.0),
        fontsize=8.2,
        fontweight="bold",
        color="#991B1B",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#FEF2F2", edgecolor="#DC2626", lw=0.9),
        arrowprops=dict(arrowstyle="->", color="#DC2626", lw=1.2),
        zorder=10,
    )

    ax_nat.set_xlim(-71.2, -57.0)
    ax_nat.set_ylim(-23.2, -9.2)
    ax_nat.set_aspect(1.0 / math.cos(math.radians(-16.5)))
    ax_nat.grid(True, linestyle=":", color="#94A3B8", alpha=0.6, zorder=0)
    ax_nat.set_xlabel("Longitud Oeste [°]", fontsize=9.2)
    ax_nat.set_ylabel("Latitud Sur [°]", fontsize=9.2)
    ax_nat.set_title("(a) Contexto Nacional y Departamento de La Paz", fontsize=10.8, fontweight="bold", pad=8)
    ax_nat.tick_params(labelsize=8.2)
    _add_north_arrow(ax_nat, 0.92, 0.84, size=0.08)
    _add_scale_bar(ax_nat, -70.6, -22.3, 300, "300 km", segments=3)

    # ---------------- PANEL (b): PLANO LOCAL CUENCA DE LA PAZ ----------------
    ax_loc.set_facecolor("#F8FAFC")

    muni_colors = {
        "Nuestra Señora de La Paz": "#ECFDF5",
        "El Alto": "#F1F5F9",
        "Achocalla": "#FEF9C3",
        "Mecapaca": "#FFF7ED",
        "Palca": "#F0F9FF",
    }
    for m in geo["municipalities_lapaz"]:
        name = m["name"]
        fc = muni_colors.get(name, "#F8FAFC")
        lw = 1.4 if name == "Nuestra Señora de La Paz" else 0.9
        ec = "#047857" if name == "Nuestra Señora de La Paz" else "#64748B"
        _plot_geojson_geom(ax_loc, m["geom"], facecolor=fc, edgecolor=ec, linewidth=lw, zorder=1)

    for u in geo["urban_lapaz"]:
        _plot_geojson_geom(ax_loc, u, facecolor="#CBD5E1", edgecolor="#64748B", linewidth=0.7, alpha=0.55, zorder=2)

    # Etiquetas de jurisdicciones en posiciones libres de flecha Norte y escala
    ax_loc.text(-68.202, -16.490, "Mun. El Alto\n(Altiplano ~4.050 m)", fontsize=7.5, color="#475569",
                ha="left", va="top", bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="#CBD5E1", alpha=0.9), zorder=6)
    ax_loc.text(-68.122, -16.458, "Mun. Nuestra Señora de La Paz", fontsize=8.0, fontweight="bold", color="#065F46",
                ha="center", va="top", bbox=dict(boxstyle="round,pad=0.24", fc="#ECFDF5", ec="#10B981", alpha=0.95), zorder=6)
    ax_loc.text(-68.198, -16.593, "Mun. Achocalla", fontsize=7.6, color="#713F12", ha="left", va="bottom",
                path_effects=halo, zorder=6)
    ax_loc.text(-68.042, -16.565, "Cuenca Sur / Palca", fontsize=7.5, color="#475569", ha="right", va="bottom",
                path_effects=halo, zorder=6)

    # Anillos de radio de referencia geodésica real (1 km y 2 km)
    lat_rad = math.radians(site_lat)
    km_per_deg_lat = 110.574
    km_per_deg_lon = 111.320 * math.cos(lat_rad)
    for r_km, ls, lbl_r in [(1.0, "--", "Radio 1 km"), (2.0, ":", "Radio 2 km")]:
        theta = np.linspace(0, 2 * np.pi, 180)
        cx = site_lon + (r_km / km_per_deg_lon) * np.cos(theta)
        cy = site_lat + (r_km / km_per_deg_lat) * np.sin(theta)
        ax_loc.plot(cx, cy, linestyle=ls, color="#0284C7", linewidth=1.0, alpha=0.85, zorder=5)
        ax_loc.text(site_lon + (r_km / km_per_deg_lon) * 0.72, site_lat + (r_km / km_per_deg_lat) * 0.72,
                    lbl_r, fontsize=7.0, color="#0369A1", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8), zorder=7)

    # Cruz geodésica exacta
    ax_loc.axvline(site_lon, color="#DC2626", linestyle=":", linewidth=0.9, alpha=0.7, zorder=4)
    ax_loc.axhline(site_lat, color="#DC2626", linestyle=":", linewidth=0.9, alpha=0.7, zorder=4)

    # Marcador principal del sitio
    ax_loc.scatter(site_lon, site_lat, s=220, color="#DC2626", edgecolor="white", linewidth=1.6, zorder=10, marker="*")
    ax_loc.scatter(site_lon, site_lat, s=340, facecolors="none", edgecolors="#991B1B", linewidth=1.3, zorder=9)

    ax_loc.annotate(
        "Sitio de Estudio (USB / Zona Achachicala)\n"
        "16°31'20.1\"S, 68°07'25.6\"W\n"
        "(-16,52225° Lat; -68,12378° Lon)\n"
        "Altitud ref.: ~3.600–3.650 m s. n. m.\n"
        "Presión barométrica ref.: ~67,5 kPa",
        xy=(site_lon, site_lat),
        xytext=(-68.198, -16.550),
        fontsize=7.8,
        fontweight="bold",
        color="#0F172A",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#FEF2F2", edgecolor="#DC2626", lw=1.2),
        arrowprops=dict(arrowstyle="-|>", color="#DC2626", lw=1.4, connectionstyle="arc3,rad=-0.15"),
        zorder=12,
    )

    ax_loc.set_xlim(-68.21, -68.035)
    ax_loc.set_ylim(-16.60, -16.45)
    ax_loc.set_aspect(1.0 / math.cos(lat_rad))
    ax_loc.grid(True, linestyle=":", color="#94A3B8", alpha=0.7, zorder=0)
    ax_loc.set_xlabel("Longitud Oeste [°] (WGS84)", fontsize=9.2)
    ax_loc.set_ylabel("Latitud Sur [°] (WGS84)", fontsize=9.2)
    ax_loc.set_title("(b) Delimitación Local — Cuenca de La Paz (WGS84)", fontsize=10.8, fontweight="bold", pad=8)
    ax_loc.tick_params(labelsize=8.0)

    _add_north_arrow(ax_loc, 0.93, 0.84, size=0.08)
    _add_scale_bar(ax_loc, -68.095, -16.592, 4.0, "4 km", segments=4)

    legend_handles = [
        patches.Patch(facecolor="#BFDBFE", edgecolor="#1D4ED8", label="Dpto. de La Paz"),
        patches.Patch(facecolor="#ECFDF5", edgecolor="#047857", label="Mun. Nuestra Señora de La Paz"),
        patches.Patch(facecolor="#CBD5E1", edgecolor="#64748B", alpha=0.65, label="Área urbana consolidada (Natural Earth)"),
        Line2D([0], [0], marker="*", color="w", markerfacecolor="#DC2626", markeredgecolor="#991B1B",
               markersize=12, label="Punto experimental (16°31'20.1\"S, 68°07'25.6\"W)"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        ncol=4,
        fontsize=8.3,
        frameon=True,
        facecolor="#FFFFFF",
        edgecolor="#CBD5E1",
        bbox_to_anchor=(0.5, 0.01),
    )

    fig.text(
        0.5, -0.025,
        "Fuentes cartográficas reales: geoBoundaries (BOL ADM1/ADM3, WGS84) y Natural Earth 10m (lagos y mancha urbana). "
        "No se representan trazados viales ni parcelas no verificadas en campo.",
        ha="center", va="top", fontsize=7.6, color="#475569", style="italic"
    )

    out_path = FIG_DIR / "fig_mapa_ubicacion_lapaz.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight", pad_inches=0.18, facecolor="white")
    plt.close(fig)
    return out_path


# ==============================================================================
# FIGURA 4: ESQUEMA EXPERIMENTAL Y CONTROL EN CASCADA (NIVEL 0 VS NIVEL 1)
# ==============================================================================

def generar_diseno_cascada_bloques():
    fig, ax = plt.subplots(figsize=(16.2, 11.2), dpi=300)
    ax.set_xlim(0, 16.2)
    ax.set_ylim(0, 11.2)
    ax.axis("off")

    ax.text(8.1, 10.85, "Esquema Experimental Comparativo y Arquitectura de Control Jerárquico en Cascada",
            ha="center", va="center", fontsize=14.0, fontweight="bold", color="#0F172A")
    ax.text(8.1, 10.48, "Contrastación entre Nivel 0 (manejo manual / testigo) y Nivel 1 (prototipo IoT–PID–IA) mediante protocolos E1–E8",
            ha="center", va="center", fontsize=9.6, color="#475569")

    # ================= BLOQUE A: NIVEL 0 (MANUAL / TESTIGO) =================
    ax.add_patch(FancyBboxPatch((0.30, 8.25), 15.60, 1.85, boxstyle="round,pad=0.05,rounding_size=0.18",
                                facecolor="#FEF2F2", edgecolor="#DC2626", linewidth=1.4, zorder=0))
    ax.text(0.55, 9.85, "NIVEL 0 — MANEJO MANUAL / TESTIGO DE LAZO ABIERTO (SIN AUTOMATIZACIÓN IoT–PID–IA)",
            ha="left", va="center", fontsize=9.4, fontweight="bold", color="#991B1B")

    draw_box(ax, 0.55, 8.48, 3.15, 1.05,
             title="Inspección Visual Periódica",
             body="Observación humana discontinua\nSin registro continuo T / HR / VPD",
             fc="#FFFFFF", ec="#EF4444", lw=1.3, title_size=8.6, body_size=7.5)
    draw_box(ax, 4.40, 8.48, 3.25, 1.05,
             title="Accionamiento Manual / On-Off",
             body="Apertura manual o histéresis ±0,5 °C\nConmutación brusca (TV_u elevado)",
             fc="#FFFFFF", ec="#EF4444", lw=1.3, title_size=8.6, body_size=7.5)
    draw_box(ax, 8.35, 8.48, 3.35, 1.05,
             title="Invernadero Testigo (Papa)",
             body="Expuesto a heladas altiplánicas\ny picos nocturnos de HR >= 90%",
             fc="#FFFFFF", ec="#EF4444", lw=1.3, title_size=8.6, body_size=7.5)
    draw_box(ax, 12.40, 8.48, 3.25, 1.05,
             title="Desempeño Esperado / Ref.",
             body="Sobreimpulso alto (Mp=9,27% sim.)\nDetección tardía de P. infestans",
             fc="#FFF1F2", ec="#B91C1C", lw=1.3, title_size=8.6, body_size=7.5)

    draw_arrow(ax, (3.72, 9.00), (4.38, 9.00), color="#B91C1C", lw=1.6)
    draw_arrow(ax, (7.67, 9.00), (8.33, 9.00), color="#B91C1C", lw=1.6)
    draw_arrow(ax, (11.72, 9.00), (12.38, 9.00), color="#B91C1C", lw=1.6)

    # ================= BLOQUE B: NIVEL 1 (CASCADA IoT-PID-IA) =================
    ax.add_patch(FancyBboxPatch((0.30, 2.55), 15.60, 5.42, boxstyle="round,pad=0.05,rounding_size=0.20",
                                facecolor="#F0FDF4", edgecolor="#15803D", linewidth=1.6, zorder=0))
    ax.text(0.55, 7.72, "NIVEL 1 — SISTEMA AUTOMATIZADO IoT–PID–IA EN CASCADA (ARQUITECTURA PROPUESTA)",
            ha="left", va="center", fontsize=9.6, fontweight="bold", color="#14532D")

    # Sub-contenedor Lazo Externo (y = 5.75 .. 7.42)
    ax.add_patch(FancyBboxPatch((0.55, 5.75), 15.10, 1.67, boxstyle="round,pad=0.04,rounding_size=0.16",
                                facecolor="#EFF6FF", edgecolor="#2563EB", linewidth=1.3, linestyle="--", zorder=1))
    ax.text(0.75, 7.22, "LAZO EXTERNO SUPERVISOR (T = 30 s | Docker: FastAPI + inference_worker)",
            ha="left", va="center", fontsize=8.6, fontweight="bold", color="#1E40AF", zorder=2)

    draw_box(ax, 0.75, 5.93, 3.15, 1.05,
             title="Visión Artificial (YOLO + SAHI)",
             body="YOLO26n / YOLO11n + SAHI 0.12.8\nFollaje y trampas -> MQTT /vision",
             fc="#FFFFFF", ec="#2563EB", lw=1.3, title_size=8.3, body_size=7.3, zorder=3)

    draw_box(ax, 4.48, 5.93, 3.95, 1.05,
             title="Fusión Multimodal de Riesgo",
             body="Score = 0,45·Clima + 0,35·Visión + 0,20·Tend.\nVentana 48 muestras (VPD, HR, LWH)",
             fc="#FFFFFF", ec="#1D4ED8", lw=1.4, title_size=8.3, body_size=7.3, zorder=3)

    draw_box(ax, 9.00, 5.93, 3.55, 1.05,
             title="Clasificador de Setpoints",
             body="BAJO (18°C/75%) | MEDIO (18,5°C/70%)\nALTO (19,5°C/65%) | CRÍTICO (20°C/60%)",
             fc="#FFFFFF", ec="#1D4ED8", lw=1.4, title_size=8.3, body_size=7.3, zorder=3)

    draw_box(ax, 13.05, 5.93, 2.40, 1.05,
             title="Alerta y Auditoría",
             body="Bot Telegram (ALTO/CRÍTICO)\nInfluxDB + SQLite + Django",
             fc="#FFFFFF", ec="#0284C7", lw=1.3, title_size=8.3, body_size=7.3, zorder=3)

    draw_arrow(ax, (3.92, 6.45), (4.46, 6.45), color="#1D4ED8", lw=1.5)
    draw_arrow(ax, (8.45, 6.45), (8.98, 6.45), color="#1D4ED8", lw=1.5)
    draw_arrow(ax, (12.57, 6.45), (13.03, 6.45), color="#0284C7", lw=1.5)

    # Corredor libre y = 4.92 .. 5.75 para las conexiones en cascada sin tocar títulos

    # Sub-contenedor Lazo Interno (y = 2.75 .. 4.92)
    ax.add_patch(FancyBboxPatch((0.55, 2.75), 15.10, 2.17, boxstyle="round,pad=0.04,rounding_size=0.16",
                                facecolor="#FFFFFF", edgecolor="#15803D", linewidth=1.4, zorder=1))
    ax.text(2.08, 4.72, "LAZO INTERNO RÁPIDO AUTÓNOMO (f = 10 Hz, dt = 0,1 s | ESP32 DevKit V1)",
            ha="left", va="center", fontsize=8.6, fontweight="bold", color="#14532D", zorder=2)

    # Nodo sumador
    sum_circle = patches.Circle((1.35, 3.85), 0.24, facecolor="#DCFCE7", edgecolor="#15803D", linewidth=1.5, zorder=4)
    ax.add_patch(sum_circle)
    ax.text(1.35, 3.85, "Σ", ha="center", va="center", fontsize=11.5, fontweight="bold", color="#14532D", zorder=5)
    ax.text(1.48, 4.18, "+", ha="left", va="bottom", fontsize=8.5, fontweight="bold", color="#1D4ED8")
    ax.text(1.66, 3.60, "−", ha="left", va="center", fontsize=9.5, fontweight="bold", color="#DC2626")

    draw_box(ax, 2.08, 3.42, 2.60, 0.92,
             title="Banda Muerta y PID",
             body="Deadband ±0,25 °C\nDerivada en PV + Anti-Windup",
             fc="#F0FDF4", ec="#16A34A", lw=1.3, title_size=8.2, body_size=7.2, zorder=3)

    draw_box(ax, 5.18, 3.42, 3.22, 0.92,
             title="Divisor Split-Range u ∈ [-100, 100]",
             body="u > 0: SSR 220V (GPIO23, 2 s)\nu < 0: MOSFET PWM 25 kHz (GPIO19)",
             fc="#F0FDF4", ec="#16A34A", lw=1.3, title_size=8.2, body_size=7.2, zorder=3)

    draw_box(ax, 8.90, 3.42, 2.90, 0.92,
             title="Planta: Invernadero Papa",
             body="FOPDT sim.: K=0,1639 °C/%\nτ=242,96 s | θ=33,33 s",
             fc="#FEFCE8", ec="#CA8A04", lw=1.4, title_size=8.2, body_size=7.2, zorder=3)

    draw_box(ax, 12.30, 3.42, 3.15, 0.92,
             title="Sensores + Borde 10 Hz",
             body="SHT31, DS18B20, BH1750, Cap. v1.2\nHampel + EMA + Tetens/Magnus VPD",
             fc="#ECFDF5", ec="#0D9488", lw=1.3, title_size=8.2, body_size=7.2, zorder=3)

    draw_arrow(ax, (1.59, 3.85), (2.06, 3.85), color="#15803D", lw=1.5)
    draw_arrow(ax, (4.70, 3.85), (5.16, 3.85), color="#15803D", lw=1.5)
    draw_arrow(ax, (8.42, 3.85), (8.88, 3.85), color="#CA8A04", lw=1.5)
    draw_arrow(ax, (11.82, 3.85), (12.28, 3.85), color="#0D9488", lw=1.5)

    # Realimentación inferior (Lazo Interno)
    ax.plot([13.88, 13.88, 1.35, 1.35], [3.40, 2.95, 2.95, 3.60], color="#DC2626", lw=1.4, zorder=3)
    draw_arrow(ax, (1.35, 3.10), (1.35, 3.60), color="#DC2626", lw=1.4)
    ax.text(7.60, 3.06, "Realimentación continua de T_filtrada, HR_filtrada y VPD (10 Hz en ESP32)",
            ha="center", va="bottom", fontsize=7.4, fontweight="bold", color="#991B1B",
            bbox=dict(boxstyle="round,pad=0.14", fc="white", ec="none"))

    # Conexiones ortogonales limpias en el corredor y = 5.18 / 5.45 (sin tocar títulos)
    draw_ortho_arrow(
        ax,
        [(10.78, 5.91), (10.78, 5.36), (1.35, 5.36), (1.35, 4.11)],
        color="#2563EB", lw=1.8,
        label="Setpoints dinámicos T_sp, HR_sp vía MQTT",
        label_pos=(5.10, 5.36), label_bg="#EFF6FF", label_size=7.5
    )
    draw_ortho_arrow(
        ax,
        [(13.88, 4.36), (13.88, 5.36), (11.20, 5.36), (11.20, 5.55), (6.45, 5.55), (6.45, 5.91)],
        color="#0D9488", lw=1.6, ls="--",
        label="Telemetría 1 Hz vía Mosquitto",
        label_pos=(12.50, 5.36), label_bg="#ECFDF5", label_size=7.4
    )

    # ================= BLOQUE C: MATRIZ DE EVALUACIÓN E1-E8 =================
    ax.add_patch(FancyBboxPatch((0.30, 0.35), 15.60, 1.95, boxstyle="round,pad=0.05,rounding_size=0.18",
                                facecolor="#F8FAFC", edgecolor="#334155", linewidth=1.4, zorder=0))
    ax.text(8.1, 2.08, "EVALUACIÓN EXPERIMENTAL CRUZADA: PROTOCOLOS E1–E8 (BASE SQLite / DISEÑO DE VALIDACIÓN)",
            ha="center", va="center", fontsize=9.3, fontweight="bold", color="#0F172A")

    protocolos = [
        ("E1", "Metrología\nSHT31 vs patrón\n(3.600 m s.n.m.)"),
        ("E2", "Escalón FOPDT\nIdentificación\n(K, τ, θ, R²)"),
        ("E3", "Sintonía PID\nOptuna vs ZN/CC\n(IAE, ITAE, Mp)"),
        ("E4", "Control VPD\nRango 0,8–1,2 kPa\n(PWM + Humid.)"),
        ("E5", "Visión Foliar\nYOLO26n / 11n\n(mAP, Latencia)"),
        ("E6", "Trampas + SAHI\nMosaicos 320x320\n(Recall plagas)"),
        ("E7", "Riesgo + SHAP\nXGBoost vs Blight\n(AUC, Brier)"),
        ("E8", "Resiliencia 24/7\nHelada altiplánica\n(Disponibilidad)"),
    ]
    start_x = 0.50
    card_w = 1.78
    gap = 0.135
    for idx, (cod, desc) in enumerate(protocolos):
        cx = start_x + idx * (card_w + gap)
        hdr_c = "#1D4ED8" if idx < 4 else "#6D28D9"
        draw_box(
            ax, cx, 0.52, card_w, 1.32,
            title=cod,
            body=desc,
            fc="#FFFFFF", ec=hdr_c, lw=1.2,
            header_fc=hdr_c, header_h=0.32, title_color="#FFFFFF",
            title_size=8.6, body_size=6.9, rounding=0.10
        )

    out_path = FIG_DIR / "fig_exp_diseno_cascada_bloques.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight", pad_inches=0.15, facecolor="white")
    plt.close(fig)
    return out_path


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    generados = [
        generar_modelo_v(),
        generar_arquitectura_real(),
        generar_mapa_lapaz(),
        generar_diseno_cascada_bloques(),
    ]
    for path in generados:
        print(f"[OK] Generado 300 dpi: {path}")


if __name__ == "__main__":
    main()
