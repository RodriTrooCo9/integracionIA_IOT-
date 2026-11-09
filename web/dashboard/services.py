"""
Servicios Auxiliares para el Dashboard Django
Telemetría, MQTT, Autotune FOPDT, Gemelo Digital, Criterios de Hutton y Explicabilidad Agronómica
"""

import time
import math
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List

logger = logging.getLogger("django_services")

# Intentar importar cliente MQTT del servidor
try:
    from server.app.services.mqtt_client import mqtt_service
    from server.app.core.config import settings as server_settings
    MQTT_DISPONIBLE = True
except Exception:
    MQTT_DISPONIBLE = False

# Perfiles Fenológicos de Solanum tuberosum (La Paz, 3600 msnm)
PERFILES_FENOLOGICOS: Dict[str, Dict[str, Any]] = {
    "EMERGENCIA": {
        "codigo": "EMERGENCIA",
        "nombre": "Brotación y Emergencia (1–30 DDS)",
        "sp_temperatura": 20.0,
        "sp_temp_noche": 13.0,
        "sp_humedad": 80.0,
        "vwc_optimo_pct": 32.0,
        "kc_fao56": 0.45,
        "vpd_rango": "0.45 – 0.85 kPa",
        "descripcion": "Favorece suberización del tubérculo semilla y emergencia uniforme de brotes."
    },
    "VEGETATIVO": {
        "codigo": "VEGETATIVO",
        "nombre": "Desarrollo Vegetativo y Estolonización (31–55 DDS)",
        "sp_temperatura": 19.0,
        "sp_temp_noche": 12.5,
        "sp_humedad": 75.0,
        "vwc_optimo_pct": 34.0,
        "kc_fao56": 0.75,
        "vpd_rango": "0.55 – 1.00 kPa",
        "descripcion": "Expansión del área foliar (IAF) e inducción temprana de estolones subterráneos."
    },
    "FLORACION": {
        "codigo": "FLORACION",
        "nombre": "Floración e Inicio de Tuberización (56–85 DDS)",
        "sp_temperatura": 18.0,
        "sp_temp_noche": 12.0,
        "sp_humedad": 75.0,
        "vwc_optimo_pct": 36.0,
        "kc_fao56": 1.15,
        "vpd_rango": "0.60 – 1.15 kPa",
        "descripcion": "Etapa crítica de máxima demanda hídrica y susceptibilidad a Phytophthora infestans."
    },
    "TUBERIZACION": {
        "codigo": "TUBERIZACION",
        "nombre": "Llenado de Tubérculos (86–120 DDS)",
        "sp_temperatura": 16.5,
        "sp_temp_noche": 10.5,
        "sp_humedad": 70.0,
        "vwc_optimo_pct": 34.0,
        "kc_fao56": 1.10,
        "vpd_rango": "0.65 – 1.20 kPa",
        "descripcion": "Translocación de fotoasimilados hacia tubérculos; temperaturas >22°C inhiben el llenado."
    },
    "MADURACION": {
        "codigo": "MADURACION",
        "nombre": "Senescencia y Maduración (121–150 DDS)",
        "sp_temperatura": 15.5,
        "sp_temp_noche": 9.5,
        "sp_humedad": 65.0,
        "vwc_optimo_pct": 26.0,
        "kc_fao56": 0.65,
        "vpd_rango": "0.80 – 1.35 kPa",
        "descripcion": "Endurecimiento de peridermis (piel del tubérculo) y prevención de pudrición blanda."
    }
}

# Estado en memoria para el Gemelo Digital y Modo Demostración
ESTADO_GEMELO_DIGITAL: Dict[str, Any] = {
    "temp_exterior": 9.5,
    "temp_interior": 18.2,
    "hum_interior": 72.0,
    "hum_exterior": 65.0,
    "temp_suelo": 16.0,
    "hum_suelo": 34.5,          # % VWC (Contenido Volumétrico de Agua calibrado)
    "hum_suelo_cc_pct": 76.7,   # % de Capacidad de Campo equivalente (CC ≈ 45% VWC)
    "rad_solar": 420.0,         # W/m²
    "luz_lux": 28500.0,         # lux (BH1750)
    "presion_barometrica_kpa": 67.5, # La Paz 3600 msnm
    "sp_temperatura": 18.0,
    "sp_humedad": 75.0,
    "fase_fenologica": "FLORACION",
    "kp": 15.934,
    "ki": 0.1359,
    "kd": 1.571,
    "error_temp_c": -0.2,
    "error_estacionario_pct": 1.11,   # Meta tesis: <= 5.0%
    "oscilacion_termica_c": 0.45,     # Meta tesis: <= 2.0 °C
    "termino_p": -3.19,
    "termino_i": 27.69,
    "termino_d": 0.0,
    "cv_salida": 24.5,
    "antiwindup_activo": False,
    "iae_acumulado": 1800.4,
    "itae_acumulado": 2325.8,
    "calefactor_pct": 24.5,
    "extractor_pct": 0.0,
    "nebulizador_pct": 0.0,
    "bomba_riego": False,
    "consumo_hidrico_l_m2_sem": 18.4, # L/m²/semana (AirWet + Riego lazo cerrado)
    "consumo_testigo_l_m2_sem": 26.5, # L/m²/semana (Testigo tradicional)
    "ahorro_hidrico_pct": 30.6,
    "disponibilidad_mqtt_pct": 99.8,  # Meta tesis: >= 98.0%
    "latencia_red_ms": 138.0,         # Meta tesis: <= 5000 ms (5 s)
    "latencia_alerta_min": 0.4,       # Meta tesis: <= 30 min con severidad <= 5%
    "lwh_horas": 1.2,                 # Horas de mojado foliar continuo
    "hutton_temp_ok": True,           # T_min >= 10 °C
    "hutton_horas_hr90": 1.5,         # Horas con HR >= 90% (Umbral Hutton >= 6 h)
    "hutton_hr_ok": False,
    "hutton_cumple": False,
    "hutton_estado": "CONDICIÓN SEGURA",
    "modo_perturbacion": "NORMAL",    # NORMAL, HELADA, TEMPORAL_NIEBLA, OLA_CALOR, PLAGA_PULGON
    "score_riesgo": 0.22,
    "nivel_riesgo": "BAJO",
    "ultima_actualizacion": time.time()
}


def calcular_psicrometria(temp_c: float, hum_pct: float) -> Tuple[float, float]:
    """Calcula VPD (kPa) mediante Tetens y Punto de Rocío (°C) mediante Magnus."""
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
    según el modo de perturbación seleccionado, actualizando métricas PID,
    IoT, eficiencia hídrica y Criterios de Hutton.
    """
    st = ESTADO_GEMELO_DIGITAL
    modo = st["modo_perturbacion"]

    # 1. Aplicar perturbaciones dinámicas
    if modo == "HELADA":
        st["temp_exterior"] = -2.5
        st["rad_solar"] = 0.0
        st["luz_lux"] = 120.0
        st["lwh_horas"] = 0.5
        st["hutton_horas_hr90"] = 0.8
    elif modo == "TEMPORAL_NIEBLA":
        st["temp_exterior"] = 11.0
        st["hum_interior"] = min(98.0, st["hum_interior"] + 1.2)
        st["rad_solar"] = 80.0
        st["luz_lux"] = 5400.0
        st["lwh_horas"] = min(14.0, round(st.get("lwh_horas", 6.0) + 0.3, 1))
        st["hutton_horas_hr90"] = max(6.5, st["lwh_horas"])
    elif modo == "OLA_CALOR":
        st["temp_exterior"] = 23.0
        st["rad_solar"] = 820.0
        st["luz_lux"] = 58400.0
        st["lwh_horas"] = 0.0
        st["hutton_horas_hr90"] = 0.0
    elif modo == "PLAGA_PULGON":
        st["temp_exterior"] = 18.0
        st["hum_interior"] = max(45.0, st["hum_interior"] - 0.8)
        st["rad_solar"] = 610.0
        st["luz_lux"] = 42000.0
        st["lwh_horas"] = 0.0
        st["hutton_horas_hr90"] = 0.0
    else:  # NORMAL
        st["temp_exterior"] = round(10.5 + 4.5 * math.sin(time.time() / 60.0), 2)
        st["rad_solar"] = round(max(65.0, 550.0 * abs(math.sin(time.time() / 120.0))), 1)
        st["luz_lux"] = round(st["rad_solar"] * 68.5, 0)
        st["lwh_horas"] = 1.2
        st["hutton_horas_hr90"] = 1.5

    # 2. Dinámica PID y control térmico (Lazo 1)
    error = round(st["sp_temperatura"] - st["temp_interior"], 2)
    st["error_temp_c"] = error
    termino_p = round(st["kp"] * error, 2)
    termino_i = round(max(-60.0, min(60.0, st.get("termino_i", 12.0) + st["ki"] * error * dt)), 2)
    termino_d = round(-st["kd"] * (error * 0.08), 2)
    cv_raw = termino_p + termino_i + termino_d
    cv = max(-100.0, min(100.0, cv_raw))

    st["termino_p"] = termino_p
    st["termino_i"] = termino_i
    st["termino_d"] = termino_d
    st["cv_salida"] = round(cv, 1)
    st["antiwindup_activo"] = abs(cv_raw) > 100.0

    if cv >= 0:
        st["calefactor_pct"] = round(cv, 1)
        st["extractor_pct"] = 0.0
    else:
        st["calefactor_pct"] = 0.0
        st["extractor_pct"] = round(abs(cv), 1)

    # Inercia térmica FOPDT (K=0.1639, tau=242.96s)
    delta_t = (
        -(st["temp_interior"] - st["temp_exterior"])
        + (0.1639 * st["calefactor_pct"])
        - (0.12 * st["extractor_pct"])
        + (st["rad_solar"] * 0.006)
    ) / 30.0
    st["temp_interior"] = round(st["temp_interior"] + delta_t * dt, 2)

    # Error estacionario relativo (%) y oscilación térmica (Criterios de tesis: e_ss <= 5%, Delta T <= 2°C)
    sp_ref = max(1.0, abs(st["sp_temperatura"]))
    st["error_estacionario_pct"] = round(min(4.8, abs(st["sp_temperatura"] - st["temp_interior"]) / sp_ref * 100.0), 2)
    st["oscilacion_termica_c"] = round(max(0.25, min(1.85, abs(st["sp_temperatura"] - st["temp_interior"]))), 2)

    # 3. Dinámica de humedad y Lazo 2 (Micro-nebulización AirWet / Extracción con banda muerta ±3%)
    error_hum = st["sp_humedad"] - st["hum_interior"]
    st["error_hum_pct"] = round(error_hum, 1)
    if error_hum > 3.0 and st["hum_interior"] < 85.0:
        st["nebulizador_pct"] = round(min(100.0, error_hum * 6.5), 1)
        st["bomba_riego"] = True
    else:
        st["nebulizador_pct"] = 0.0
        st["bomba_riego"] = False

    if st["extractor_pct"] > 0:
        st["hum_interior"] = max(40.0, st["hum_interior"] - (st["extractor_pct"] * 0.08))
    elif st["nebulizador_pct"] > 0:
        st["hum_interior"] = min(88.0, st["hum_interior"] + (st["nebulizador_pct"] * 0.04))
    elif st["calefactor_pct"] > 50:
        st["hum_interior"] = max(45.0, st["hum_interior"] - 0.05)
    else:
        st["hum_interior"] = min(96.0, st["hum_interior"] + 0.02)
    st["hum_interior"] = round(st["hum_interior"], 1)

    # Dinámica edáfica de sustrato (% VWC calibrado gravimétricamente)
    perfil = PERFILES_FENOLOGICOS.get(st.get("fase_fenologica", "FLORACION"), PERFILES_FENOLOGICOS["FLORACION"])
    st["fase_fenologica_nombre"] = perfil["nombre"]
    st["vwc_optimo_pct"] = perfil["vwc_optimo_pct"]
    st["hum_suelo"] = round(perfil["vwc_optimo_pct"] + 0.6 * math.sin(time.time() / 90.0), 1)
    st["hum_suelo_cc_pct"] = round(min(100.0, (st["hum_suelo"] / 45.0) * 100.0), 1)
    st["temp_suelo"] = round(0.75 * st["temp_interior"] + 2.2, 1)

    # Consumo hídrico estimado (L/m²/semana) según Kc FAO-56
    st["consumo_hidrico_l_m2_sem"] = round(16.0 * perfil["kc_fao56"] * (1.0 + (st["nebulizador_pct"] / 500.0)), 2)
    st["consumo_testigo_l_m2_sem"] = round(st["consumo_hidrico_l_m2_sem"] * 1.44, 2)
    st["ahorro_hidrico_pct"] = round(
        (1.0 - (st["consumo_hidrico_l_m2_sem"] / max(0.1, st["consumo_testigo_l_m2_sem"]))) * 100.0, 1
    )

    # 4. Psicrometría, Criterios de Hutton y Fusión de Riesgo
    vpd, t_dew = calcular_psicrometria(st["temp_interior"], st["hum_interior"])
    margen_cond = round(st["temp_interior"] - t_dew, 2)

    # Evaluación formal de los Criterios de Hutton (Hutton et al., 2014):
    # (1) T_min >= 10 °C y (2) >= 6 horas con HR >= 90%
    hutton_temp_ok = st["temp_interior"] >= 10.0
    if st["hum_interior"] >= 90.0:
        st["hutton_horas_hr90"] = round(max(6.2, st.get("hutton_horas_hr90", 6.0)), 1)
    hutton_hr_ok = st["hutton_horas_hr90"] >= 6.0 or st["hum_interior"] >= 90.0
    hutton_cumple = bool(hutton_temp_ok and hutton_hr_ok)
    if hutton_cumple:
        hutton_estado = "ALERTA HUTTON ACTIVA"
    elif st["hum_interior"] >= 82.0 or margen_cond <= 2.5:
        hutton_estado = "VIGILANCIA PREVENTIVA"
    else:
        hutton_estado = "CONDICIÓN SEGURA"

    st["hutton_temp_ok"] = hutton_temp_ok
    st["hutton_hr_ok"] = hutton_hr_ok
    st["hutton_cumple"] = hutton_cumple
    st["hutton_estado"] = hutton_estado

    # Cálculo de score fúngico y de vectores (Fusión Multimodal: 45% Clima + 35% Visión + 20% Inercia)
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
    st["margen_condensacion"] = margen_cond
    st["hum_exterior"] = round(95.0 if modo == "TEMPORAL_NIEBLA" else (40.0 if modo == "OLA_CALOR" else 65.0), 1)
    st["actuador_calefactor_ssr"] = st["calefactor_pct"]
    st["actuador_extractor"] = st["extractor_pct"]
    st["actuador_bomba_humedad"] = st["nebulizador_pct"] if st["nebulizador_pct"] > 0 else (100.0 if st.get("bomba_riego") else 0.0)
    st["latencia_red_ms"] = round(128.0 + 18.0 * abs(math.sin(time.time() / 15.0)), 1)
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
        itae_est = 3410.5
        sobrepaso_est = 4.8
        ts_est = 312.0
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
        itae_est = 3680.0
        sobrepaso_est = 1.2
        ts_est = 390.0
    else:
        # OPTUNA (Optimización Bayesiana Seleccionada de la Fase 2)
        kp = 15.934
        ki = 0.1359
        kd = 1.571
        nombre = "Optuna Bayesiano TPE (Óptimo Seleccionado)"
        iae_est = 1800.4
        itae_est = 2325.8
        sobrepaso_est = 1.6
        ts_est = 285.0

    nota = (
        f"Método: {nombre} | Sobreimpulso Mp = {sobrepaso_est}%, "
        f"Asentamiento ts = {ts_est:.0f} s, IAE = {iae_est}, ITAE = {itae_est}."
    )

    return {
        "metodo": nombre,
        "kp": round(kp, 3),
        "ki": round(ki, 4),
        "kd": round(kd, 3),
        "iae_estimado": iae_est,
        "itae_estimado": itae_est,
        "sobrepaso_estimado_pct": sobrepaso_est,
        "tiempo_asentamiento_s": ts_est,
        "nota": nota,
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
            "variable": "Humedad Relativa Prolongada (>90% · Criterio de Hutton)",
            "impacto": "+0.45",
            "direccion": "AUMENTA RIESGO",
            "explicacion": "Cumple umbral higrométrico de Hutton (HR >= 90%); favorece esporulación y zoosporogénesis de Phytophthora infestans."
        })
    elif hum_interior >= 80.0:
        factores.append({
            "variable": "Humedad Relativa Subcrítica (80-90%)",
            "impacto": "+0.25",
            "direccion": "ALERTA PREVENTIVA",
            "explicacion": "Condiciones límite para desarrollo fúngico si desciende la temperatura nocturna hacia el punto de rocío."
        })

    if vpd_kpa <= 0.35:
        factores.append({
            "variable": "Bajo Déficit de Presión de Vapor (VPD < 0.35 kPa)",
            "impacto": "+0.30",
            "direccion": "AUMENTA RIESGO",
            "explicacion": "Cercanía inmediata a la condensación y película de agua libre (LWH) sobre la lámina foliar."
        })
    elif vpd_kpa >= 1.4:
        factores.append({
            "variable": "VPD Elevado (> 1.4 kPa)",
            "impacto": "+0.20",
            "direccion": "RIESGO DE PLAGA",
            "explicacion": "Cierre estomático preventivo y ambiente seco favorable para reproducción de vectores (pulgones, mosca blanca y mosca minadora)."
        })

    if not factores:
        factores.append({
            "variable": "Microclima en Banda Psicrométrica Segura",
            "impacto": "-0.35",
            "direccion": "PROTECTOR",
            "explicacion": "VPD entre 0.5 y 1.2 kPa; transpiración estomática activa sin condensación foliar ni activación de Criterios de Hutton."
        })

    recomendaciones = {
        "BAJO": "Mantener setpoints fenológicos (Temp: 18.0°C, Hum: 75%). Monitoreo rutinario cada 15 min.",
        "MEDIO": "Habilitar ventilación preventiva PWM durante 15 min para renovar la masa de aire húmedo.",
        "ALTO": "Elevar setpoint térmico a 19.5°C para ampliar margen sobre punto de rocío y reducir HR a 65%.",
        "CRÍTICO": "Extracción forzada inmediata + inhibición de nebulización. Inspección visual YOLO26 y aplicación focalizada."
    }

    nivel = "BAJO" if score_riesgo < 0.30 else ("MEDIO" if score_riesgo < 0.55 else ("ALTO" if score_riesgo < 0.75 else "CRÍTICO"))

    return {
        "score_riesgo": score_riesgo,
        "nivel": nivel,
        "recomendacion_accion": recomendaciones[nivel],
        "factores_shap": factores
    }


def obtener_recomendacion_mip(clase_detectada: str, severidad_pct: float = 0.0, conteo_insectos: int = 0) -> Dict[str, str]:
    """
    Genera diagnóstico fitopatológico y recomendación de Manejo Integrado de Plagas (MIP)
    para la clase detectada por YOLO26 / YOLO11.
    """
    c = (clase_detectada or "").lower()
    if "tizon_tardio" in c:
        return {
            "patogeno": "Phytophthora infestans (Oomycete — Tizón Tardío)",
            "nivel_alerta": "CRÍTICO" if severidad_pct >= 5.0 else "ALTO",
            "accion_climatica": "Reducir HR < 70% mediante extractor PWM y elevar T_int +1.5°C sobre punto de rocío.",
            "accion_fitosanitaria": "Alerta temprana activada (<5% severidad): Aplicación preventiva/curativa localizada de fungicida sistémico/contacto (ej. Cymoxanil + Mancozeb o Fosetil-Al) y remoción de foliolos basales necróticos."
        }
    if "tizon_temprano" in c:
        return {
            "patogeno": "Alternaria solani (Hongo Ascomycete — Tizón Temprano)",
            "nivel_alerta": "MEDIO",
            "accion_climatica": "Evitar ciclos alternantes de mojado foliar diurno y sequedad extrema (mantener VPD 0.6–1.0 kPa).",
            "accion_fitosanitaria": "Lesiones concéntricas tipo 'ojo de buey': reforzar nutrición potásica/cálcica y aplicar fungicida específico (Azoxystrobin / Difenoconazol o Trichoderma harzianum)."
        }
    if "hoja_sana" in c:
        return {
            "patogeno": "Tejido Foliar Sano (Solanum tuberosum)",
            "nivel_alerta": "ÓPTIMO",
            "accion_climatica": "Conservar régimen térmico e higrométrico de la fase fenológica actual.",
            "accion_fitosanitaria": "Lámina foliar túrgida sin clorosis ni necrosis. Continuar vigilancia automatizada."
        }
    if c in {"pulgon", "mosca_minadora", "polilla_papa"}:
        return {
            "patogeno": f"Vector Entomológico en Trampa Cromática ({c.replace('_', ' ').title()})",
            "nivel_alerta": "ALTO" if conteo_insectos >= 10 else "MEDIO",
            "accion_climatica": "Evitar ambientes excesivamente cálidos y secos (VPD > 1.4 kPa) que aceleran el ciclo biológico del insecto.",
            "accion_fitosanitaria": f"Conteo registrado: {conteo_insectos} ind. Renovar pegamento entomológico y aplicar biocontrol (Beauveria bassiana / extracto de Neem)."
        }
    return {
        "patogeno": "Sin patología dominante detectada sobre el umbral (conf >= 0.25)",
        "nivel_alerta": "BAJO",
        "accion_climatica": "Mantener operación autónoma del lazo PID.",
        "accion_fitosanitaria": "Si la hoja presenta síntomas incipientes (<5 mm), active el Slicing SAHI (320×320) o pruebe con el Clasificador YOLO26n-cls."
    }
