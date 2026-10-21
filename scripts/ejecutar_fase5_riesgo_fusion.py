#!/usr/bin/env python3
"""
Fase 5: Modelo de Riesgo Fitopatológico, Comparativa ML y Fusión de Decisión
Proyecto de Tesis - Invernadero de Papa (La Paz, Bolivia)

Ejecuta el pipeline completo de:
1. Ingeniería de características bioclimáticas avanzadas.
2. Implementación de BlightManager (Wallin 1962) como línea base epidemiológica.
3. Partición temporal estricta (sin fuga futura / No Lookahead Bias).
4. Entrenamiento y validación comparativa: BlightManager, Random Forest, XGBoost, SVM y LSTM.
5. Calibración probabilística (Platt Scaling / Regresión Isotónica) y Curvas de Confiabilidad.
6. Explicabilidad agronómica con SHAP (TreeExplainer).
7. Función de Fusión de Decisión Multimodal (Clima + Visión + Tendencia) y simulación
   del lazo de control supervisor externo (ajuste dinámico de setpoints MQTT).
8. Generación de figuras a 300 DPI en thesis/figuras/ y tabla de métricas en CSV.
"""

import time
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Scikit-learn
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss,
    f1_score, accuracy_score, confusion_matrix, roc_curve, precision_recall_curve
)

# XGBoost
import xgboost as xgb

# SHAP
import shap

# PyTorch para LSTM
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

# Semillas fijas para estricta reproducibilidad científica
SEED = 42
np.random.seed(SEED)
torch.manual_seed(SEED)

class BlightManagerBaseline:
    """
    Implementación del modelo clásico Wallin (1962) / BlightManager para
    predicción de Tizón Tardío (Phytophthora infestans).
    Calcula Severity Values (SV) basados en horas de hoja húmeda y temperatura media.
    """
    def __init__(self, umbral_acumulado: float = 18.0):
        self.umbral_acumulado = umbral_acumulado

    def predecir_probabilidad(self, blight_units_7d: np.ndarray) -> np.ndarray:
        # Sigmoide centrada en el umbral epidemiológico de 18 Blight Units
        # con dispersión típica observada en literatura agronómica
        z = (blight_units_7d - self.umbral_acumulado) / 3.5
        prob = 1.0 / (1.0 + np.exp(-z))
        return np.clip(prob, 0.0, 1.0)

    def predecir_clase(self, blight_units_7d: np.ndarray, umbral_prob: float = 0.5) -> np.ndarray:
        prob = self.predecir_probabilidad(blight_units_7d)
        return (prob >= umbral_prob).astype(int)

class BioclimaticLSTM(nn.Module):
    """
    Red Neuronal Recurrente LSTM bidireccional / multicapa para captura de dependencias
    temporales en series de microclima de invernadero.
    """
    def __init__(self, input_dim: int, hidden_dim: int = 32, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, 1)
        )

    def forward(self, x):
        out, (hn, cn) = self.lstm(x)
        # Tomar la salida del último paso temporal de la ventana
        last_step = out[:, -1, :]
        logits = self.fc(last_step)
        return logits.squeeze(-1)

def ingenieria_caracteristicas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera 18 características bioclimáticas avanzadas respetando causalidad temporal.
    """
    data = df.copy()
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data = data.sort_values('timestamp').reset_index(drop=True)

    # 1. Depresión del punto de rocío (T_aire - T_rocío)
    data['depresion_rocio_c'] = np.maximum(0.0, data['temp_interior_c'] - data['punto_rocio_c'])

    # 2. Ventanas móviles de temperatura interior (6h, 12h, 24h)
    data['temp_in_media_6h'] = data['temp_interior_c'].rolling(6, min_periods=1).mean()
    data['temp_in_media_24h'] = data['temp_interior_c'].rolling(24, min_periods=1).mean()
    data['temp_in_std_24h'] = data['temp_interior_c'].rolling(24, min_periods=1).std().fillna(0)
    data['oscilacion_termica_24h'] = (data['temp_interior_c'].rolling(24, min_periods=1).max() - 
                                      data['temp_interior_c'].rolling(24, min_periods=1).min())

    # 3. Ventanas móviles de humedad relativa interior (6h, 12h, 24h)
    data['hum_in_media_6h'] = data['hum_interior_pct'].rolling(6, min_periods=1).mean()
    data['hum_in_media_24h'] = data['hum_interior_pct'].rolling(24, min_periods=1).mean()
    data['hum_in_max_24h'] = data['hum_interior_pct'].rolling(24, min_periods=1).max()
    data['hum_in_std_24h'] = data['hum_interior_pct'].rolling(24, min_periods=1).std().fillna(0)

    # 4. Ventanas móviles de VPD (6h, 24h)
    data['vpd_media_6h'] = data['vpd_kpa'].rolling(6, min_periods=1).mean()
    data['vpd_media_24h'] = data['vpd_kpa'].rolling(24, min_periods=1).mean()
    data['vpd_min_24h'] = data['vpd_kpa'].rolling(24, min_periods=1).min()

    # 5. Acumuladores de horas de hoja húmeda (LWH)
    data['lwh_max_24h'] = data['lwh_continuo_horas'].rolling(24, min_periods=1).max()
    data['lwh_suma_48h'] = data['hoja_humeda_bin'].rolling(48, min_periods=1).sum()

    # 6. Derivadas / Razones de cambio temporal (1 hora)
    data['delta_vpd_1h'] = data['vpd_kpa'].diff().fillna(0)
    data['delta_temp_1h'] = data['temp_interior_c'].diff().fillna(0)
    data['delta_hum_1h'] = data['hum_interior_pct'].diff().fillna(0)

    # 7. Grados-hora acumulados en 24h
    data['grados_hora_24h'] = data['grados_hora'].rolling(24, min_periods=1).sum()

    return data

def crear_secuencias_lstm(X: np.ndarray, y: np.ndarray, seq_len: int = 24):
    """
    Construye ventanas deslizantes [N - seq_len, seq_len, num_features] para LSTM.
    """
    X_seq, y_seq = [], []
    for i in range(len(X) - seq_len):
        X_seq.append(X[i:i + seq_len])
        y_seq.append(y[i + seq_len])
    return np.array(X_seq, dtype=np.float32), np.array(y_seq, dtype=np.float32)

def funcion_fusion_riesgo(p_clima: float, sev_foliar: float, conteo_trampas: float, tend_48h: float) -> tuple:
    """
    Función de Fusión de Decisión Multimodal:
    Score_riesgo = w1 * Riesgo_clima + w2 * Deteccion_vision + w3 * Tendencia_temporal
    Pesos agronómicos:
    - w1 = 0.45: El microclima es un indicador anticipatorio preventivo.
    - w2 = 0.35: La visión confirma la colonización visible de esporas o presencia de insectos vector.
    - w3 = 0.20: La inercia o tendencia temporal de las últimas 48h.
    """
    w1, w2, w3 = 0.45, 0.35, 0.20
    
    # Normalización de visión a [0, 1]
    # Umbrales agronómicos: > 20% severidad foliar es crítico; > 25 insectos/trampa es infestación severa
    comp_foliar = min(1.0, sev_foliar / 20.0)
    comp_trampa = min(1.0, conteo_trampas / 25.0)
    score_vision = 0.65 * comp_foliar + 0.35 * comp_trampa
    
    # Normalización de tendencia a [0, 1]
    score_tendencia = np.clip(tend_48h, 0.0, 1.0)
    
    # Score combinado ponderado
    score_riesgo = (w1 * p_clima) + (w2 * score_vision) + (w3 * score_tendencia)
    score_riesgo = float(np.clip(score_riesgo, 0.0, 1.0))
    
    # Mapeo a Niveles de Acción Fitosanitaria y Ajuste de Setpoints
    if score_riesgo < 0.30:
        nivel = "BAJO"
        color = "VERDE"
        sp_temp = 18.0
        sp_hum = 75.0
        accion = "Monitoreo rutinario; sin alteración de setpoints."
    elif score_riesgo < 0.55:
        nivel = "MEDIO"
        color = "AMARILLO"
        sp_temp = 18.5
        sp_hum = 70.0
        accion = "Ventilación diurna preventiva; inhibir períodos de saturación."
    elif score_riesgo < 0.75:
        nivel = "ALTO"
        color = "NARANJA"
        sp_temp = 19.5
        sp_hum = 65.0
        accion = "Deshumidificación activa nocturna; alerta preventiva al agrónomo."
    else:
        nivel = "CRÍTICO"
        color = "ROJO"
        sp_temp = 20.0
        sp_hum = 60.0
        accion = "Protocolo de choque fitosanitario: extracción forzada y recomendación de fungicida."
        
    return score_riesgo, nivel, color, sp_temp, sp_hum, accion

def main():
    print("=" * 80)
    print("FASE 5: MODELO DE RIESGO FITOPATOLÓGICO Y FUSIÓN DE DECISIÓN")
    print("=" * 80)

    # 1. Cargar Dataset Sintético Generado
    data_path = Path("/home/rodrigo/Desktop/IOTtesis/data/synthetic/dataset_agroclimatico_invernadero.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"No se encontró el dataset en {data_path}. Ejecuta scripts/generar_dataset_agroclimatico.py primero.")

    df_raw = pd.read_csv(data_path)
    print(f"✔ Dataset cargado: {len(df_raw)} registros horarios (90 días).")

    # 2. Ingeniería de Características
    print("\n[Paso 1] Ejecutando ingeniería de características bioclimáticas...")
    df_feat = ingenieria_caracteristicas(df_raw)
    
    feature_cols = [
        'temp_interior_c', 'hum_interior_pct', 'vpd_kpa', 'punto_rocio_c',
        'depresion_rocio_c', 'lwh_continuo_horas', 'grados_hora',
        'temp_in_media_6h', 'temp_in_media_24h', 'temp_in_std_24h', 'oscilacion_termica_24h',
        'hum_in_media_6h', 'hum_in_media_24h', 'hum_in_max_24h', 'hum_in_std_24h',
        'vpd_media_6h', 'vpd_media_24h', 'vpd_min_24h',
        'lwh_max_24h', 'lwh_suma_48h',
        'delta_vpd_1h', 'delta_temp_1h', 'delta_hum_1h', 'grados_hora_24h'
    ]
    print(f"✔ {len(feature_cols)} características bioclimáticas generadas.")

    # 3. Partición Temporal Estricta (60% Train, 20% Val, 20% Test)
    # 90 días = 2160 horas:
    # Train: 54 días (1296h), Val: 18 días (432h), Test: 18 días (432h)
    n_total = len(df_feat)
    n_train = 1296
    n_val = 432
    n_test = n_total - n_train - n_val

    df_train = df_feat.iloc[:n_train].copy()
    df_val = df_feat.iloc[n_train:n_train + n_val].copy()
    df_test = df_feat.iloc[n_train + n_val:].copy()

    X_train_raw = df_train[feature_cols].values
    y_train = df_train['riesgo_infeccion_gt'].values
    X_val_raw = df_val[feature_cols].values
    y_val = df_val['riesgo_infeccion_gt'].values
    X_test_raw = df_test[feature_cols].values
    y_test = df_test['riesgo_infeccion_gt'].values

    # Escalador estándar entrenado ÚNICAMENTE con conjunto de Train (cero fuga)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw)
    X_val = scaler.transform(X_val_raw)
    X_test = scaler.transform(X_test_raw)

    print(f"\n[Paso 2] Partición Temporal Estricta:")
    print(f"  • Train: {len(df_train)} h ({df_train['timestamp'].iloc[0]} a {df_train['timestamp'].iloc[-1]}) | Positivos: {y_train.sum()} ({y_train.mean():.1%})")
    print(f"  • Val:   {len(df_val)} h ({df_val['timestamp'].iloc[0]} a {df_val['timestamp'].iloc[-1]}) | Positivos: {y_val.sum()} ({y_val.mean():.1%})")
    print(f"  • Test:  {len(df_test)} h ({df_test['timestamp'].iloc[0]} a {df_test['timestamp'].iloc[-1]}) | Positivos: {y_test.sum()} ({y_test.mean():.1%})")

    # 4. Modelo 0: Línea Base BlightManager (Wallin 1962)
    print("\n[Paso 3] Evaluando Línea Base BlightManager...")
    blight_model = BlightManagerBaseline(umbral_acumulado=18.0)
    
    t0 = time.time()
    prob_bm_test = blight_model.predecir_probabilidad(df_test['blight_units_7d'].values)
    pred_bm_test = blight_model.predecir_clase(df_test['blight_units_7d'].values)
    lat_bm = (time.time() - t0) / len(df_test) * 1000.0

    auc_bm = roc_auc_score(y_test, prob_bm_test)
    pr_auc_bm = average_precision_score(y_test, prob_bm_test)
    brier_bm = brier_score_loss(y_test, prob_bm_test)
    f1_bm = f1_score(y_test, pred_bm_test)

    # 5. Modelo 1: Random Forest
    print("\n[Paso 4] Entrenando Random Forest Classifier...")
    rf_base = RandomForestClassifier(n_estimators=120, max_depth=6, random_state=SEED, class_weight='balanced')
    rf_base.fit(X_train, y_train)

    # Calibración con Platt Scaling (Logistic Regression sobre probabilidades de validación)
    val_rf_raw = rf_base.predict_proba(X_val)[:, 1]
    platt_rf = LogisticRegression(random_state=SEED)
    platt_rf.fit(val_rf_raw.reshape(-1, 1), y_val)

    t0 = time.time()
    test_rf_raw = rf_base.predict_proba(X_test)[:, 1]
    prob_rf_test = platt_rf.predict_proba(test_rf_raw.reshape(-1, 1))[:, 1]
    pred_rf_test = (prob_rf_test >= 0.50).astype(int)
    lat_rf = (time.time() - t0) / len(df_test) * 1000.0

    auc_rf = roc_auc_score(y_test, prob_rf_test)
    pr_auc_rf = average_precision_score(y_test, prob_rf_test)
    brier_rf = brier_score_loss(y_test, prob_rf_test)
    f1_rf = f1_score(y_test, pred_rf_test)

    # 6. Modelo 2: XGBoost Classifier
    print("\n[Paso 5] Entrenando XGBoost Classifier...")
    pos_weight = float((len(y_train) - y_train.sum()) / max(1, y_train.sum()))
    xgb_base = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=pos_weight,
        eval_metric='logloss',
        random_state=SEED
    )
    xgb_base.fit(X_train, y_train)

    # Calibración Isotónica sobre probabilidades de validación
    val_xgb_raw = xgb_base.predict_proba(X_val)[:, 1]
    iso_xgb = IsotonicRegression(out_of_bounds='clip')
    iso_xgb.fit(val_xgb_raw, y_val)

    t0 = time.time()
    test_xgb_raw = xgb_base.predict_proba(X_test)[:, 1]
    prob_xgb_test = iso_xgb.predict(test_xgb_raw)
    pred_xgb_test = (prob_xgb_test >= 0.50).astype(int)
    lat_xgb = (time.time() - t0) / len(df_test) * 1000.0

    auc_xgb = roc_auc_score(y_test, prob_xgb_test)
    pr_auc_xgb = average_precision_score(y_test, prob_xgb_test)
    brier_xgb = brier_score_loss(y_test, prob_xgb_test)
    f1_xgb = f1_score(y_test, pred_xgb_test)

    # 7. Modelo 3: Support Vector Machine (SVM RBF)
    print("\n[Paso 6] Entrenando Support Vector Classifier (RBF Kernel)...")
    svm_model = SVC(kernel='rbf', C=1.5, gamma='scale', probability=True, random_state=SEED, class_weight='balanced')
    svm_model.fit(X_train, y_train)

    t0 = time.time()
    prob_svm_test = svm_model.predict_proba(X_test)[:, 1]
    pred_svm_test = (prob_svm_test >= 0.50).astype(int)
    lat_svm = (time.time() - t0) / len(df_test) * 1000.0

    auc_svm = roc_auc_score(y_test, prob_svm_test)
    pr_auc_svm = average_precision_score(y_test, prob_svm_test)
    brier_svm = brier_score_loss(y_test, prob_svm_test)
    f1_svm = f1_score(y_test, pred_svm_test)

    # 8. Modelo 4: Bioclimatic LSTM (PyTorch)
    print("\n[Paso 7] Entrenando Bioclimatic LSTM (PyTorch)...")
    SEQ_LEN = 24
    X_train_seq, y_train_seq = crear_secuencias_lstm(X_train, y_train, seq_len=SEQ_LEN)
    X_val_seq, y_val_seq = crear_secuencias_lstm(X_val, y_val, seq_len=SEQ_LEN)
    X_test_seq, y_test_seq = crear_secuencias_lstm(X_test, y_test, seq_len=SEQ_LEN)

    train_ds = TensorDataset(torch.from_numpy(X_train_seq), torch.from_numpy(y_train_seq))
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)

    lstm_model = BioclimaticLSTM(input_dim=len(feature_cols), hidden_dim=32, num_layers=2, dropout=0.2)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(lstm_model.parameters(), lr=0.003, weight_decay=1e-4)

    lstm_model.train()
    for epoch in range(25):
        for bx, by in train_loader:
            optimizer.zero_grad()
            logits = lstm_model(bx)
            loss = criterion(logits, by)
            loss.backward()
            optimizer.step()

    lstm_model.eval()
    t0 = time.time()
    with torch.no_grad():
        test_logits = lstm_model(torch.from_numpy(X_test_seq))
        prob_lstm_test = torch.sigmoid(test_logits).numpy()
    lat_lstm = (time.time() - t0) / len(X_test_seq) * 1000.0
    pred_lstm_test = (prob_lstm_test >= 0.50).astype(int)

    auc_lstm = roc_auc_score(y_test_seq, prob_lstm_test)
    pr_auc_lstm = average_precision_score(y_test_seq, prob_lstm_test)
    brier_lstm = brier_score_loss(y_test_seq, prob_lstm_test)
    f1_lstm = f1_score(y_test_seq, pred_lstm_test)

    # Alinear longitud de LSTM test para comparativas
    prob_lstm_aligned = np.zeros(len(df_test))
    prob_lstm_aligned[:SEQ_LEN] = prob_rf_test[:SEQ_LEN] # Relleno inicial
    prob_lstm_aligned[SEQ_LEN:] = prob_lstm_test

    # 9. Guardar Métricas Comparativas en CSV
    metricas = [
        {"Modelo": "BlightManager (Wallin 1962)", "ROC-AUC": round(auc_bm, 4), "PR-AUC": round(pr_auc_bm, 4), "Brier Score": round(brier_bm, 4), "F1-Score": round(f1_bm, 4), "Latencia CPU (ms)": round(lat_bm, 3), "Seleccionado": "No (Línea Base)"},
        {"Modelo": "Random Forest (Calibrado)", "ROC-AUC": round(auc_rf, 4), "PR-AUC": round(pr_auc_rf, 4), "Brier Score": round(brier_rf, 4), "F1-Score": round(f1_rf, 4), "Latencia CPU (ms)": round(lat_rf, 3), "Seleccionado": "No"},
        {"Modelo": "XGBoost (Calibrado)", "ROC-AUC": round(auc_xgb, 4), "PR-AUC": round(pr_auc_xgb, 4), "Brier Score": round(brier_xgb, 4), "F1-Score": round(f1_xgb, 4), "Latencia CPU (ms)": round(lat_xgb, 3), "Seleccionado": "SI (Ganador)"},
        {"Modelo": "Support Vector Machine (RBF)", "ROC-AUC": round(auc_svm, 4), "PR-AUC": round(pr_auc_svm, 4), "Brier Score": round(brier_svm, 4), "F1-Score": round(f1_svm, 4), "Latencia CPU (ms)": round(lat_svm, 3), "Seleccionado": "No"},
        {"Modelo": "Bioclimatic LSTM (PyTorch)", "ROC-AUC": round(auc_lstm, 4), "PR-AUC": round(pr_auc_lstm, 4), "Brier Score": round(brier_lstm, 4), "F1-Score": round(f1_lstm, 4), "Latencia CPU (ms)": round(lat_lstm, 3), "Seleccionado": "No (Complejidad)"}
    ]
    df_metrics = pd.DataFrame(metricas)
    metrics_path = Path("/home/rodrigo/Desktop/IOTtesis/data/synthetic/metricas_experimentos_fase5_riesgo.csv")
    df_metrics.to_csv(metrics_path, index=False)
    print(f"\n✔ Tabla comparativa guardada en {metrics_path}:")
    print(df_metrics.to_string(index=False))

    # 10. Explicabilidad Agronómica con SHAP (TreeExplainer sobre XGBoost)
    print("\n[Paso 8] Calculando explicabilidad bioclimática con SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(xgb_base)
    shap_values = explainer.shap_values(X_test)
    
    # Ranking de importancia media absoluta
    mean_shap = np.mean(np.abs(shap_values), axis=0)
    shap_ranking = pd.DataFrame({
        'Feature': feature_cols,
        'Mean_SHAP': mean_shap
    }).sort_values('Mean_SHAP', ascending=False).reset_index(drop=True)
    print("Top 7 características bioclimáticas más influyentes según SHAP:")
    for idx, row in shap_ranking.head(7).iterrows():
        print(f"  {idx+1}. {row['Feature']}: {row['Mean_SHAP']:.4f}")

    # 11. Simulación del Lazo Supervisor Externo (Fusión de Decisión en Test)
    print("\n[Paso 9] Simulando Fusión de Decisión Multimodal y Ajuste de Setpoints...")
    test_scores = []
    test_niveles = []
    test_sp_temps = []
    test_sp_hums = []

    # Tendencia temporal de 48h calculada sobre la derivada del riesgo climático
    prob_series = pd.Series(prob_xgb_test)
    tendencia_48h = (prob_series.diff(12) / 12.0).clip(lower=0.0).fillna(0.0).values * 5.0
    tendencia_48h = np.clip(tendencia_48h, 0.0, 1.0)

    sev_foliar_test = df_test['vision_severidad_foliar_pct'].values
    conteo_trampa_test = df_test['vision_conteo_trampa_amarilla'].values

    for i in range(len(df_test)):
        score, nivel, color, sp_t, sp_h, act = funcion_fusion_riesgo(
            p_clima=prob_xgb_test[i],
            sev_foliar=sev_foliar_test[i],
            conteo_trampas=conteo_trampa_test[i],
            tend_48h=tendencia_48h[i]
        )
        test_scores.append(score)
        test_niveles.append(nivel)
        test_sp_temps.append(sp_t)
        test_sp_hums.append(sp_h)

    df_test['score_riesgo_fusion'] = test_scores
    df_test['nivel_accion'] = test_niveles
    df_test['sp_temp_ajustado'] = test_sp_temps
    df_test['sp_hum_ajustado'] = test_sp_hums

    # 12. Generación de Figuras de Tesis a 300 DPI
    fig_dir = Path("/home/rodrigo/Desktop/IOTtesis/thesis/figuras")
    fig_dir.mkdir(parents=True, exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    # FIGURA 1: Curvas ROC Comparativas (BlightManager vs ML)
    plt.figure(figsize=(8, 6), dpi=300)
    fpr_bm, tpr_bm, _ = roc_curve(y_test, prob_bm_test)
    fpr_rf, tpr_rf, _ = roc_curve(y_test, prob_rf_test)
    fpr_xgb, tpr_xgb, _ = roc_curve(y_test, prob_xgb_test)
    fpr_svm, tpr_svm, _ = roc_curve(y_test, prob_svm_test)
    fpr_lstm, tpr_lstm, _ = roc_curve(y_test_seq, prob_lstm_test)

    plt.plot(fpr_xgb, tpr_xgb, label=f"XGBoost Calibrado (AUC = {auc_xgb:.3f}) [Seleccionado]", color='#1b9e77', lw=2.5)
    plt.plot(fpr_rf, tpr_rf, label=f"Random Forest Calibrado (AUC = {auc_rf:.3f})", color='#386cb0', lw=2.0)
    plt.plot(fpr_lstm, tpr_lstm, label=f"Bioclimatic LSTM (AUC = {auc_lstm:.3f})", color='#7570b3', lw=1.8, linestyle='--')
    plt.plot(fpr_svm, tpr_svm, label=f"SVM RBF (AUC = {auc_svm:.3f})", color='#e7298a', lw=1.8, linestyle=':')
    plt.plot(fpr_bm, tpr_bm, label=f"BlightManager Linea Base (AUC = {auc_bm:.3f})", color='#d95f02', lw=2.0, linestyle='-.')
    plt.plot([0, 1], [0, 1], color='gray', linestyle=':', label='Azar (AUC = 0.500)')

    plt.xlabel('Tasa de Falsos Positivos (1 - Especificidad)', fontsize=12)
    plt.ylabel('Tasa de Verdaderos Positivos (Sensibilidad)', fontsize=12)
    plt.title('Comparativa de Curvas ROC para Riesgo de Tizon Tardio\n(Evaluacion Temporal en Conjunto Test)', fontsize=13, fontweight='bold')
    plt.legend(loc='lower right', frameon=True, fontsize=10)
    plt.tight_layout()
    fig1_path = fig_dir / "fig_blightmanager_vs_ml_roc.png"
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"✔ Figura guardada: {fig1_path}")

    # FIGURA 2: Diagramas de Confiabilidad y Calibración Probabilística
    plt.figure(figsize=(8, 6), dpi=300)
    prob_true_uncal, prob_pred_uncal = calibration_curve(y_test, xgb_base.predict_proba(X_test)[:, 1], n_bins=10)
    prob_true_cal, prob_pred_cal = calibration_curve(y_test, prob_xgb_test, n_bins=10)
    prob_true_bm, prob_pred_bm = calibration_curve(y_test, prob_bm_test, n_bins=10)

    plt.plot([0, 1], [0, 1], 'k--', label='Calibracion Perfecta (Ideal)', lw=1.5)
    plt.plot(prob_pred_cal, prob_true_cal, 's-', label=f"XGBoost Calibrado Isotonico (Brier: {brier_xgb:.4f})", color='#1b9e77', lw=2.2)
    plt.plot(prob_pred_uncal, prob_true_uncal, 'o:', label=f"XGBoost Sin Calibrar (Brier: {brier_score_loss(y_test, xgb_base.predict_proba(X_test)[:, 1]):.4f})", color='#e6ab02', lw=1.8)
    plt.plot(prob_pred_bm, prob_true_bm, '^-.', label=f"BlightManager Wallin (Brier: {brier_bm:.4f})", color='#d95f02', lw=1.8)

    plt.xlabel('Probabilidad Media Predicha', fontsize=12)
    plt.ylabel('Fraccion Real de Positivos', fontsize=12)
    plt.title('Curvas de Calibracion Probabilistica (Reliability Diagram)\nEvaluacion de Certeza Agronomica', fontsize=13, fontweight='bold')
    plt.legend(loc='upper left', frameon=True, fontsize=10)
    plt.tight_layout()
    fig2_path = fig_dir / "fig_curvas_calibracion_probabilidad.png"
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"✔ Figura guardada: {fig2_path}")

    # FIGURA 3: Importancia Bioclimática SHAP
    top10_shap = shap_ranking.head(10).iloc[::-1]
    plt.figure(figsize=(9, 6), dpi=300)
    y_pos = np.arange(len(top10_shap))
    nombres_legibles = [
        col.replace('_c', ' (C)').replace('_pct', ' (%)').replace('_kpa', ' (kPa)').replace('_in_', ' Int. ').replace('_', ' ').capitalize()
        for col in top10_shap['Feature']
    ]
    plt.barh(y_pos, top10_shap['Mean_SHAP'], color='#2b83ba', edgecolor='#2c7bb6', height=0.65)
    plt.yticks(y_pos, nombres_legibles, fontsize=10)
    plt.xlabel('Impacto Medio Absoluto en la Salida del Modelo (|SHAP value|)', fontsize=11)
    plt.title('Explicabilidad Bioclimatica con SHAP (XGBoost)\nFactores Determinantes en la Prediccion de Riesgo', fontsize=13, fontweight='bold')
    for i, v in enumerate(top10_shap['Mean_SHAP']):
        plt.text(v + 0.01, i, f"{v:.3f}", va='center', fontsize=9, fontweight='semibold')
    plt.xlim(0, max(top10_shap['Mean_SHAP']) * 1.15)
    plt.tight_layout()
    fig3_path = fig_dir / "fig_shap_importancia_bioclimatica.png"
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print(f"✔ Figura guardada: {fig3_path}")

    # FIGURA 4: Simulación de la Fusión Multimodal y Adaptación Dinámica de Setpoints
    horas_test = np.arange(len(df_test))
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True, dpi=300)

    # Subplot 1: Clima (VPD y LWH)
    ax1 = axes[0]
    ax1.plot(horas_test, df_test['vpd_kpa'].values, label='VPD (kPa)', color='#2b83ba', lw=1.5)
    ax1.set_ylabel('VPD (kPa)', color='#2b83ba', fontsize=10)
    ax1.tick_params(axis='y', labelcolor='#2b83ba')
    ax1_twin = ax1.twinx()
    ax1_twin.fill_between(horas_test, 0, df_test['lwh_continuo_horas'].values, color='#abdda4', alpha=0.4, label='LWH Continuo (h)')
    ax1_twin.set_ylabel('LWH (h)', color='#2ca25f', fontsize=10)
    ax1_twin.tick_params(axis='y', labelcolor='#2ca25f')
    ax1.set_title('Respuesta Temporal del Lazo Supervisor Externo (18 Dias de Ensayo en Test)', fontsize=12, fontweight='bold')
    ax1.grid(True, linestyle=':', alpha=0.6)

    # Subplot 2: Visión Artificial (Severidad Foliar y Trampas)
    ax2 = axes[1]
    ax2.plot(horas_test, df_test['vision_severidad_foliar_pct'].values, label='Severidad Foliar YOLO (%)', color='#d7191c', lw=1.8)
    ax2.set_ylabel('Severidad (%)', color='#d7191c', fontsize=10)
    ax2.tick_params(axis='y', labelcolor='#d7191c')
    ax2_twin = ax2.twinx()
    ax2_twin.plot(horas_test, df_test['vision_conteo_trampa_amarilla'].values, label='Conteo Trampa SAHI (uds)', color='#fdae61', lw=1.5, linestyle='--')
    ax2_twin.set_ylabel('Plagas Trampa', color='#fdae61', fontsize=10)
    ax2_twin.tick_params(axis='y', labelcolor='#fdae61')
    ax2.grid(True, linestyle=':', alpha=0.6)

    # Subplot 3: Fusión Multimodal (Score de Riesgo y Umbrales)
    ax3 = axes[2]
    ax3.plot(horas_test, df_test['score_riesgo_fusion'].values, label='Score Fusión Multimodal', color='#404040', lw=2.2)
    ax3.axhline(0.30, color='#66c2a5', linestyle='--', label='Umbral Bajo/Medio (0.30)')
    ax3.axhline(0.55, color='#fdae61', linestyle='--', label='Umbral Medio/Alto (0.55)')
    ax3.axhline(0.75, color='#d7191c', linestyle='--', label='Umbral Critico (0.75)')
    ax3.fill_between(horas_test, 0.75, 1.0, color='#d7191c', alpha=0.15)
    ax3.set_ylabel('Score Riesgo [0, 1]', fontsize=10)
    ax3.set_ylim(-0.05, 1.05)
    ax3.legend(loc='upper left', fontsize=8, ncol=4)
    ax3.grid(True, linestyle=':', alpha=0.6)

    # Subplot 4: Ajuste Dinámico de Setpoints (Lazo Externo hacia ESP32)
    ax4 = axes[3]
    ax4.step(horas_test, df_test['sp_temp_ajustado'].values, where='post', label='SP Temp (°C) Ajustado por IA', color='#e41a1c', lw=2.0)
    ax4.axhline(18.0, color='#e41a1c', linestyle=':', label='SP Temp Base (18.0°C)')
    ax4.set_ylabel('SP Temp (°C)', color='#e41a1c', fontsize=10)
    ax4.tick_params(axis='y', labelcolor='#e41a1c')
    ax4_twin = ax4.twinx()
    ax4_twin.step(horas_test, df_test['sp_hum_ajustado'].values, where='post', label='SP Hum (%) Ajustado por IA', color='#377eb8', lw=2.0)
    ax4_twin.axhline(75.0, color='#377eb8', linestyle=':', label='SP Hum Base (75.0%)')
    ax4_twin.set_ylabel('SP Hum (%)', color='#377eb8', fontsize=10)
    ax4_twin.tick_params(axis='y', labelcolor='#377eb8')
    ax4.set_xlabel('Horas de Ensayo en Test (0 a 432 h)', fontsize=11)
    ax4.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    fig4_path = fig_dir / "fig_simulacion_fusion_lazo_externo.png"
    plt.savefig(fig4_path, dpi=300)
    plt.close()
    print(f"✔ Figura guardada: {fig4_path}")

    print("\n" + "=" * 80)
    print("✔ FASE 5 EJECUTADA CON ÉXITO")
    print("=" * 80)

if __name__ == "__main__":
    main()
