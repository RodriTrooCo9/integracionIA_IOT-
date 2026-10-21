"""
Script para inicializar y poblar los ensayos experimentales E1 a E8 en la base relacional SQLite.
Tesis: Sistema Integrado IoT-PID-IA en Invernadero de Papa (La Paz, Bolivia).
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "invernadero_relacional.db"

ENSAYOS = [
    ('E1', 'Validación Metrológica de Sensores y Repetibilidad', 'Sensor SHT31 vs BME280 a 3600 msnm', '2026-03-01 08:00:00', '2026-03-03 18:00:00', 58.0, 
     'Verificación de calibración e histeresis en condiciones de baja presión barométrica (67.5 kPa).', 
     json.dumps({'rmse_temperatura_c': 0.18, 'rmse_humedad_pct': 1.42, 'deriva_diaria_c': 0.04, 'repetibilidad_pct': 99.4})),
    
    ('E2', 'Identificación de la Dinámica Térmica FOPDT', 'Escalón de Potencia SSR al 60% a Lazo Abierto', '2026-03-05 10:00:00', '2026-03-05 14:00:00', 4.0,
     'Ajuste por mínimos cuadrados no lineales del modelo térmico de primer orden con retardo.',
     json.dumps({'k_ganancia_estatica': 0.1639, 'tau_constante_s': 242.96, 'theta_retardo_s': 33.33, 'r2_score': 0.9841})),
    
    ('E3', 'Sintonización Comparativa de Control Térmico', 'Ziegler-Nichols vs Cohen-Coon vs Optuna Bayesian', '2026-03-08 00:00:00', '2026-03-10 23:59:00', 72.0,
     'Comparación cuantitativa de criterios de error integral (ITAE, IAE) y estabilidad ante sobreimpulso.',
     json.dumps({'itae_zn': 4520.1, 'itae_cohen_coon': 3410.5, 'itae_optuna': 2325.8, 'sobreimpulso_pct': 4.2, 'tiempo_asentamiento_s': 285})),
    
    ('E4', 'Control Psicrométrico Desacoplado de Humedad y VPD', 'Extracción forzada PWM + Nebulización ultrasónica', '2026-03-12 06:00:00', '2026-03-14 18:00:00', 60.0,
     'Mantenimiento de VPD en zona segura (0.8 - 1.2 kPa) para evitar esporulación fúngica.',
     json.dumps({'tiempo_rango_optimo_vpd_pct': 92.4, 'consumo_agua_l_dia': 4.8, 'eventos_rocio_evitados': 14})),
    
    ('E5', 'Detección Fitosanitaria de Patologías Foliares', 'YOLO11n en Follaje de Papa (Tizón Tardío y Temprano)', '2026-03-16 09:00:00', '2026-03-17 17:00:00', 32.0,
     'Evaluación de precisión, recall y latencia en cámara fija y subidas fotográficas de alta resolución.',
     json.dumps({'map50': 0.884, 'precision': 0.891, 'recall': 0.862, 'f1_score': 0.876, 'latencia_ms': 78.4})),
    
    ('E6', 'Inspección de Trampas Cromáticas Amarillas con SAHI', 'YOLO11n + SAHI (Slicing 320x320 con overlap 0.25)', '2026-03-19 08:00:00', '2026-03-20 18:00:00', 34.0,
     'Conteo y clasificación de insectos de tamaño menor a 30 px (pulgón alado y mosca minadora).',
     json.dumps({'incremento_recall_sahi_pct': 39.7, 'falsos_negativos_reducidos_pct': 64.2, 'latencia_total_ms': 142.1})),
    
    ('E7', 'Predicción de Riesgo Bio-Climático y Explicabilidad SHAP', 'XGBoost Calibrado vs BlightManager Tradicional', '2026-03-22 00:00:00', '2026-03-26 23:59:00', 120.0,
     'Validación temporal con TimeSeriesSplit (60/20/20) y cálculo de valores SHAP para interpretabilidad agronómica.',
     json.dumps({'brier_score_xgboost': 0.1878, 'brier_score_blightmanager': 0.3142, 'reduccion_brier_pct': 40.2, 'top1_feature_shap': 'horas_hr_gt_90'})),
    
    ('E8', 'Ensayo Integrado 24/7 y Resiliencia ante Helada Altiplánica', 'Sistema Completo IoT-PID-IA en Operación Continua', '2026-03-28 00:00:00', '2026-04-04 23:59:00', 192.0,
     'Supervisión ininterrumpida frente a heladas con temperatura exterior de -3.2 °C y ráfagas de viento.',
     json.dumps({'temp_ext_minima_c': -3.2, 'temp_int_minima_c': 14.1, 'danos_foliares_pct': 0.0, 'disponibilidad_sistema_pct': 99.8, 'alertas_telegram_enviadas': 6}))
]

def poblar_ensayos():
    if not DB_PATH.exists():
        print(f"Error: No existe la base de datos en {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executemany('''
        INSERT OR REPLACE INTO experimentos_ensayos 
        (codigo_experimento, nombre_ensayo, tratamiento, fecha_inicio, fecha_fin, duracion_horas, observaciones, metricas_resumen_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ENSAYOS)
    conn.commit()
    print(f"✅ Se han registrado {c.rowcount} ensayos experimentales en SQLite.")
    conn.close()
    return True

if __name__ == "__main__":
    poblar_ensayos()
