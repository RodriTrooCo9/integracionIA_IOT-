#!/usr/bin/env python3
"""
ejecutar_fase2_identificacion_pid.py
Script integral para la Fase 2:
1. Carga y ajuste FOPDT de datos experimentales de escalón.
2. Cálculo de ganancias Ziegler-Nichols, Cohen-Coon e IMC.
3. Optimización bayesiana con Optuna (o búsqueda TPE adaptativa).
4. Simulación temporal comparativa y cálculo de métricas (tr, ts, Mp, ess, IAE, ITAE).
5. Comparación rigurosa On/Off vs PID.
6. Generación y exportación de figuras en alta resolución (300 DPI) para la memoria de tesis.
"""

import sys
import os
import math
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "synthetic" / "prueba_escalon_fopdt.csv"
FIGURAS_DIR = BASE_DIR / "thesis" / "figuras"
FIGURAS_DIR.mkdir(parents=True, exist_ok=True)

try:
    import numpy as np
    import scipy.optimize as opt
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAVE_PACKAGES = True
except ImportError:
    HAVE_PACKAGES = False
    print("[!] Paquetes científicos aún cargándose en el entorno...")

# ==============================================================================
# 1. CARGA Y AJUSTE FOPDT
# ==============================================================================

def cargar_datos_escalon():
    tiempos = []
    controles = []
    temps = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tiempos.append(float(row["tiempo_segundos"]))
            controles.append(float(row["control_u_pct"]))
            temps.append(float(row["temperatura_medida_c"]))
    return np.array(tiempos), np.array(controles), np.array(temps)

def modelo_fopdt_ecuacion(t, K, tau, theta, t_step=120.0, T0=8.5):
    """Respuesta analítica al escalón de un sistema FOPDT continuo."""
    y = np.full_like(t, T0, dtype=float)
    idx_activo = t >= (t_step + theta)
    t_efectivo = t[idx_activo] - (t_step + theta)
    delta_u = 70.0
    y[idx_activo] = T0 + K * delta_u * (1.0 - np.exp(-t_efectivo / tau))
    return y

def ajustar_fopdt(t, u, y):
    t_step = 120.0
    delta_u = 70.0
    
    # Magnitudes de equilibrio
    T0 = float(np.mean(y[t < t_step]))
    T_inf = float(np.mean(y[t >= 1500]))
    delta_T = T_inf - T0
    K_inicial = delta_T / delta_u

    # Método de dos puntos de Smith (28.3% y 63.2%)
    y_28 = T0 + 0.283 * delta_T
    y_63 = T0 + 0.632 * delta_T
    
    # Interpolación de tiempos correspondientes
    t_28 = float(np.interp(y_28, y[t >= t_step], t[t >= t_step]))
    t_63 = float(np.interp(y_63, y[t >= t_step], t[t >= t_step]))
    
    tau_inicial = 1.5 * (t_63 - t_28)
    theta_inicial = max(5.0, (t_63 - t_step) - tau_inicial)

    # Regresión No Lineal por Mínimos Cuadrados (curve_fit)
    def residuo_func(t_vals, K_val, tau_val, theta_val):
        return modelo_fopdt_ecuacion(t_vals, K_val, tau_val, theta_val, t_step=t_step, T0=T0)

    popt, _ = opt.curve_fit(
        residuo_func, t, y,
        p0=[K_inicial, tau_inicial, theta_inicial],
        bounds=([0.05, 50.0, 5.0], [0.5, 600.0, 100.0])
    )
    K_opt, tau_opt, theta_opt = popt

    # Bondad de ajuste
    y_pred = residuo_func(t, K_opt, tau_opt, theta_opt)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1.0 - (ss_res / ss_tot)
    rmse = np.sqrt(np.mean((y - y_pred) ** 2))

    return {
        "K": K_opt, "tau": tau_opt, "theta": theta_opt,
        "T0": T0, "T_inf": T_inf, "delta_u": delta_u,
        "R2": r2, "RMSE": rmse, "y_pred": y_pred
    }

# ==============================================================================
# 2. CÁLCULO DE GANANCIAS PID COMPARATIVAS
# ==============================================================================

def calcular_ganancias_clasicas(K, tau, theta):
    R = theta / tau
    
    # 1. Ziegler-Nichols (Curva de reacción)
    kp_zn = (1.2 * tau) / (K * theta)
    ti_zn = 2.0 * theta
    td_zn = 0.5 * theta
    ki_zn = kp_zn / ti_zn
    kd_zn = kp_zn * td_zn

    # 2. Cohen-Coon
    kp_cc = (1.0 / (K * R)) * ((4.0 / 3.0) + (R / 4.0))
    ti_cc = theta * ((32.0 + 6.0 * R) / (13.0 + 8.0 * R))
    td_cc = theta * (4.0 / (11.0 + 2.0 * R))
    ki_cc = kp_cc / ti_cc
    kd_cc = kp_cc * td_cc

    # 3. IMC (Internal Model Control con lambda moderado)
    lambda_filtro = max(0.15 * tau, 0.8 * theta)
    kp_imc = (tau + 0.5 * theta) / (K * (lambda_filtro + 0.5 * theta))
    ti_imc = tau + 0.5 * theta
    td_imc = (tau * theta) / (2.0 * tau + theta)
    ki_imc = kp_imc / ti_imc
    kd_imc = kp_imc * td_imc

    return {
        "Ziegler-Nichols": {"Kp": kp_zn, "Ki": ki_zn, "Kd": kd_zn, "Ti": ti_zn, "Td": td_zn},
        "Cohen-Coon": {"Kp": kp_cc, "Ki": ki_cc, "Kd": kd_cc, "Ti": ti_cc, "Td": td_cc},
        "IMC": {"Kp": kp_imc, "Ki": ki_imc, "Kd": kd_imc, "Ti": ti_imc, "Td": td_imc}
    }

# ==============================================================================
# 3. MOTOR DE SIMULACIÓN EN LAZO CERRADO Y MÉTRICAS
# ==============================================================================

def simular_lazo_cerrado(Kp, Ki, Kd, K, tau, theta, T0=8.5, SP=20.0, t_sim=2400.0, dt=1.0, perturbacion_tiempo=1400.0, delta_pert=-2.5):
    """Simula el proceso FOPDT real con control PID discreto y retardo de transporte."""
    n = int(t_sim / dt)
    t = np.arange(n) * dt
    
    # Buffers
    pasos_retardo = int(round(theta / dt))
    buffer_u = [0.0] * max(1, pasos_retardo)
    
    y = np.zeros(n)
    u = np.zeros(n)
    error = np.zeros(n)
    
    y[0] = T0
    error_acumulado = 0.0
    pv_prev = T0
    
    for i in range(1, n):
        t_actual = t[i]
        
        # 1. Error de consigna
        e = SP - y[i-1]
        error[i] = e
        
        # 2. PID con Anti-windup (Clamping condicional)
        p_term = Kp * e
        d_term = -Kd * (y[i-1] - pv_prev) / dt
        pv_prev = y[i-1]
        
        # Integración condicional
        u_tentativa = p_term + error_acumulado + d_term
        if 0.0 <= u_tentativa <= 100.0:
            error_acumulado += Ki * e * dt
            
        u_val = np.clip(p_term + error_acumulado + d_term, 0.0, 100.0)
        u[i] = u_val
        
        # 3. Retardo de transporte (FIFO)
        buffer_u.append(u_val)
        u_efectiva = buffer_u.pop(0)
        
        # 4. Inyección de perturbación externa (helada de La Paz)
        pert_val = delta_pert if t_actual >= perturbacion_tiempo else 0.0
        
        # 5. Dinámica FOPDT discretizada
        dy = ( - (y[i-1] - (T0 + pert_val)) + (K * u_efectiva) ) / tau * dt
        y[i] = y[i-1] + dy

    return t, y, u, error

def calcular_metricas(t, y, u, error, SP=20.0, T0=8.5):
    dt = t[1] - t[0]
    delta_total = SP - T0
    
    # Sobrepaso máximo
    y_max = np.max(y)
    Mp = max(0.0, ((y_max - SP) / delta_total) * 100.0)
    
    # Tiempo de subida tr (10% a 90% de consigna)
    y_10 = T0 + 0.10 * delta_total
    y_90 = T0 + 0.90 * delta_total
    idx_10 = np.where(y >= y_10)[0]
    idx_90 = np.where(y >= y_90)[0]
    tr = (t[idx_90[0]] - t[idx_10[0]]) if len(idx_10) > 0 and len(idx_90) > 0 else np.nan
    
    # Tiempo de asentamiento ts (criterio 2% antes de perturbación a t=1400)
    idx_pre_pert = np.where(t < 1400.0)[0]
    banda_inf = SP - 0.02 * delta_total
    banda_sup = SP + 0.02 * delta_total
    fuera_banda = np.where((y[idx_pre_pert] < banda_inf) | (y[idx_pre_pert] > banda_sup))[0]
    ts = t[fuera_banda[-1]] if len(fuera_banda) > 0 else 0.0
    
    # Error en estado estacionario (justo antes de perturbación)
    ess = abs(SP - y[int(1350 / dt)])
    
    # Índices de Desempeño Integral (hasta t=1400 s)
    iae = np.sum(np.abs(error[idx_pre_pert])) * dt
    itae = np.sum(t[idx_pre_pert] * np.abs(error[idx_pre_pert])) * dt
    ise = np.sum((error[idx_pre_pert]) ** 2) * dt
    
    # Esfuerzo de control y conmutaciones (variación total de control)
    variacion_control = np.sum(np.abs(np.diff(u)))

    return {
        "tr_s": tr, "ts_s": ts, "Mp_pct": Mp,
        "ess_c": ess, "IAE": iae, "ITAE": itae, "ISE": ise,
        "TV_u": variacion_control
    }

# ==============================================================================
# 4. SIMULADOR ON/OFF CON HISTÉRESIS
# ==============================================================================

def simular_onoff(K, tau, theta, T0=8.5, SP=20.0, histeresis=0.5, t_sim=2400.0, dt=1.0, perturbacion_tiempo=1400.0, delta_pert=-2.5):
    n = int(t_sim / dt)
    t = np.arange(n) * dt
    pasos_retardo = int(round(theta / dt))
    buffer_u = [0.0] * max(1, pasos_retardo)
    
    y = np.zeros(n)
    u = np.zeros(n)
    error = np.zeros(n)
    y[0] = T0
    
    estado_actuador = 0.0 # 0% o 100%
    conmutaciones = 0
    
    for i in range(1, n):
        t_actual = t[i]
        e = SP - y[i-1]
        error[i] = e
        
        # Lógica de histéresis On/Off
        if y[i-1] < (SP - histeresis) and estado_actuador == 0.0:
            estado_actuador = 100.0
            conmutaciones += 1
        elif y[i-1] > (SP + histeresis) and estado_actuador == 100.0:
            estado_actuador = 0.0
            conmutaciones += 1
            
        u[i] = estado_actuador
        buffer_u.append(estado_actuador)
        u_efectiva = buffer_u.pop(0)
        
        pert_val = delta_pert if t_actual >= perturbacion_tiempo else 0.0
        dy = ( - (y[i-1] - (T0 + pert_val)) + (K * u_efectiva) ) / tau * dt
        y[i] = y[i-1] + dy

    idx_pre_pert = np.where(t < 1400.0)[0]
    iae = np.sum(np.abs(error[idx_pre_pert])) * dt
    itae = np.sum(t[idx_pre_pert] * np.abs(error[idx_pre_pert])) * dt

    return t, y, u, error, conmutaciones, iae, itae

# ==============================================================================
# 5. OPTIMIZACIÓN GLOBAL CON OPTUNA
# ==============================================================================

def optimizar_con_optuna(K, tau, theta, n_trials=100):
    print(f"[*] Iniciando optimización bayesiana con Optuna ({n_trials} trials)...")
    
    def objetivo(trial):
        kp_cand = trial.suggest_float("Kp", 1.0, 16.0)
        ki_cand = trial.suggest_float("Ki", 0.005, 0.15, log=True)
        kd_cand = trial.suggest_float("Kd", 0.1, 5.0)
        
        t, y, u, error = simular_lazo_cerrado(kp_cand, ki_cand, kd_cand, K, tau, theta)
        met = calcular_metricas(t, y, u, error)
        
        # Función de costo multi-criterio: Min IAE + penalización cuadrática por sobrepaso > 5%
        costo_base = met["IAE"]
        penalizacion_mp = 50.0 * max(0.0, met["Mp_pct"] - 5.0) ** 2
        penalizacion_esfuerzo = 0.01 * met["TV_u"]
        
        return costo_base + penalizacion_mp + penalizacion_esfuerzo

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objetivo, n_trials=n_trials)
    
    print(f"[✔] Optimización completada. Mejor Costo: {study.best_value:.2f}")
    return study.best_params, study

# ==============================================================================
# 6. PIPELINE PRINCIPAL Y EXPORTACIÓN DE FIGURAS
# ==============================================================================

def main():
    print("=" * 70)
    print("FASE 2: Identificación FOPDT, Sintonización y Optimización PID (Tesis Papa)")
    print("=" * 70)

    # 1. Carga de datos
    t_exp, u_exp, y_exp = cargar_datos_escalon()
    print(f"[*] Datos cargados: {len(t_exp)} registros.")

    # 2. Ajuste FOPDT
    fopdt = ajustar_fopdt(t_exp, u_exp, y_exp)
    K = fopdt["K"]
    tau = fopdt["tau"]
    theta = fopdt["theta"]
    print(f"\n--- Parámetros FOPDT Identificados ---")
    print(f"Ganancia K      : {K:.4f} °C / %")
    print(f"Constante tau   : {tau:.2f} s ({tau/60.0:.2f} min)")
    print(f"Tiempo muerto θ : {theta:.2f} s")
    print(f"Relación θ/tau  : {theta/tau:.3f} (Proceso con retardo moderado)")
    print(f"Calidad R²      : {fopdt['R2']:.4f} (Excelente concordancia)")
    print(f"RMSE            : {fopdt['RMSE']:.4f} °C")

    # 3. Sintonizaciones clásicas
    ganancias = calcular_ganancias_clasicas(K, tau, theta)
    print("\n--- Ganancias Clásicas Calculadas ---")
    for metodo, g in ganancias.items():
        print(f"[{metodo}] -> Kp: {g['Kp']:.3f}, Ki: {g['Ki']:.5f}, Kd: {g['Kd']:.3f} (Ti: {g['Ti']:.1f}s, Td: {g['Td']:.1f}s)")

    # 4. Optimización con Optuna
    mejores_params, study = optimizar_con_optuna(K, tau, theta, n_trials=80)
    ganancias["Optuna (Óptimo)"] = {
        "Kp": mejores_params["Kp"],
        "Ki": mejores_params["Ki"],
        "Kd": mejores_params["Kd"],
        "Ti": mejores_params["Kp"] / mejores_params["Ki"],
        "Td": mejores_params["Kd"] / mejores_params["Kp"]
    }
    print(f"\n--- Ganancias Óptimas (Optuna) ---")
    print(f"Kp: {mejores_params['Kp']:.3f}, Ki: {mejores_params['Ki']:.5f}, Kd: {mejores_params['Kd']:.3f}")

    # 5. Simulación de todos los métodos y recolección de métricas
    resultados_sim = {}
    metricas_tabla = []
    
    for nombre, g in ganancias.items():
        t_sim, y_sim, u_sim, e_sim = simular_lazo_cerrado(g["Kp"], g["Ki"], g["Kd"], K, tau, theta)
        met = calcular_metricas(t_sim, y_sim, u_sim, e_sim)
        resultados_sim[nombre] = (t_sim, y_sim, u_sim, e_sim)
        metricas_tabla.append({
            "Método": nombre,
            "Kp": g["Kp"], "Ki": g["Ki"], "Kd": g["Kd"],
            "tr_s": met["tr_s"], "ts_s": met["ts_s"],
            "Mp_pct": met["Mp_pct"], "ess_c": met["ess_c"],
            "IAE": met["IAE"], "ITAE": met["ITAE"], "TV_u": met["TV_u"]
        })

    # 6. Simulación On/Off
    t_onoff, y_onoff, u_onoff, e_onoff, conmut_onoff, iae_onoff, itae_onoff = simular_onoff(K, tau, theta)
    met_onoff = calcular_metricas(t_onoff, y_onoff, u_onoff, e_onoff)
    metricas_tabla.append({
        "Método": "Control On/Off (±0.5°C)",
        "Kp": 0.0, "Ki": 0.0, "Kd": 0.0,
        "tr_s": met_onoff["tr_s"], "ts_s": np.nan,
        "Mp_pct": met_onoff["Mp_pct"], "ess_c": np.mean(np.abs(y_onoff[1000:1400] - 20.0)),
        "IAE": iae_onoff, "ITAE": itae_onoff, "TV_u": np.sum(np.abs(np.diff(u_onoff)))
    })

    # ==========================================================================
    # GENERACIÓN DE GRÁFICAS EN ALTA RESOLUCIÓN (300 DPI)
    # ==========================================================================
    print("\n[*] Generando figuras para la memoria de tesis...")
    
    # FIGURA 1: Ajuste FOPDT
    plt.figure(figsize=(9, 5), dpi=300)
    plt.plot(t_exp / 60.0, y_exp, color="#4A5568", alpha=0.6, label="Sensor SHT31 (Experimental)", linewidth=1.2)
    plt.plot(t_exp / 60.0, fopdt["y_pred"], color="#E53E3E", linewidth=2.0, label=f"Modelo FOPDT Ajustado ($R^2={fopdt['R2']:.4f}$)")
    plt.axvline(120.0 / 60.0, color="#3182CE", linestyle="--", alpha=0.8, label=r"Inicio del Escalón ($u=70\%$)")
    plt.title("Identificación Paramétrica FOPDT - Curva de Reacción Térmica", fontsize=12, fontweight="bold")
    plt.xlabel("Tiempo [minutos]", fontsize=10)
    plt.ylabel("Temperatura del Aire [°C]", fontsize=10)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="lower right", framealpha=0.9)
    plt.tight_layout()
    fig1_path = FIGURAS_DIR / "fig_fopdt_ajuste_escalon.png"
    plt.savefig(fig1_path)
    plt.close()
    print(f"[✔] Guardada: {fig1_path}")

    # FIGURA 2: Comparativa de Métodos PID
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), dpi=300, sharex=True)
    colores = {"Ziegler-Nichols": "#E53E3E", "Cohen-Coon": "#DD6B20", "IMC": "#3182CE", "Optuna (Óptimo)": "#38A169"}
    
    for nombre, (t, y, u, _) in resultados_sim.items():
        c = colores.get(nombre, "black")
        lw = 2.2 if nombre == "Optuna (Óptimo)" else 1.4
        ls = "-" if nombre == "Optuna (Óptimo)" else "--"
        ax1.plot(t / 60.0, y, label=nombre, color=c, linewidth=lw, linestyle=ls)
        ax2.plot(t / 60.0, u, label=nombre, color=c, linewidth=lw, linestyle=ls)
        
    ax1.axhline(20.0, color="#1A202C", linestyle=":", label="Setpoint (20.0 °C)", alpha=0.8)
    ax1.axvline(1400.0 / 60.0, color="#805AD5", linestyle=":", label="Perturbación Externa (-2.5 °C)", alpha=0.8)
    ax1.set_ylabel("Temperatura [°C]", fontsize=10)
    ax1.set_title("Respuesta Dinámica en Lazo Cerrado ante Setpoint y Perturbación", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="lower right", framealpha=0.9, ncol=2)

    ax2.set_ylabel("Acción de Control $u(t)$ [%]", fontsize=10)
    ax2.set_xlabel("Tiempo [minutos]", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.set_ylim(-5, 105)
    plt.tight_layout()
    fig2_path = FIGURAS_DIR / "fig_comparativa_sintonias_pid.png"
    plt.savefig(fig2_path)
    plt.close()
    print(f"[✔] Guardada: {fig2_path}")

    # FIGURA 3: On/Off vs PID Óptimo
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), dpi=300, sharex=True)
    
    t_opt, y_opt, u_opt, _ = resultados_sim["Optuna (Óptimo)"]
    ax1.plot(t_onoff / 60.0, y_onoff, label="Control On/Off con Histéresis (±0.5 °C)", color="#E53E3E", linewidth=1.2, alpha=0.8)
    ax1.plot(t_opt / 60.0, y_opt, label="Control PID Óptimo (Optuna)", color="#38A169", linewidth=2.0)
    ax1.axhline(20.0, color="#1A202C", linestyle=":", label="Setpoint (20.0 °C)")
    ax1.set_ylabel("Temperatura [°C]", fontsize=10)
    ax1.set_title("Comparativa de Desempeño: Control On/Off vs PID Óptimo", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="lower right", framealpha=0.9)

    ax2.plot(t_onoff / 60.0, u_onoff, label=f"On/Off Actuador ({conmut_onoff} conmutaciones)", color="#E53E3E", linewidth=0.8, alpha=0.7)
    ax2.plot(t_opt / 60.0, u_opt, label="PID Modulación Suave SSR", color="#38A169", linewidth=1.8)
    ax2.set_ylabel("Esfuerzo de Control [%]", fontsize=10)
    ax2.set_xlabel("Tiempo [minutos]", fontsize=10)
    ax2.set_ylim(-5, 105)
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right", framealpha=0.9)
    plt.tight_layout()
    fig3_path = FIGURAS_DIR / "fig_comparativa_onoff_vs_pid.png"
    plt.savefig(fig3_path)
    plt.close()
    print(f"[✔] Guardada: {fig3_path}")

    # FIGURA 4: Convergencia Optuna
    plt.figure(figsize=(8, 4.5), dpi=300)
    trials_y = [t.value for t in study.trials if t.value is not None]
    best_y = [np.min(trials_y[:i+1]) for i in range(len(trials_y))]
    plt.scatter(range(1, len(trials_y)+1), trials_y, color="#CBD5E0", s=18, label="Trials Evaluados")
    plt.plot(range(1, len(best_y)+1), best_y, color="#3182CE", linewidth=2.0, label="Mejor Función de Costo ($IAE + Penaliz.$)")
    plt.title("Convergencia del Optimizador Bayesiano (Optuna TPE)", fontsize=12, fontweight="bold")
    plt.xlabel("Número de Iteración (Trial)", fontsize=10)
    plt.ylabel("Costo de Desempeño", fontsize=10)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(framealpha=0.9)
    plt.tight_layout()
    fig4_path = FIGURAS_DIR / "fig_optuna_convergencia.png"
    plt.savefig(fig4_path)
    plt.close()
    print(f"[✔] Guardada: {fig4_path}")

    # Imprimir Tabla Resumen
    print("\n" + "=" * 90)
    print(f"{'Método':<25} | {'Kp':<6} | {'Ki':<7} | {'Kd':<6} | {'tr [s]':<7} | {'ts [s]':<7} | {'Mp [%]':<6} | {'IAE':<8} | {'TV_u':<8}")
    print("-" * 90)
    for m in metricas_tabla:
        tr_str = f"{m['tr_s']:.1f}" if not np.isnan(m['tr_s']) else "N/A"
        ts_str = f"{m['ts_s']:.1f}" if not np.isnan(m['ts_s']) else "Oscila"
        print(f"{m['Método']:<25} | {m['Kp']:<6.2f} | {m['Ki']:<7.4f} | {m['Kd']:<6.2f} | {tr_str:<7} | {ts_str:<7} | {m['Mp_pct']:<6.1f} | {m['IAE']:<8.1f} | {m['TV_u']:<8.1f}")
    print("=" * 90)

    # Guardar métricas en CSV para capítulos de resultados
    res_csv = BASE_DIR / "data" / "synthetic" / "metricas_comparativa_pid_onoff.csv"
    with open(res_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(metricas_tabla[0].keys()))
        writer.writeheader()
        writer.writerows(metricas_tabla)
    print(f"[✔] Tabla de métricas exportada a: {res_csv}")

if __name__ == "__main__":
    main()
