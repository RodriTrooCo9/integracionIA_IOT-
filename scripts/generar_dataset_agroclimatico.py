#!/usr/bin/env python3
"""
Simulador de Datos Agroclimáticos y Eventos Fitopatológicos para Invernadero de Papa
Ubicación simulada: Altiplano de La Paz, Bolivia (~3600 msnm)

Genera una serie temporal horaria realista de 90 días (2160 horas) que modela:
1. Microclima interno del invernadero (temperatura, humedad relativa, radiación, suelo).
2. Variables bioclimáticas derivadas (VPD, punto de rocío, horas continuas de hoja húmeda).
3. Fenología y microclima propicio para Phytophthora infestans (Tizón tardío) y plagas.
4. Señales de visión artificial periódica (severidad foliar YOLO y conteo en trampas SAHI).

NOTA DE INTEGRIDAD ACADÉMICA:
Este dataset es 100% sintético pero derivado de ecuaciones biofísicas consolidadas
(Tetens, Wallin 1962, SimCast/Fry 1983) para desarrollo y validación algorítmica previa a campo.
"""

import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

def calcular_vpd_y_rocio(temp_c: np.ndarray, rh_pct: np.ndarray):
    """
    Calcula la Presión de Vapor de Saturación (es), Presión de Vapor Actual (ea),
    Déficit de Presión de Vapor (VPD en kPa) y Temperatura de Punto de Rocío (Tdew en °C)
    mediante las ecuaciones de Tetens y Magnus-Tetens.
    """
    a = 17.27
    b = 237.3
    # Presión de saturación en kPa
    es = 0.61078 * np.exp((a * temp_c) / (temp_c + b))
    # Presión actual en kPa
    ea = es * (np.clip(rh_pct, 1.0, 100.0) / 100.0)
    # VPD en kPa
    vpd = np.maximum(0.0, es - ea)
    
    # Punto de rocío (Magnus-Tetens)
    alpha = ((a * temp_c) / (b + temp_c)) + np.log(np.clip(rh_pct, 1.0, 100.0) / 100.0)
    t_dew = (b * alpha) / (a - alpha)
    
    return es, ea, vpd, t_dew

def generar_dataset_invernadero(dias: int = 90, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    n_horas = dias * 24
    start_date = datetime(2026, 11, 1, 0, 0, 0) # Campaña agrícola de verano andino
    fechas = [start_date + timedelta(hours=i) for i in range(n_horas)]
    
    # 1. Ciclo Diario y Estacional de Temperatura Exterior (La Paz, 3600 msnm)
    # Oscilación térmica típica: Noches frías (2°C a 7°C), tardes templadas (16°C a 20°C)
    horas_dia = np.array([f.hour for f in fechas])
    dias_transcurridos = np.array([i / 24.0 for i in range(n_horas)])
    
    # Variación sinodal diurna: pico a las 14:00 (hora 14), valle a las 05:00 (hora 5)
    fase_diurna = (horas_dia - 14) * (2 * np.pi / 24.0)
    t_ext_base = 11.0 + 7.5 * np.cos(fase_diurna)
    
    # Ruido meteorológico y frentes fríos periódicos ("surazos" / bajas de presión cada 12-15 días)
    frentes_frios = -3.5 * np.maximum(0.0, np.sin(2 * np.pi * dias_transcurridos / 14.0) - 0.6)
    ruido_t = np.random.normal(0, 1.2, n_horas)
    temp_exterior = t_ext_base + frentes_frios + ruido_t
    
    # Radiación solar diurna (W/m2) en plano horizontal
    # Pico cenital andino (muy alto ~850 W/m2 al mediodía con cielo despejado)
    rad_solar = np.zeros(n_horas)
    mascara_dia = (horas_dia >= 6) & (horas_dia <= 18)
    rad_solar[mascara_dia] = 850.0 * np.sin((horas_dia[mascara_dia] - 6) * np.pi / 12.0)
    # Nubosidad estocástica
    nubosidad = np.clip(np.random.normal(0.25, 0.2, n_horas), 0.0, 0.85)
    rad_solar = rad_solar * (1.0 - nubosidad)
    rad_solar = np.maximum(0.0, rad_solar)
    
    # 2. Temperatura Interior Invernadero (con PID activo y efecto invernadero pasivo)
    # Calefacción nocturna evita caídas bajo 12°C. Invernadero pasivo gana 4-6°C con radiación.
    ganancia_solar = rad_solar * 0.008
    temp_interior = np.zeros(n_horas)
    hum_interior = np.zeros(n_horas)
    
    # Simulación acoplada hora a hora
    t_prev = 14.0
    for i in range(n_horas):
        # Térmico: mezcla de inercia, exterior, radiación y calefactor PID
        calefactor_activo = 1.0 if t_prev < 15.0 else 0.0
        potencia_calor = calefactor_activo * 3.5 * (15.5 - t_prev) if t_prev < 15.5 else 0.0
        
        t_in = 0.75 * t_prev + 0.25 * (temp_exterior[i] + 4.0 + ganancia_solar[i] + potencia_calor)
        t_in += np.random.normal(0, 0.3)
        temp_interior[i] = t_in
        t_prev = t_in
        
        # Humedad relativa: anticorrelacionada con temperatura + picos de riego y noches
        rh_base = 72.0 - 1.6 * (t_in - 14.0) + (14.0 if (horas_dia[i] >= 22 or horas_dia[i] <= 6) else -8.0)
        
        # Eventos meteorológicos de temporales / lluvias prolongadas (temporada de lluvias en La Paz: dic-feb)
        # Ocurren 4 episodios durante los 90 días: días 18-22, 38-41, 58-62, 75-78
        dia_actual = dias_transcurridos[i]
        es_temporal = (18 <= dia_actual <= 22) or (38 <= dia_actual <= 41) or (58 <= dia_actual <= 62) or (75 <= dia_actual <= 78)
        
        if es_temporal:
            # Durante el temporal, niebla andina y lluvia continua: humedad interior 91% a 98%
            rh_base = 94.5 + 2.5 * np.sin(horas_dia[i] * np.pi / 12.0)
            
        rh_in = np.clip(rh_base + np.random.normal(0, 1.8), 38.0, 99.0)
        hum_interior[i] = rh_in
        
    # Variables de suelo
    temp_suelo = 0.9 * pd.Series(temp_interior).rolling(12, min_periods=1).mean().values + np.random.normal(0, 0.2, n_horas)
    hum_suelo = 28.0 + 5.0 * np.sin(2 * np.pi * dias_transcurridos / 7.0) + np.random.normal(0, 0.8, n_horas) # Riego semanal
    
    # 3. Psicrometría y Hoja Húmeda
    _, _, vpd_kpa, t_dew = calcular_vpd_y_rocio(temp_interior, hum_interior)
    
    # Horas de hoja húmeda continua (LWH): definida por RH >= 90% o T_in - T_dew <= 0.6°C
    hoja_humeda_inst = ((hum_interior >= 90.0) | ((temp_interior - t_dew) <= 0.6)).astype(int)
    
    lwh_continuo = np.zeros(n_horas)
    contador_lwh = 0
    for i in range(n_horas):
        if hoja_humeda_inst[i] == 1:
            contador_lwh += 1
        else:
            contador_lwh = 0
        lwh_continuo[i] = contador_lwh
        
    # Grados-hora acumulados sobre base 7°C (desarrollo vegetal de Solanum tuberosum)
    grados_hora = np.maximum(0.0, temp_interior - 7.0)
    
    # 4. Modelo Epidemiológico de Tizón Tardío (Phytophthora infestans) según Wallin (1962)
    # Severity Values (SV) calculados con temperatura media durante el período húmedo:
    # Si LWH >= 10h y Temp entre 12°C y 22°C (óptimo de germinación de zoosporas de P. infestans)
    sv_horario = np.zeros(n_horas)
    for i in range(n_horas):
        if lwh_continuo[i] >= 10:
            temp_lwh = np.mean(temp_interior[max(0, i-int(lwh_continuo[i])+1):i+1])
            if 10.0 <= temp_lwh <= 15.0:
                if lwh_continuo[i] >= 18:
                    sv_horario[i] = 4
                elif lwh_continuo[i] >= 15:
                    sv_horario[i] = 3
                elif lwh_continuo[i] >= 12:
                    sv_horario[i] = 2
                else:
                    sv_horario[i] = 1
            elif 15.0 < temp_lwh <= 25.0:
                if lwh_continuo[i] >= 16:
                    sv_horario[i] = 4
                elif lwh_continuo[i] >= 13:
                    sv_horario[i] = 3
                elif lwh_continuo[i] >= 10:
                    sv_horario[i] = 2
                else:
                    sv_horario[i] = 1
                    
    # Acumulación de valores de severidad en ventana móvil de 7 días (168 horas)
    blight_units_7d = pd.Series(sv_horario).rolling(168, min_periods=1).sum().values
    
    # Etiqueta de riesgo fitopatológico epidemiológico (Ground Truth) según Wallin (1962):
    # - < 9 BU: Riesgo Bajo
    # - 9 a 13 BU: Riesgo Moderado
    # - >= 14 BU: Riesgo Alto / Crítico (brote inminente de Phytophthora infestans)
    prob_infeccion_real = np.clip((blight_units_7d - 8.0) / 10.0, 0.0, 1.0)
    riesgo_infeccion_binario = (blight_units_7d >= 14.0).astype(int)
    
    # 5. Señales de Visión Periódica (Cámara estéreo/cenital e inspección de trampas)
    # Se muestrean cada 6 horas y se interpolan con persistencia
    vision_severidad_foliar = np.zeros(n_horas) # Daño foliar visible (%)
    vision_conteo_trampa = np.zeros(n_horas)    # Insectos en trampas adhesivas (unidades)
    
    # Simulación de propagación de tizón si hay eventos de infección sostenida
    danio_acumulado = 0.0
    plagas_acumuladas = 3.0
    for i in range(n_horas):
        if riesgo_infeccion_binario[i] == 1:
            danio_acumulado += 0.04 # Progresión de necrosis si el microclima favorece
        else:
            danio_acumulado = max(0.0, danio_acumulado - 0.005) # Manejo / poda sanitaria
        
        # Plagas aumentan más en períodos secos y cálidos (VPD > 1.0 kPa)
        if vpd_kpa[i] > 0.9 and temp_interior[i] > 18.0:
            plagas_acumuladas += 0.03
        
        # Muestreo de visión con ruido de detección de YOLO11n y SAHI
        if i % 6 == 0:
            ruido_det = np.random.normal(0, 0.5)
            val_foliar = max(0.0, min(100.0, danio_acumulado + ruido_det))
            val_trampa = max(0, int(round(plagas_acumuladas + np.random.normal(0, 1.2))))
        
        vision_severidad_foliar[i] = val_foliar
        vision_conteo_trampa[i] = val_trampa

    df = pd.DataFrame({
        'timestamp': fechas,
        'temp_exterior_c': np.round(temp_exterior, 2),
        'radiacion_solar_wm2': np.round(rad_solar, 1),
        'temp_interior_c': np.round(temp_interior, 2),
        'hum_interior_pct': np.round(hum_interior, 2),
        'temp_suelo_c': np.round(temp_suelo, 2),
        'hum_suelo_pct': np.round(hum_suelo, 2),
        'vpd_kpa': np.round(vpd_kpa, 3),
        'punto_rocio_c': np.round(t_dew, 2),
        'hoja_humeda_bin': hoja_humeda_inst,
        'lwh_continuo_horas': lwh_continuo,
        'grados_hora': np.round(grados_hora, 2),
        'blight_units_7d': np.round(blight_units_7d, 2),
        'vision_severidad_foliar_pct': np.round(vision_severidad_foliar, 2),
        'vision_conteo_trampa_amarilla': vision_conteo_trampa.astype(int),
        'riesgo_infeccion_gt': riesgo_infeccion_binario
    })
    
    return df

def main():
    output_dir = Path("/home/rodrigo/Desktop/IOTtesis/data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "dataset_agroclimatico_invernadero.csv"
    
    print("=" * 70)
    print("Generando dataset agroclimático sintético (90 días, 2160 horas)...")
    df = generar_dataset_invernadero(dias=90, seed=42)
    df.to_csv(csv_path, index=False)
    
    print(f"✔ Dataset guardado con éxito en: {csv_path}")
    print(f"  Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas")
    print(f"  Rango de fechas: {df['timestamp'].min()} a {df['timestamp'].max()}")
    print(f"  Distribución de clases (riesgo_infeccion_gt):")
    print(df['riesgo_infeccion_gt'].value_counts(normalize=True).round(3))
    print(f"  VPD medio: {df['vpd_kpa'].mean():.3f} kPa (min: {df['vpd_kpa'].min():.3f}, max: {df['vpd_kpa'].max():.3f})")
    print(f"  Máximo LWH continuo: {df['lwh_continuo_horas'].max()} horas")
    print("=" * 70)

if __name__ == "__main__":
    main()
