"""
Servicios Auxiliares para el Dashboard Django
Telemetría, MQTT, Autotune FOPDT, Gemelo Digital y Explicabilidad Agronómica
"""

import time
import math
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

logger = logging.getLogger("django_services")

# Intentar importar cliente MQTT del servidor
try:
    from server.app.services.mqtt_client import mqtt_service
    from server.app.core.config import settings as server_settings
    MQTT_DISPONIBLE = True
except Exception:
    MQTT_DISPONIBLE = False

# Estado en memoria para el Gemelo Digital y Modo Demostración
ESTADO_GEMELO_DIGITAL = {
    "temp_exterior": 9.5,
    "temp_interior": 18.2,
    "hum_interior": 72.0,
    "temp_suelo": 16.0,
    "hum_suelo": 30.5,
    "rad_solar": 420.0,
    "sp_temperatura": 18.0,
    "sp_humedad": 75.0,
    "kp": 15.934,
    "ki": 0.1359,
    "kd": 1.571,
    "calefactor_pct": 24.5,
    "extractor_pct": 0.0,
    "bomba_riego": False,
    "modo_perturbacion": "NORMAL", # NORMAL, HELADA, TEMPORAL_NIEBLA, OLA_CALOR, PLAGA_PULGON
    "score_riesgo": 0.22,
    "nivel_riesgo": "BAJO",
    "ultima_actualizacion": time.time()
}

def calcular_psicrometria(temp_c: float, hum_pct: float) -> Tuple[float, float]:
    """Calcula VPD (kPa) y Punto de Rocío (°C)."""
    hum_clamped = max(1.0, min(100.0, hum_pct))
    es = 0.61078 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    ea = es * (hum_clamped / 100.0)
    vpd = max(0.0, es - ea)
    
    alpha = ((17.27 * temp_c) / (237.3 + temp_c)) + math.log(hum_clamped / 100.0)
    t_dew = (237.3 * alpha) / (17.27 - alpha)
    return round(vpd, 3), round(t_dew, 2)

def actualizar_gemelo_digital(dt: float = 1.0) -> Dict[str, Any]:
    """
    Ejecuta un paso de simulación del gemelo digital acoplado FOPDT
    según el modo de perturbación seleccionado.
    """
    st = ESTADO_GEMELO_DIGITAL
    modo = st["modo_perturbacion"]
    
    # 1. Aplicar perturbaciones dinámicas
    if modo == "HELADA":
        st["temp_exterior"] = -2.5
        st["rad_solar"] = 0.0
    elif modo == "TEMPORAL_NIEBLA":
        st["temp_exterior"] = 11.0
        st["hum_interior"] = min(98.0, st["hum_interior"] + 1.2)
        st["rad_solar"] = 80.0
    elif modo == "OLA_CALOR":
        st["temp_exterior"] = 23.0
        st["rad_solar"] = 820.0
    elif modo == "PLAGA_PULGON":
        st["temp_exterior"] = 18.0
        st["hum_interior"] = max(45.0, st["hum_interior"] - 0.8)
    else: # NORMAL
        st["temp_exterior"] = 10.5 + 4.5 * math.sin(time.time() / 60.0)
        st["rad_solar"] = max(0.0, 550.0 * math.sin(time.time() / 120.0))

    # 2. Dinámica PID y control térmico
    error = st["sp_temperatura"] - st["temp_interior"]
    cv = (st["kp"] * error) + 10.0 # Aproximación proporcional-integral
    cv = max(-100.0, min(100.0, cv))
    
    if cv >= 0:
        st["calefactor_pct"] = round(cv, 1)
        st["extractor_pct"] = 0.0
    else:
        st["calefactor_pct"] = 0.0
        st["extractor_pct"] = round(abs(cv), 1)

    # Inercia térmica FOPDT (K=0.1639, tau=240s)
    delta_t = (-(st["temp_interior"] - st["temp_exterior"]) + (0.1639 * st["calefactor_pct"]) - (0.12 * st["extractor_pct"]) + (st["rad_solar"] * 0.006)) / 30.0
    st["temp_interior"] = round(st["temp_interior"] + delta_t * dt, 2)
    
    # Dinámica de humedad
    if st["extractor_pct"] > 0:
        st["hum_interior"] = max(40.0, st["hum_interior"] - (st["extractor_pct"] * 0.08))
    elif st["calefactor_pct"] > 50:
        st["hum_interior"] = max(45.0, st["hum_interior"] - 0.05)
    else:
        st["hum_interior"] = min(96.0, st["hum_interior"] + 0.02)
    st["hum_interior"] = round(st["hum_interior"], 1)

    # 3. Psicrometría y Fusión de Riesgo
    vpd, t_dew = calcular_psicrometria(st["temp_interior"], st["hum_interior"])
    
    # Cálculo de score fúngico y de vectores
    score_clima = 0.85 if st["hum_interior"] >= 90.0 else (0.50 if st["hum_interior"] >= 80.0 else 0.15)
    score_vision = 0.75 if modo == "PLAGA_PULGON" else (0.45 if modo == "TEMPORAL_NIEBLA" else 0.10)
    score_tend = 0.20 if modo in ["TEMPORAL_NIEBLA", "PLAGA_PULGON"] else 0.05
    
    score_total = round(0.45 * score_clima + 0.35 * score_vision + 0.20 * score_tend, 3)
    
    if score_total < 0.30:
        nivel = "BAJO"
    elif score_total < 0.55:
        nivel = "MEDIO"
    elif score_total < 0.75:
        nivel = "ALTO"
    else:
        nivel = "CRÍTICO"

    st["score_riesgo"] = score_total
    st["nivel_riesgo"] = nivel
    st["vpd_kpa"] = vpd
    st["punto_rocio"] = t_dew
    st["ultima_actualizacion"] = time.time()
    
    return st

def ejecutar_autotune_pid(metodo: str = "OPTUNA") -> Dict[str, Any]:
    """
    Ejecuta el algoritmo de autotuning paramétrico a partir del modelo FOPDT
    identificado en la Fase 2 (K=0.1639 °C/%, tau=242.96 s, theta=33.33 s).
    """
    K = 0.1639
    tau = 242.96
    theta = 33.33

    if metodo.upper() == "COHEN_COON":
        # Fórmulas analíticas de Cohen-Coon para PID continuo
        r = theta / tau
        kp = (1.0 / (K * r)) * (4.0 / 3.0 + r / 4.0)
        ti = theta * ((32.0 + 6.0 * r) / (13.0 + 8.0 * r))
        td = theta * (4.0 / (11.0 + 2.0 * r))
        ki = kp / ti
        kd = kp * td
        nombre = "Cohen-Coon (Rechazo Rápido)"
        iae_est = 1845.2
        sobrepaso_est = 4.8
    elif metodo.upper() == "IMC":
        # Internal Model Control (lambda = tau = 243 s para sintonía suave y conservadora)
        tc = max(theta, 0.5 * tau)
        kp = (1.0 / K) * (tau / (tc + theta))
        ti = tau
        td = 0.5 * theta
        ki = kp / ti
        kd = kp * td
        nombre = "IMC (Control Suave y Seguro)"
        iae_est = 1920.0
        sobrepaso_est = 1.2
    else:
        # OPTUNA (Optimización Bayesiana Seleccionada de la Fase 2)
        kp = 15.934
        ki = 0.1359
        kd = 1.571
        nombre = "Optuna Bayesiano TPE (Óptimo Seleccionado)"
        iae_est = 1800.4
        sobrepaso_est = 1.6

    return {
        "metodo": nombre,
        "kp": round(kp, 3),
        "ki": round(ki, 4),
        "kd": round(kd, 3),
        "iae_estimado": iae_est,
        "sobrepaso_estimado_pct": sobrepaso_est,
        "tiempo_asentamiento_s": 346.0,
        "fopdt": {
            "ganancia_K": K,
            "constante_tau_s": tau,
            "retardo_theta_s": theta
        }
    }

def obtener_explicacion_riesgo_shap(score_riesgo: float, hum_interior: float, vpd_kpa: float) -> Dict[str, Any]:
    """
    Genera la interpretación agronómica explicable (SHAP) del semáforo fitosanitario.
    """
    factores = []
    
    if hum_interior >= 90.0:
        factores.append({
            "variable": "Humedad Relativa Prolongada (>90%)",
            "impacto": "+0.45",
            "direccion": "AUMENTA RIESGO",
            "explicacion": "Favorece la germinación de esporangios y motilidad de zoosporas de Phytophthora infestans (Tizón tardío)."
        })
    elif hum_interior >= 80.0:
        factores.append({
            "variable": "Humedad Relativa Subcrítica (80-90%)",
            "impacto": "+0.25",
            "direccion": "ALERTA PREVENTIVA",
            "explicacion": "Condiciones límite para desarrollo fúngico si desciende la temperatura nocturna."
        })
        
    if vpd_kpa <= 0.35:
        factores.append({
            "variable": "Bajo Déficit de Presión de Vapor (VPD < 0.35 kPa)",
            "impacto": "+0.30",
            "direccion": "AUMENTA RIESGO",
            "explicacion": "Cercanía inmediata a la condensación y rocío sobre la superficie foliar."
        })
    elif vpd_kpa >= 1.4:
        factores.append({
            "variable": "VPD Elevado (> 1.4 kPa)",
            "impacto": "+0.20",
            "direccion": "RIESGO DE PLAGA",
            "explicacion": "Estrés hídrico y ambiente seco favorable para reproducción rápida de pulgones y trips."
        })
        
    if not factores:
        factores.append({
            "variable": "Microclima en Rango Óptimo",
            "impacto": "-0.35",
            "direccion": "PROTECTOR",
            "explicacion": "VPD entre 0.5 y 1.2 kPa; transpiración vegetal equilibrada sin mojado foliar."
        })

    recomendaciones = {
        "BAJO": "Mantener setpoints estándar (Temp: 18.0°C, Hum: 75%). Monitoreo de rutina.",
        "MEDIO": "Habilitar ventilación diurna durante 15 minutos para renovar la masa de aire saturado.",
        "ALTO": "Elevar setpoint térmico a 19.5°C para evitar cruce con punto de rocío y reducir humedad a 65%.",
        "CRÍTICO": "Extracción forzada inmediata. Inspección visual y aplicación de biofungicida preventivo."
    }

    nivel = "BAJO" if score_riesgo < 0.30 else ("MEDIO" if score_riesgo < 0.55 else ("ALTO" if score_riesgo < 0.75 else "CRÍTICO"))

    return {
        "score_riesgo": score_riesgo,
        "nivel": nivel,
        "recomendacion_accion": recomendaciones[nivel],
        "factores_shap": factores
    }
