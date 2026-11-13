#!/usr/bin/env python3
"""
analisis_estadistico_tesis.py
Agente 5 - Analista de Datos / Estadístico
Análisis estadístico riguroso y reproducible sobre archivos reales del repositorio:
/home/rodrigo/Desktop/IOTtesis

Separa estrictamente:
1. Pilotos reales entrenados en Google Colab sobre datasets públicos (PlantVillage, PlantDoc).
2. Simulaciones físicas/matemáticas reproducibles (FOPDT, PID, serie agroclimática 90 días, Fase 5).
3. Datos de referencia/diseño y verificación de artefactos de software/firmware.

Salidas:
- Tablas CSV y Markdown (APA 7.a ed.) en /home/rodrigo/Desktop/IOTtesis/tesis/tablas/
- Gráficos PNG a 300 dpi en /home/rodrigo/Desktop/IOTtesis/tesis/figuras/ con prefijo fig_est_
- Resumen estructurado en consola para trazabilidad exacta con tesis/02_analisis_datos.md
"""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import optimize as opt
from scipy import stats


# ==============================================================================
# RUTAS Y CONFIGURACION GLOBAL
# ==============================================================================
BASE_DIR = Path("/home/rodrigo/Desktop/IOTtesis")
TESIS_DIR = BASE_DIR / "tesis"
TABLAS_DIR = TESIS_DIR / "tablas"
FIGURAS_DIR = TESIS_DIR / "figuras"

TABLAS_DIR.mkdir(parents=True, exist_ok=True)
FIGURAS_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "figure.dpi": 300,
    "savefig.dpi": 300,
})


# ==============================================================================
# UTILIDADES ESTADISTICAS
# ==============================================================================
def fmt_p(p: float) -> str:
    """Formatea valores p siguiendo convenciones APA 7 (p < .001 o 3-4 decimales)."""
    if np.isnan(p):
        return "N/A"
    if p < 0.0001:
        return "< .0001"
    if p < 0.001:
        return "< .001"
    return f"{p:.4f}".lstrip("0") if p < 1.0 else "1.000"


def fmt_p_num(p: float) -> str:
    """Formatea valor p con notación científica si es extremadamente pequeño."""
    if np.isnan(p):
        return "N/A"
    if p < 1e-4:
        return f"{p:.3e}"
    return f"{p:.4f}"


def resumen_descriptivo(arr: np.ndarray) -> dict[str, float]:
    """Calcula n, media, DE muestral, mediana, Q1, Q3, RIQ, min y max."""
    arr = np.asarray(arr, dtype=float)
    arr = arr[~np.isnan(arr)]
    q1, med, q3 = np.percentile(arr, [25, 50, 75])
    return {
        "n": int(len(arr)),
        "media": float(np.mean(arr)),
        "de": float(np.std(arr, ddof=1)),
        "mediana": float(med),
        "q1": float(q1),
        "q3": float(q3),
        "riq": float(q3 - q1),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def prueba_normalidad(arr: np.ndarray) -> dict[str, float]:
    """Ejecuta Shapiro-Wilk y D'Agostino-Pearson (si n >= 8 y varianza > 0)."""
    arr = np.asarray(arr, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) < 3 or np.std(arr, ddof=1) == 0:
        return {"sw_w": np.nan, "sw_p": np.nan, "dag_k2": np.nan, "dag_p": np.nan}
    sw_res = stats.shapiro(arr)
    dag_k2, dag_p = (np.nan, np.nan)
    if len(arr) >= 8:
        dag_res = stats.normaltest(arr)
        dag_k2, dag_p = float(dag_res.statistic), float(dag_res.pvalue)
    return {
        "sw_w": float(sw_res.statistic),
        "sw_p": float(sw_res.pvalue),
        "dag_k2": dag_k2,
        "dag_p": dag_p,
    }


def mann_whitney_con_efecto(x_pos: np.ndarray, x_neg: np.ndarray) -> dict[str, float]:
    """
    Mann-Whitney U bilateral entre grupo 1 (riesgo=1) y grupo 0 (riesgo=0).
    Reporta U1 (para grupo 1), Z con corrección por empates, valor p asintótico,
    r de rangos biserial (Wendt/Glass) y r de Rosenthal (|Z|/sqrt(N)).
    """
    g1 = np.asarray(x_pos, dtype=float)
    g0 = np.asarray(x_neg, dtype=float)
    n1, n0 = len(g1), len(g0)
    n_tot = n1 + n0

    res = stats.mannwhitneyu(g1, g0, alternative="two-sided", method="asymptotic")
    u1 = float(res.statistic)
    p_val = float(res.pvalue)

    # Z con corrección por empates (tie correction)
    concat = np.concatenate([g1, g0])
    ranks = stats.rankdata(concat)
    _, counts = np.unique(concat, return_counts=True)
    tie_term = np.sum(counts ** 3 - counts)
    mean_u = n1 * n0 / 2.0
    var_u = (n1 * n0 / 12.0) * ((n_tot + 1.0) - tie_term / (n_tot * (n_tot - 1.0)))
    sd_u = math.sqrt(var_u) if var_u > 0 else np.nan
    # Corrección de continuidad opcional no usada en Z para Rosenthal estándar,
    # pero coincide en tendencia con stats.mannwhitneyu
    z_val = (u1 - mean_u) / sd_u if sd_u and sd_u > 0 else np.nan

    # Rank-biserial correlation: r_rb = 2*U1/(n1*n0) - 1 (positivo si g1 > g0)
    r_rb = (2.0 * u1) / (n1 * n0) - 1.0
    r_rosenthal = abs(z_val) / math.sqrt(n_tot) if not np.isnan(z_val) else np.nan

    # Tamaño de efecto paramétrico complementario (Hedges' g / Cohen's d)
    s_pooled = math.sqrt(((n1 - 1) * np.var(g1, ddof=1) + (n0 - 1) * np.var(g0, ddof=1)) / (n_tot - 2))
    cohen_d = (np.mean(g1) - np.mean(g0)) / s_pooled if s_pooled > 0 else np.nan

    # Prueba t de Welch como contraste de sensibilidad
    welch = stats.ttest_ind(g1, g0, equal_var=False)

    return {
        "n1": n1,
        "n0": n0,
        "n_total": n_tot,
        "U": u1,
        "Z": float(z_val),
        "p_mw": p_val,
        "r_rb": float(r_rb),
        "r_rosenthal": float(r_rosenthal),
        "cohen_d": float(cohen_d),
        "welch_t": float(welch.statistic),
        "welch_df": float(welch.df),
        "welch_p": float(welch.pvalue),
    }


def wilcoxon_pareado_con_efecto(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    """
    Prueba pareada de Wilcoxon de rangos con signo sobre diferencias d = x - y.
    Reporta normalidad de d, estadístico W, Z normal aproximado, p, r de Rosenthal,
    mediana y RIQ de las diferencias, y t pareada de referencia.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    d = x - y
    n_pairs = len(d)

    norm_d = prueba_normalidad(d)
    w_res = stats.wilcoxon(x, y, zero_method="wilcox", alternative="two-sided", method="asymptotic")
    w_stat = float(w_res.statistic)
    p_wilcox = float(w_res.pvalue)

    # Cálculo explícito de Z para Wilcoxon sobre diferencias no nulas
    d_nz = d[d != 0]
    n_nz = len(d_nz)
    if n_nz > 0:
        abs_d = np.abs(d_nz)
        ranks = stats.rankdata(abs_d)
        r_pos = float(np.sum(ranks[d_nz > 0]))
        _, counts = np.unique(abs_d, return_counts=True)
        tie_term = np.sum(counts ** 3 - counts)
        mean_w = n_nz * (n_nz + 1.0) / 4.0
        var_w = (n_nz * (n_nz + 1.0) * (2.0 * n_nz + 1.0) - 0.5 * tie_term) / 24.0
        sd_w = math.sqrt(var_w) if var_w > 0 else np.nan
        z_val = (r_pos - mean_w) / sd_w if sd_w and sd_w > 0 else np.nan
        r_ros = abs(z_val) / math.sqrt(n_pairs) if not np.isnan(z_val) else np.nan
    else:
        z_val, r_ros = 0.0, 0.0

    # Mann-Whitney U independiente como referencia adicional sobre distribuciones de épocas
    mw_res = stats.mannwhitneyu(x, y, alternative="two-sided", method="asymptotic")

    # t pareada como referencia paramétrica
    t_res = stats.ttest_rel(x, y)

    q1_d, med_d, q3_d = np.percentile(d, [25, 50, 75])
    return {
        "n_pares": n_pairs,
        "n_no_cero": n_nz,
        "sw_diff_w": norm_d["sw_w"],
        "sw_diff_p": norm_d["sw_p"],
        "diff_media": float(np.mean(d)),
        "diff_de": float(np.std(d, ddof=1)),
        "diff_mediana": float(med_d),
        "diff_riq": float(q3_d - q1_d),
        "W_wilcoxon": w_stat,
        "Z_wilcoxon": float(z_val),
        "p_wilcoxon": p_wilcox,
        "r_rosenthal": float(r_ros),
        "U_mw": float(mw_res.statistic),
        "p_mw": float(mw_res.pvalue),
        "t_pareado": float(t_res.statistic),
        "gl_t": int(n_pairs - 1),
        "p_t_pareado": float(t_res.pvalue),
    }


def df_to_markdown(df: pd.DataFrame) -> str:
    """Convierte un DataFrame a tabla Markdown estándar sin depender de tabulate."""
    cols = [str(c) for c in df.columns]
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = []
    for _, row in df.iterrows():
        vals = [str(row[c]).replace("|", "\\|") for c in df.columns]
        rows.append("| " + " | ".join(vals) + " |")
    return "\n".join([header, sep, *rows])


def escribir_md_apa(path: Path, titulo: str, subtitulo: str, df: pd.DataFrame, nota: str) -> None:
    """Exporta un DataFrame a formato de tabla Markdown compatible con APA 7.a edición."""
    lines = [
        f"**{titulo}**  ",
        f"*{subtitulo}*\n",
        df_to_markdown(df),
        f"\n*Nota.* {nota}\n",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


# ==============================================================================
# BLOQUE A: ANALISIS AGROCLIMATICO SIMULADO (N = 2160 HORAS)
# ==============================================================================
def analizar_agroclimatico() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    print("\n" + "=" * 90)
    print("A. ANALISIS DE DATOS AGROCLIMATICOS SIMULADOS (n = 2160 horas)")
    print("=" * 90)

    csv_path = BASE_DIR / "data" / "synthetic" / "dataset_agroclimatico_invernadero.csv"
    df = pd.read_csv(csv_path)
    print(f"[INFO] Archivo cargado: {csv_path} ({len(df)} filas x {df.shape[1]} columnas)")

    vc = df["riesgo_infeccion_gt"].value_counts().sort_index()
    n0 = int(vc.get(0, 0))
    n1 = int(vc.get(1, 0))
    print(f"[INFO] Distribucion riesgo_infeccion_gt: 0 (Bajo/Moderado) = {n0} ({n0/len(df):.2%}), "
          f"1 (Alto/Critico) = {n1} ({n1/len(df):.2%})")

    variables = [
        ("temp_exterior_c", "Temperatura exterior (°C)"),
        ("temp_interior_c", "Temperatura interior (°C)"),
        ("hum_interior_pct", "Humedad relativa interior (%)"),
        ("vpd_kpa", "Déficit de presión de vapor, VPD (kPa)"),
        ("hum_suelo_pct", "Humedad volumétrica del suelo (%)"),
        ("lwh_continuo_horas", "Hoja húmeda continua, LWH (h)"),
        ("blight_units_7d", "Unidades de tizón 7 días, BU (pts)"),
    ]

    filas_csv = []
    filas_apa = []

    g0_mask = df["riesgo_infeccion_gt"] == 0
    g1_mask = df["riesgo_infeccion_gt"] == 1

    for col, etiqueta in variables:
        s_all = df[col].values
        s0 = df.loc[g0_mask, col].values
        s1 = df.loc[g1_mask, col].values

        d_all = resumen_descriptivo(s_all)
        d0 = resumen_descriptivo(s0)
        d1 = resumen_descriptivo(s1)

        nrm_0 = prueba_normalidad(s0)
        nrm_1 = prueba_normalidad(s1)
        lev = stats.levene(s0, s1, center="median")
        mw = mann_whitney_con_efecto(s1, s0)

        normal_ambos = (nrm_0["sw_p"] >= 0.05) and (nrm_1["sw_p"] >= 0.05)
        homocedastico = float(lev.pvalue) >= 0.05
        prueba_elegida = "t de Welch" if (normal_ambos and homocedastico) else "Mann-Whitney U"

        filas_csv.append({
            "variable_cod": col,
            "variable": etiqueta,
            "n_total": d_all["n"],
            "global_media": round(d_all["media"], 4),
            "global_de": round(d_all["de"], 4),
            "global_mediana": round(d_all["mediana"], 4),
            "global_riq": round(d_all["riq"], 4),
            "global_min": round(d_all["min"], 4),
            "global_max": round(d_all["max"], 4),
            "n_riesgo0": d0["n"],
            "r0_media": round(d0["media"], 4),
            "r0_de": round(d0["de"], 4),
            "r0_mediana": round(d0["mediana"], 4),
            "r0_riq": round(d0["riq"], 4),
            "r0_min": round(d0["min"], 4),
            "r0_max": round(d0["max"], 4),
            "r0_shapiro_W": round(nrm_0["sw_w"], 4),
            "r0_shapiro_p": nrm_0["sw_p"],
            "r0_dagostino_p": nrm_0["dag_p"],
            "n_riesgo1": d1["n"],
            "r1_media": round(d1["media"], 4),
            "r1_de": round(d1["de"], 4),
            "r1_mediana": round(d1["mediana"], 4),
            "r1_riq": round(d1["riq"], 4),
            "r1_min": round(d1["min"], 4),
            "r1_max": round(d1["max"], 4),
            "r1_shapiro_W": round(nrm_1["sw_w"], 4),
            "r1_shapiro_p": nrm_1["sw_p"],
            "r1_dagostino_p": nrm_1["dag_p"],
            "levene_F": round(float(lev.statistic), 4),
            "levene_p": float(lev.pvalue),
            "prueba_seleccionada": prueba_elegida,
            "U_mann_whitney": round(mw["U"], 1),
            "Z_mw": round(mw["Z"], 4),
            "p_mw": mw["p_mw"],
            "r_rangos_biserial": round(mw["r_rb"], 4),
            "r_rosenthal": round(mw["r_rosenthal"], 4),
            "cohen_d_ref": round(mw["cohen_d"], 4),
            "welch_t_ref": round(mw["welch_t"], 4),
            "welch_p_ref": mw["welch_p"],
        })

        filas_apa.append({
            "Variable": etiqueta,
            f"Sin riesgo (n={n0}) M ± DE": f"{d0['media']:.2f} ± {d0['de']:.2f}",
            f"Sin riesgo Mdn (RIQ) [Min–Max]": f"{d0['mediana']:.2f} ({d0['riq']:.2f}) [{d0['min']:.2f}–{d0['max']:.2f}]",
            f"Con riesgo (n={n1}) M ± DE": f"{d1['media']:.2f} ± {d1['de']:.2f}",
            f"Con riesgo Mdn (RIQ) [Min–Max]": f"{d1['mediana']:.2f} ({d1['riq']:.2f}) [{d1['min']:.2f}–{d1['max']:.2f}]",
            "Levene F (p)": f"{lev.statistic:.2f} ({fmt_p(lev.pvalue)})",
            "Mann-Whitney U (Z)": f"{mw['U']:,.0f} ({mw['Z']:.2f})",
            "p": fmt_p(mw["p_mw"]),
            "r_rb / |r|": f"{mw['r_rb']:.3f} / {mw['r_rosenthal']:.3f}",
        })

    df_t1_csv = pd.DataFrame(filas_csv)
    df_t1_apa = pd.DataFrame(filas_apa)

    print("\n--- Tabla 01 (Resumen Comparativo Estratos) ---")
    print(df_t1_apa.to_string(index=False))

    print("\n--- Verificacion de Supuestos y Descriptiva Global (n = 2160) ---")
    for _, r in df_t1_csv.iterrows():
        print(
            f"  {r['variable_cod']:<20} | Global M={r['global_media']:.2f}±{r['global_de']:.2f}, Mdn={r['global_mediana']:.2f} (RIQ={r['global_riq']:.2f}) [{r['global_min']:.2f}..{r['global_max']:.2f}] | "
            f"SW0 W={r['r0_shapiro_W']:.4f} (p={fmt_p_num(r['r0_shapiro_p'])}), SW1 W={r['r1_shapiro_W']:.4f} (p={fmt_p_num(r['r1_shapiro_p'])}) | "
            f"Levene F={r['levene_F']:.2f} (p={fmt_p_num(r['levene_p'])}) | Welch t={r['welch_t_ref']:.2f} (p={fmt_p_num(r['welch_p_ref'])})"
        )

    # Correlaciones de Spearman entre VPD, HR, LWH, Blight Units y Riesgo GT
    corr_vars = [
        "vpd_kpa",
        "hum_interior_pct",
        "lwh_continuo_horas",
        "blight_units_7d",
        "riesgo_infeccion_gt",
    ]
    corr_rows = []
    for i, v1 in enumerate(corr_vars):
        for j, v2 in enumerate(corr_vars):
            if j <= i:
                continue
            rho, p_sp = stats.spearmanr(df[v1].values, df[v2].values)
            corr_rows.append({
                "var_1": v1,
                "var_2": v2,
                "n": len(df),
                "spearman_rho": round(float(rho), 4),
                "p_valor": float(p_sp),
                "p_formato": fmt_p_num(float(p_sp)),
            })
    df_corr = pd.DataFrame(corr_rows)
    print("\n--- Correlaciones de Spearman (n = 2160) ---")
    print(df_corr.to_string(index=False))

    # Exportar Tabla 01 CSV + MD APA
    t1_csv_path = TABLAS_DIR / "tabla_01_descriptiva_agroclimatica.csv"
    t1_md_path = TABLAS_DIR / "tabla_01_descriptiva_agroclimatica.md"
    df_t1_csv.to_csv(t1_csv_path, index=False)

    # Construir nota APA con los resultados de Spearman principales
    sp_dict = {(r["var_1"], r["var_2"]): r for _, r in df_corr.iterrows()}
    nota_t1 = (
        f"Datos simulados horarios (N = {len(df)}, 90 días; scripts/generar_dataset_agroclimatico.py). "
        f"Ninguna variable cumplió normalidad conjunta en Shapiro-Wilk (todos p <= .020) y/o homocedasticidad en Levene "
        f"(excepto temp_exterior_c en Levene p = {df_t1_csv.loc[0, 'levene_p']:.4f}, pero no normal en Shapiro-Wilk p < .001), "
        f"por lo que se aplicó la prueba U de Mann-Whitney bilateral (N = {len(df)}). "
        f"M = media; DE = desviación estándar muestral; Mdn = mediana; RIQ = rango intercuartílico; "
        f"r_rb = correlación biserial de rangos (positivo indica valores mayores en riesgo = 1); "
        f"|r| = tamaño de efecto de Rosenthal (|Z|/sqrt(N)). "
        f"Correlaciones de Spearman (N = 2160): VPD vs. HR rho = {sp_dict[('vpd_kpa', 'hum_interior_pct')]['spearman_rho']:.4f} (p < .001); "
        f"VPD vs. LWH rho = {sp_dict[('vpd_kpa', 'lwh_continuo_horas')]['spearman_rho']:.4f} (p < .001); "
        f"VPD vs. Blight Units rho = {sp_dict[('vpd_kpa', 'blight_units_7d')]['spearman_rho']:.4f} (p = {sp_dict[('vpd_kpa', 'blight_units_7d')]['p_formato']}); "
        f"LWH vs. Blight Units rho = {sp_dict[('lwh_continuo_horas', 'blight_units_7d')]['spearman_rho']:.4f} (p < .001); "
        f"Blight Units vs. Riesgo GT rho = {sp_dict[('blight_units_7d', 'riesgo_infeccion_gt')]['spearman_rho']:.4f} (p < .001)."
    )
    escribir_md_apa(
        t1_md_path,
        "Tabla 1",
        "Estadística descriptiva, verificación de supuestos y comparación no paramétrica de variables agroclimáticas simuladas según riesgo de tizón tardío (n = 2160 horas)",
        df_t1_apa,
        nota_t1,
    )
    print(f"[OK] Exportada Tabla 01: {t1_csv_path} y {t1_md_path}")

    # Figura 1: fig_est_boxplots_vpd_riesgo.png
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5), dpi=300)
    panel_vars = [
        ("vpd_kpa", "Déficit de Presión de Vapor, VPD [kPa]"),
        ("hum_interior_pct", "Humedad Relativa Interior [%]"),
        ("temp_interior_c", "Temperatura Interior [°C]"),
        ("lwh_continuo_horas", "Hoja Húmeda Continua, LWH [h]"),
    ]
    col_map = {r["variable_cod"]: r for _, r in df_t1_csv.iterrows()}
    paleta = ["#3182CE", "#E53E3E"]

    for ax, (col, title) in zip(axes.flat, panel_vars):
        d0 = df.loc[g0_mask, col].values
        d1 = df.loc[g1_mask, col].values
        bp = ax.boxplot(
            [d0, d1],
            tick_labels=[f"Sin riesgo (0)\n(n={n0})", f"Con riesgo (1)\n(n={n1})"],
            patch_artist=True,
            widths=0.5,
            showmeans=True,
            meanprops={"marker": "D", "markerfacecolor": "white", "markeredgecolor": "black", "markersize": 5},
            flierprops={"marker": "o", "markersize": 2.5, "alpha": 0.35, "markerfacecolor": "#4A5568"},
        )
        for patch, color in zip(bp["boxes"], paleta):
            patch.set_facecolor(color)
            patch.set_alpha(0.65)
            patch.set_edgecolor("#1A202C")
        for median in bp["medians"]:
            median.set_color("#1A202C")
            median.set_linewidth(1.8)

        row_info = col_map[col]
        p_txt = fmt_p(row_info["p_mw"])
        y_min = min(d0.min(), d1.min())
        y_max = max(d0.max(), d1.max())
        yrange = y_max - y_min if y_max > y_min else 1.0
        ax.set_ylim(y_min - 0.06 * yrange, y_max + 0.28 * yrange)
        ax.set_title(title, fontsize=10.5)
        ax.grid(True, axis="y", linestyle=":", alpha=0.6)
        txt = (
            f"U = {row_info['U_mann_whitney']:,.0f}, p {p_txt}\n"
            f"r_rb = {row_info['r_rangos_biserial']:.3f}, |r| = {row_info['r_rosenthal']:.3f}\n"
            f"Mdn0 = {row_info['r0_mediana']:.2f} vs. Mdn1 = {row_info['r1_mediana']:.2f}"
        )
        ax.text(
            0.03, 0.96, txt,
            transform=ax.transAxes, va="top", ha="left",
            fontsize=8,
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.88, "edgecolor": "#CBD5E0"},
        )

    fig.suptitle(
        "Comparación Agroclimática Estratificada por Riesgo Fitopatológico (Simulación 90 Días, n = 2160 h)",
        fontsize=12, fontweight="bold", y=0.98
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    fig1_path = FIGURAS_DIR / "fig_est_boxplots_vpd_riesgo.png"
    plt.savefig(fig1_path, dpi=300)
    plt.close(fig)
    print(f"[OK] Guardada figura: {fig1_path}")

    return df, df_t1_csv, df_t1_apa, df_corr


# ==============================================================================
# BLOQUE B: ANALISIS TECNICO FOPDT Y COMPARATIVA PID VS ON/OFF
# ==============================================================================
def modelo_fopdt_ecuacion(t: np.ndarray, k: float, tau: float, theta: float, t_step: float = 120.0, t0: float = 8.5) -> np.ndarray:
    y = np.full_like(t, t0, dtype=float)
    idx = t >= (t_step + theta)
    t_ef = t[idx] - (t_step + theta)
    delta_u = 70.0
    y[idx] = t0 + k * delta_u * (1.0 - np.exp(-t_ef / tau))
    return y


def analizar_fopdt_pid() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    print("\n" + "=" * 90)
    print("B. ANALISIS DEL MODELO FOPDT Y COMPARATIVA PID VS. ON/OFF")
    print("=" * 90)

    step_path = BASE_DIR / "data" / "synthetic" / "prueba_escalon_fopdt.csv"
    df_step = pd.read_csv(step_path)
    t = df_step["tiempo_segundos"].values
    y = df_step["temperatura_medida_c"].values
    y_ideal = df_step["temperatura_ideal_c"].values

    t_step = 120.0
    delta_u = 70.0
    t0_est = float(np.mean(y[t < t_step]))
    t_inf_est = float(np.mean(y[t >= 1500]))
    delta_t = t_inf_est - t0_est
    k_init = delta_t / delta_u
    y_28 = t0_est + 0.283 * delta_t
    y_63 = t0_est + 0.632 * delta_t
    t_28 = float(np.interp(y_28, y[t >= t_step], t[t >= t_step]))
    t_63 = float(np.interp(y_63, y[t >= t_step], t[t >= t_step]))
    tau_init = 1.5 * (t_63 - t_28)
    theta_init = max(5.0, (t_63 - t_step) - tau_init)

    def func_fit(t_vals, k_val, tau_val, theta_val):
        return modelo_fopdt_ecuacion(t_vals, k_val, tau_val, theta_val, t_step=t_step, t0=t0_est)

    popt, pcov = opt.curve_fit(
        func_fit, t, y,
        p0=[k_init, tau_init, theta_init],
        bounds=([0.05, 50.0, 5.0], [0.5, 600.0, 100.0]),
    )
    k_opt, tau_opt, theta_opt = [float(v) for v in popt]
    perr = np.sqrt(np.diag(pcov))
    y_pred = func_fit(t, k_opt, tau_opt, theta_opt)

    residuos = y - y_pred
    ss_res = float(np.sum(residuos ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot
    rmse = float(np.sqrt(np.mean(residuos ** 2)))
    mae = float(np.mean(np.abs(residuos)))
    max_ae = float(np.max(np.abs(residuos)))

    # Comparación contra señal ideal sin ruido
    diff_ideal = y_pred - y_ideal
    rmse_ideal = float(np.sqrt(np.mean(diff_ideal ** 2)))
    mae_ideal = float(np.mean(np.abs(diff_ideal)))

    desc_res = resumen_descriptivo(residuos)
    nrm_res = prueba_normalidad(residuos)
    dw = float(np.sum(np.diff(residuos) ** 2) / ss_res)
    ac1_r, ac1_p = stats.pearsonr(residuos[:-1], residuos[1:])

    fopdt_info = {
        "n_muestras": int(len(df_step)),
        "T0_c": t0_est,
        "Tinf_c": t_inf_est,
        "K": k_opt,
        "K_se": float(perr[0]),
        "tau_s": tau_opt,
        "tau_se": float(perr[1]),
        "theta_s": theta_opt,
        "theta_se": float(perr[2]),
        "relacion_theta_tau": theta_opt / tau_opt,
        "R2": r2,
        "RMSE_c": rmse,
        "MAE_c": mae,
        "MaxAE_c": max_ae,
        "RMSE_vs_ideal_c": rmse_ideal,
        "MAE_vs_ideal_c": mae_ideal,
        "res_media": desc_res["media"],
        "res_de": desc_res["de"],
        "res_mediana": desc_res["mediana"],
        "res_riq": desc_res["riq"],
        "res_min": desc_res["min"],
        "res_max": desc_res["max"],
        "res_shapiro_W": nrm_res["sw_w"],
        "res_shapiro_p": nrm_res["sw_p"],
        "res_dagostino_k2": nrm_res["dag_k2"],
        "res_dagostino_p": nrm_res["dag_p"],
        "res_durbin_watson": dw,
        "res_acf_lag1": float(ac1_r),
        "res_acf_lag1_p": float(ac1_p),
    }

    print("[INFO] Ajuste FOPDT sobre prueba_escalon_fopdt.csv (N = 1800):")
    print(f"  K = {k_opt:.4f} ± {perr[0]:.5f} °C/% | tau = {tau_opt:.2f} ± {perr[1]:.2f} s | theta = {theta_opt:.2f} ± {perr[2]:.2f} s")
    print(f"  R2 = {r2:.6f} | RMSE = {rmse:.4f} °C | MAE = {mae:.4f} °C | MaxAE = {max_ae:.4f} °C")
    print(f"  Vs temperatura_ideal_c: RMSE = {rmse_ideal:.4f} °C | MAE = {mae_ideal:.4f} °C")
    print(f"  Residuos: M = {desc_res['media']:.5f}, DE = {desc_res['de']:.4f}, Mdn = {desc_res['mediana']:.4f}, RIQ = {desc_res['riq']:.4f}")
    print(f"  Normalidad residuos: Shapiro-Wilk W = {nrm_res['sw_w']:.4f} (p = {nrm_res['sw_p']:.4f}), D'Agostino K2 = {nrm_res['dag_k2']:.4f} (p = {nrm_res['dag_p']:.4f})")
    print(f"  Independencia residuos: Durbin-Watson = {dw:.4f}, Autocorrelación lag-1 r = {ac1_r:.4f} (p = {ac1_p:.3e})")

    # Comparativa PID vs On/Off
    pid_path = BASE_DIR / "data" / "synthetic" / "metricas_comparativa_pid_onoff.csv"
    df_pid = pd.read_csv(pid_path)
    opt_row = df_pid[df_pid["Método"] == "Optuna (Óptimo)"].iloc[0]

    comp_rows = []
    apa_rows = []
    for _, r in df_pid.iterrows():
        metodo = r["Método"]
        d_iae = ((opt_row["IAE"] - r["IAE"]) / r["IAE"]) * 100.0
        d_itae = ((opt_row["ITAE"] - r["ITAE"]) / r["ITAE"]) * 100.0
        d_tv = ((opt_row["TV_u"] - r["TV_u"]) / r["TV_u"]) * 100.0
        d_mp = ((opt_row["Mp_pct"] - r["Mp_pct"]) / r["Mp_pct"]) * 100.0 if r["Mp_pct"] > 0 else np.nan
        d_ts = ((opt_row["ts_s"] - r["ts_s"]) / r["ts_s"]) * 100.0 if pd.notna(r["ts_s"]) else np.nan
        d_tr = ((opt_row["tr_s"] - r["tr_s"]) / r["tr_s"]) * 100.0 if pd.notna(r["tr_s"]) else np.nan

        comp_rows.append({
            "Metodo": metodo,
            "Kp": round(float(r["Kp"]), 4),
            "Ki": round(float(r["Ki"]), 5),
            "Kd": round(float(r["Kd"]), 4),
            "tr_s": round(float(r["tr_s"]), 2),
            "ts_s": round(float(r["ts_s"]), 2) if pd.notna(r["ts_s"]) else np.nan,
            "Mp_pct": round(float(r["Mp_pct"]), 4),
            "ess_c": float(r["ess_c"]),
            "IAE": round(float(r["IAE"]), 2),
            "ITAE": round(float(r["ITAE"]), 2),
            "TV_u": round(float(r["TV_u"]), 2),
            "Delta_Optuna_IAE_pct": round(float(d_iae), 2),
            "Delta_Optuna_ITAE_pct": round(float(d_itae), 2),
            "Delta_Optuna_TVu_pct": round(float(d_tv), 2),
            "Delta_Optuna_Mp_pct": round(float(d_mp), 2) if not np.isnan(d_mp) else np.nan,
            "Delta_Optuna_ts_pct": round(float(d_ts), 2) if not np.isnan(d_ts) else np.nan,
            "Delta_Optuna_tr_pct": round(float(d_tr), 2) if not np.isnan(d_tr) else np.nan,
        })

        ts_str = f"{r['ts_s']:.1f}" if pd.notna(r["ts_s"]) else "No asienta"
        d_iae_str = "Ref." if metodo == "Optuna (Óptimo)" else f"{d_iae:+.2f}%"
        d_itae_str = "Ref." if metodo == "Optuna (Óptimo)" else f"{d_itae:+.2f}%"
        d_tv_str = "Ref." if metodo == "Optuna (Óptimo)" else f"{d_tv:+.2f}%"

        apa_rows.append({
            "Controlador / Método": metodo,
            "Kp / Ki / Kd": f"{r['Kp']:.2f} / {r['Ki']:.4f} / {r['Kd']:.2f}",
            "tr (s)": f"{r['tr_s']:.1f}",
            "ts (s)": ts_str,
            "Mp (%)": f"{r['Mp_pct']:.2f}",
            "e_ss (°C)": f"{r['ess_c']:.4f}" if r["ess_c"] >= 0.0001 else f"{r['ess_c']:.2e}",
            "IAE (°C·s)": f"{r['IAE']:.2f}",
            "ITAE (°C·s²)": f"{r['ITAE']:,.1f}",
            "TV_u (%)": f"{r['TV_u']:.2f}",
            "Delta Optuna (IAE / ITAE / TV_u)": f"{d_iae_str} / {d_itae_str} / {d_tv_str}",
        })

    df_t2_csv = pd.DataFrame(comp_rows)
    df_t2_apa = pd.DataFrame(apa_rows)

    print("\n--- Tabla 02 (Comparativa PID vs On/Off) ---")
    print(df_t2_apa.to_string(index=False))

    t2_csv_path = TABLAS_DIR / "tabla_02_fopdt_pid_comparativa.csv"
    t2_md_path = TABLAS_DIR / "tabla_02_fopdt_pid_comparativa.md"
    df_t2_csv.to_csv(t2_csv_path, index=False)

    nota_t2 = (
        f"Datos provenientes de simulación física/matemática reproducible (scripts/ejecutar_fase2_identificacion_pid.py "
        f"sobre data/synthetic/prueba_escalon_fopdt.csv y data/synthetic/metricas_comparativa_pid_onoff.csv). "
        f"Identificación FOPDT (N = {fopdt_info['n_muestras']}, escalón u = 70% en t = 120 s): "
        f"K = {k_opt:.4f} ± {perr[0]:.5f} °C/%, tau = {tau_opt:.2f} ± {perr[1]:.2f} s, theta = {theta_opt:.2f} ± {perr[2]:.2f} s; "
        f"R² = {r2:.4f}, RMSE = {rmse:.4f} °C, MAE = {mae:.4f} °C. "
        f"Diagnóstico de residuos (e = y - y_hat): M = {desc_res['media']:.5f} °C, DE = {desc_res['de']:.4f} °C, "
        f"Shapiro-Wilk W = {nrm_res['sw_w']:.4f} (p = {nrm_res['sw_p']:.4f}), Durbin-Watson = {dw:.4f} "
        f"(autocorrelación lag-1 r = {ac1_r:.4f}, explicada por la componente sinusoidal de viento T = 600 s). "
        f"Delta Optuna = ((Optuna - Método) / Método) × 100; valores negativos indican reducción de error o esfuerzo respecto al método comparado. "
        f"Control On/Off (±0.5 °C) presenta ciclo límite sostenido (ts no asienta; Mp = 9.27%, ess = 0.7837 °C)."
    )
    escribir_md_apa(
        t2_md_path,
        "Tabla 2",
        "Desempeño comparativo de sintonizaciones PID frente al control On/Off y ajuste del modelo FOPDT simulado",
        df_t2_apa,
        nota_t2,
    )
    print(f"[OK] Exportada Tabla 02: {t2_csv_path} y {t2_md_path}")

    # Figura 2: fig_est_residuos_fopdt.png (Diagnóstico 2x2 de residuos FOPDT)
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.2), dpi=300)

    # Panel 1: Residuos en el tiempo
    ax = axes[0, 0]
    ax.plot(t / 60.0, residuos, color="#2B6CB0", linewidth=0.75, alpha=0.85, label="Residuos $e(t) = y - \\hat{y}$")
    ax.axhline(0.0, color="#1A202C", linestyle="--", linewidth=1.2)
    ax.axhline(2 * desc_res["de"], color="#E53E3E", linestyle=":", linewidth=1.0, label=f"±2 DE (±{2*desc_res['de']:.2f} °C)")
    ax.axhline(-2 * desc_res["de"], color="#E53E3E", linestyle=":", linewidth=1.0)
    ax.set_title("(a) Residuos en el Tiempo (Oscilación Viento T = 10 min)")
    ax.set_xlabel("Tiempo [min]")
    ax.set_ylabel("Residuo [°C]")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")

    # Panel 2: Histograma + Curva Normal teórica
    ax = axes[0, 1]
    ax.hist(residuos, bins=32, density=True, color="#4299E1", alpha=0.65, edgecolor="#2B6CB0", label="Frecuencia observada")
    xs = np.linspace(residuos.min(), residuos.max(), 300)
    ax.plot(xs, stats.norm.pdf(xs, desc_res["media"], desc_res["de"]), color="#E53E3E", linewidth=2.0, label="Normal teórica")
    ax.set_title("(b) Distribución de Residuos FOPDT")
    ax.set_xlabel("Residuo [°C]")
    ax.set_ylabel("Densidad")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    ax.text(
        0.03, 0.95,
        f"M = {desc_res['media']:.4f} °C\nDE = {desc_res['de']:.4f} °C\nMAE = {mae:.4f} °C",
        transform=ax.transAxes, va="top", fontsize=8,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.9, "edgecolor": "#CBD5E0"},
    )

    # Panel 3: Q-Q Plot
    ax = axes[1, 0]
    (osm, osr), (slope, intercept, r_qq) = stats.probplot(residuos, dist="norm")
    ax.scatter(osm, osr, s=10, alpha=0.6, color="#2B6CB0", label="Cuantiles muestrales")
    ax.plot(osm, slope * osm + intercept, color="#E53E3E", linewidth=1.8, label="Recta normal teórica")
    ax.set_title("(c) Gráfico Q-Q Normal de Residuos")
    ax.set_xlabel("Cuantiles teóricos N(0, 1)")
    ax.set_ylabel("Residuos ordenados [°C]")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left")
    ax.text(
        0.97, 0.05,
        f"Shapiro-Wilk W = {nrm_res['sw_w']:.4f} (p = {nrm_res['sw_p']:.4f})\n"
        f"D'Agostino K² = {nrm_res['dag_k2']:.2f} (p = {nrm_res['dag_p']:.4f})",
        transform=ax.transAxes, va="bottom", ha="right", fontsize=8,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.9, "edgecolor": "#CBD5E0"},
    )

    # Panel 4: Autocorrelación de residuos (lags 1 a 30 s)
    ax = axes[1, 1]
    lags = np.arange(1, 31)
    acf_vals = [float(np.corrcoef(residuos[:-k], residuos[k:])[0, 1]) for k in lags]
    ci_95 = 1.96 / math.sqrt(len(residuos))
    ax.bar(lags, acf_vals, width=0.6, color="#3182CE", alpha=0.75, label="ACF muestral")
    ax.axhline(ci_95, color="#E53E3E", linestyle="--", linewidth=1.1, label=f"Banda ±1.96/√N (±{ci_95:.3f})")
    ax.axhline(-ci_95, color="#E53E3E", linestyle="--", linewidth=1.1)
    ax.axhline(0.0, color="#1A202C", linewidth=0.8)
    ax.set_title("(d) Función de Autocorrelación de Residuos (Lags 1–30 s)")
    ax.set_xlabel("Retardo (lag) [s]")
    ax.set_ylabel("Autocorrelación r")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    ax.text(
        0.03, 0.05,
        f"Durbin-Watson = {dw:.3f}\nr(lag 1) = {ac1_r:.3f}",
        transform=ax.transAxes, va="bottom", fontsize=8,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.9, "edgecolor": "#CBD5E0"},
    )

    fig.suptitle(
        f"Diagnóstico Estadístico de Residuos del Modelo FOPDT (prueba_escalon_fopdt.csv, N = {len(df_step)})",
        fontsize=12, fontweight="bold", y=0.98
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    fig2_path = FIGURAS_DIR / "fig_est_residuos_fopdt.png"
    plt.savefig(fig2_path, dpi=300)
    plt.close(fig)
    print(f"[OK] Guardada figura: {fig2_path}")

    return fopdt_info, df_t2_csv, df_t2_apa


# ==============================================================================
# BLOQUE C: VISION POR COMPUTADORA EN COLAB REAL Y BALANCE DE DATASETS REALES
# ==============================================================================
def analizar_colab_y_datasets() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, Any]]:
    print("\n" + "=" * 90)
    print("C. ANALISIS DE MODELOS REALES EN COLAB Y DATASETS PUBLICOS CURADOS")
    print("=" * 90)

    colab_dir = BASE_DIR / "data" / "models" / "entrenados_colab"
    pv_res = pd.read_csv(colab_dir / "yolo26n_plantvillage_classify" / "results.csv")
    pd26_res = pd.read_csv(colab_dir / "yolo26n_plantdoc_detect" / "results.csv")
    pd11_res = pd.read_csv(colab_dir / "yolo11n_plantdoc_detect" / "results.csv")

    with open(colab_dir / "verificacion.json", "r", encoding="utf-8") as f:
        verif = json.load(f)
    resumen_final = pd.read_csv(colab_dir / "resumen_evaluacion_final.csv")

    # 1. PlantVillage classify (25 épocas en CSV, 50 planificadas)
    pv_last5 = pv_res.tail(5)
    pv_best_loss_ep = int(pv_res.loc[pv_res["val/loss"].idxmin(), "epoch"])
    pv_best_acc_ep = int(pv_res.loc[pv_res["metrics/accuracy_top1"].idxmax(), "epoch"])
    print(f"[INFO] PlantVillage (yolo26n_plantvillage_classify): {len(pv_res)} épocas en results.csv (50 planificadas).")
    print(f"  Accuracy top-1 últimas 5 épocas (21-25): M = {pv_last5['metrics/accuracy_top1'].mean():.4f} ± {pv_last5['metrics/accuracy_top1'].std(ddof=1):.4f}, "
          f"Mdn = {pv_last5['metrics/accuracy_top1'].median():.4f} (RIQ = {np.percentile(pv_last5['metrics/accuracy_top1'], 75) - np.percentile(pv_last5['metrics/accuracy_top1'], 25):.4f})")
    print(f"  val/loss mínimo = {pv_res['val/loss'].min():.5f} en época {pv_best_loss_ep}; accuracy=1.0 alcanzado por primera vez en época {pv_best_acc_ep}")

    # 2. PlantDoc detect: 40 épocas comunes (yolo26n tiene 40, yolo11n tiene 43)
    n_common = min(len(pd26_res), len(pd11_res))
    pd26_c = pd26_res.iloc[:n_common].reset_index(drop=True)
    pd11_c = pd11_res.iloc[:n_common].reset_index(drop=True)

    metricas_det = [
        ("metrics/mAP50(B)", "mAP@0.50"),
        ("metrics/mAP50-95(B)", "mAP@0.50:0.95"),
        ("metrics/precision(B)", "Precision"),
        ("metrics/recall(B)", "Recall"),
    ]

    comp_colab_rows = []
    for col, nom in metricas_det:
        x = pd26_c[col].values
        y = pd11_c[col].values
        w_res = wilcoxon_pareado_con_efecto(x, y)

        x_last10 = pd26_c[col].tail(10).values
        y_last10 = pd11_c[col].tail(10).values
        dx26 = resumen_descriptivo(x)
        dy11 = resumen_descriptivo(y)
        dx26_l10 = resumen_descriptivo(x_last10)
        dy11_l10 = resumen_descriptivo(y_last10)

        comp_colab_rows.append({
            "Metrica": nom,
            "Columna_CSV": col,
            "Epocas_comunes": n_common,
            "YOLO26n_40ep_Media": round(dx26["media"], 4),
            "YOLO26n_40ep_DE": round(dx26["de"], 4),
            "YOLO26n_40ep_Mdn": round(dx26["mediana"], 4),
            "YOLO26n_40ep_RIQ": round(dx26["riq"], 4),
            "YOLO26n_Ult10_Media": round(dx26_l10["media"], 4),
            "YOLO26n_Ult10_DE": round(dx26_l10["de"], 4),
            "YOLO11n_40ep_Media": round(dy11["media"], 4),
            "YOLO11n_40ep_DE": round(dy11["de"], 4),
            "YOLO11n_40ep_Mdn": round(dy11["mediana"], 4),
            "YOLO11n_40ep_RIQ": round(dy11["riq"], 4),
            "YOLO11n_Ult10_Media": round(dy11_l10["media"], 4),
            "YOLO11n_Ult10_DE": round(dy11_l10["de"], 4),
            "Diff_Shapiro_W": round(w_res["sw_diff_w"], 4),
            "Diff_Shapiro_p": round(w_res["sw_diff_p"], 4),
            "Diff_Mdn": round(w_res["diff_mediana"], 4),
            "Diff_RIQ": round(w_res["diff_riq"], 4),
            "Wilcoxon_W": round(w_res["W_wilcoxon"], 1),
            "Wilcoxon_Z": round(w_res["Z_wilcoxon"], 4),
            "Wilcoxon_p": w_res["p_wilcoxon"],
            "Rosenthal_r": round(w_res["r_rosenthal"], 4),
            "MannWhitney_U_40vs40": round(w_res["U_mw"], 1),
            "MannWhitney_p": w_res["p_mw"],
            "t_pareado_ref": round(w_res["t_pareado"], 4),
            "p_t_pareado_ref": w_res["p_t_pareado"],
        })

    df_colab_comp = pd.DataFrame(comp_colab_rows)
    print("\n--- Comparativa Dinámica de Validación (40 épocas comunes, PlantDoc) ---")
    for _, r in df_colab_comp.iterrows():
        print(
            f"  {r['Metrica']:<14} | YOLO26n Mdn={r['YOLO26n_40ep_Mdn']:.4f} (RIQ={r['YOLO26n_40ep_RIQ']:.4f}) vs "
            f"YOLO11n Mdn={r['YOLO11n_40ep_Mdn']:.4f} (RIQ={r['YOLO11n_40ep_RIQ']:.4f}) | "
            f"Diff SW p={r['Diff_Shapiro_p']:.4f} | Wilcoxon W={r['Wilcoxon_W']:.1f}, Z={r['Wilcoxon_Z']:.2f}, "
            f"p={fmt_p_num(r['Wilcoxon_p'])}, r={r['Rosenthal_r']:.3f} | MW U={r['MannWhitney_U_40vs40']:.1f} (p={fmt_p_num(r['MannWhitney_p'])})"
        )

    # Extraer métricas puntuales de verificacion.json y pesos
    modelos_verif = {m["run"]: m for m in verif["models"]}
    m_pv = modelos_verif["yolo26n_plantvillage_classify"]
    m_26 = modelos_verif["yolo26n_plantdoc_detect"]
    m_11 = modelos_verif["yolo11n_plantdoc_detect"]

    for run_name, m in modelos_verif.items():
        w_size_mb = Path(m["weights_path"]).stat().st_size / (1024 * 1024)
        m["weights_size_mb"] = round(w_size_mb, 3)

    # Descriptiva de últimas 10 épocas de yolo11n completo (ep 34-43) y yolo26n (ep 31-40)
    pd26_best_ep = int(pd26_res.loc[pd26_res["metrics/mAP50-95(B)"].idxmax(), "epoch"])
    pd11_best_ep = int(pd11_res.loc[pd11_res["metrics/mAP50-95(B)"].idxmax(), "epoch"])
    print(f"[INFO] Mejor época por mAP50-95(B): YOLO26n época {pd26_best_ep} ({pd26_res['metrics/mAP50-95(B)'].max():.5f}), "
          f"YOLO11n época {pd11_best_ep} ({pd11_res['metrics/mAP50-95(B)'].max():.5f})")
    print(f"[INFO] Test único YOLO26n PlantDoc (resumen_evaluacion_final.csv): "
          f"mAP50={m_26['test']['metrics/mAP50(B)']:.4f}, mAP50-95={m_26['test']['metrics/mAP50-95(B)']:.4f}, "
          f"Precision={m_26['test']['metrics/precision(B)']:.4f}, Recall={m_26['test']['metrics/recall(B)']:.4f}")

    # Balance de datasets reales
    with open(BASE_DIR / "data" / "processed" / "papa_plantvillage_clasificacion" / "report.json", "r", encoding="utf-8") as f:
        rep_pv = json.load(f)
    with open(BASE_DIR / "data" / "processed" / "papa_plantdoc_yolo" / "report.json", "r", encoding="utf-8") as f:
        rep_pd = json.load(f)

    def calc_balance(rep: dict[str, Any]) -> dict[str, Any]:
        tot_imgs_cls: dict[str, int] = {}
        split_img_appearances: dict[str, int] = {}
        for sp, cls_dict in rep["images_per_class"].items():
            split_img_appearances[sp] = sum(cls_dict.values())
            for c, n in cls_dict.items():
                tot_imgs_cls[c] = tot_imgs_cls.get(c, 0) + n
        total_unique_imgs = int(rep["images"])
        sum_class_imgs = sum(tot_imgs_cls.values())
        probs = np.array(list(tot_imgs_cls.values()), dtype=float) / sum_class_imgs
        k_cls = len(tot_imgs_cls)
        shannon_norm = float(-np.sum(probs * np.log(probs)) / math.log(k_cls)) if k_cls > 1 else 1.0
        imbalance_imgs = max(tot_imgs_cls.values()) / min(tot_imgs_cls.values())

        tot_boxes_cls: dict[str, int] = {}
        split_boxes: dict[str, int] = {}
        for sp, cls_dict in rep["boxes_per_class"].items():
            split_boxes[sp] = sum(cls_dict.values())
            for c, n in cls_dict.items():
                tot_boxes_cls[c] = tot_boxes_cls.get(c, 0) + n
        total_boxes = sum(tot_boxes_cls.values())
        imbalance_boxes = (max(tot_boxes_cls.values()) / min(tot_boxes_cls.values())) if tot_boxes_cls else np.nan
        return {
            "total_unique_images": total_unique_imgs,
            "sum_class_appearances": sum_class_imgs,
            "multilabel_overlap": sum_class_imgs - total_unique_imgs,
            "split_img_appearances": split_img_appearances,
            "class_images": tot_imgs_cls,
            "imbalance_ratio_images": round(imbalance_imgs, 3),
            "shannon_norm_images": round(shannon_norm, 4),
            "total_boxes": total_boxes,
            "split_boxes": split_boxes,
            "class_boxes": tot_boxes_cls,
            "imbalance_ratio_boxes": round(imbalance_boxes, 3) if not np.isnan(imbalance_boxes) else None,
            "boxes_per_image": round(total_boxes / total_unique_imgs, 3) if total_boxes else 0.0,
        }

    bal_pv = calc_balance(rep_pv)
    bal_pd = calc_balance(rep_pd)
    print(f"[INFO] Balance PlantVillage: {bal_pv}")
    print(f"[INFO] Balance PlantDoc:     {bal_pd}")

    # Construir Tabla 03 (CSV y APA MD) consolidando modelos Colab + prueba pareada 40 épocas
    t3_apa_rows = [
        {
            "Experimento Colab": "yolo26n_plantvillage_classify",
            "Dataset (Real Público)": "PlantVillage (2,152 imgs; 3 clases)",
            "Épocas (CSV/Plan)": f"{m_pv['epochs_csv']} / {m_pv['epochs_planned']}",
            "Validación (Best)": f"Acc@1 = {m_pv['validation']['metrics/accuracy_top1']:.4f}",
            "Test Único (Best)": f"Acc@1 = {m_pv['test']['metrics/accuracy_top1']:.4f}",
            "Dinámica Últ. Épocas (M ± DE)": f"Acc@1 (21–25): {pv_last5['metrics/accuracy_top1'].mean():.4f} ± {pv_last5['metrics/accuracy_top1'].std(ddof=1):.4f}",
            "Peso (MB)": f"{m_pv['weights_size_mb']:.2f}",
        },
        {
            "Experimento Colab": "yolo26n_plantdoc_detect",
            "Dataset (Real Público)": "PlantDoc (219 imgs; 569 cajas; 2 clases)",
            "Épocas (CSV/Plan)": f"{m_26['epochs_csv']} / {m_26['epochs_planned']}",
            "Validación (Best)": (
                f"P={m_26['validation']['metrics/precision(B)']:.4f}, R={m_26['validation']['metrics/recall(B)']:.4f}, "
                f"mAP50={m_26['validation']['metrics/mAP50(B)']:.4f}, mAP50-95={m_26['validation']['metrics/mAP50-95(B)']:.4f}"
            ),
            "Test Único (Best)": (
                f"P={m_26['test']['metrics/precision(B)']:.4f}, R={m_26['test']['metrics/recall(B)']:.4f}, "
                f"mAP50={m_26['test']['metrics/mAP50(B)']:.4f}, mAP50-95={m_26['test']['metrics/mAP50-95(B)']:.4f}"
            ),
            "Dinámica Últ. Épocas (M ± DE)": (
                f"mAP50 (31–40): {pd26_c['metrics/mAP50(B)'].tail(10).mean():.4f} ± {pd26_c['metrics/mAP50(B)'].tail(10).std(ddof=1):.4f}; "
                f"mAP50-95: {pd26_c['metrics/mAP50-95(B)'].tail(10).mean():.4f} ± {pd26_c['metrics/mAP50-95(B)'].tail(10).std(ddof=1):.4f}"
            ),
            "Peso (MB)": f"{m_26['weights_size_mb']:.2f}",
        },
        {
            "Experimento Colab": "yolo11n_plantdoc_detect",
            "Dataset (Real Público)": "PlantDoc (219 imgs; 569 cajas; 2 clases)",
            "Épocas (CSV/Plan)": f"{m_11['epochs_csv']} / {m_11['epochs_planned']}",
            "Validación (Best)": (
                f"P={m_11['validation']['metrics/precision(B)']:.4f}, R={m_11['validation']['metrics/recall(B)']:.4f}, "
                f"mAP50={m_11['validation']['metrics/mAP50(B)']:.4f}, mAP50-95={m_11['validation']['metrics/mAP50-95(B)']:.4f}"
            ),
            "Test Único (Best)": "No ejecutado (test: null)",
            "Dinámica Últ. Épocas (M ± DE)": (
                f"mAP50 (31–40): {pd11_c['metrics/mAP50(B)'].tail(10).mean():.4f} ± {pd11_c['metrics/mAP50(B)'].tail(10).std(ddof=1):.4f}; "
                f"mAP50-95: {pd11_c['metrics/mAP50-95(B)'].tail(10).mean():.4f} ± {pd11_c['metrics/mAP50-95(B)'].tail(10).std(ddof=1):.4f}"
            ),
            "Peso (MB)": f"{m_11['weights_size_mb']:.2f}",
        },
    ]
    df_t3_apa = pd.DataFrame(t3_apa_rows)

    t3_csv_path = TABLAS_DIR / "tabla_03_modelos_vision_colab.csv"
    t3_md_path = TABLAS_DIR / "tabla_03_modelos_vision_colab.md"
    # En el CSV guardamos tanto la comparativa estadística por época como el resumen, o guardamos la comparativa estadística completa en tabla_03_modelos_vision_colab.csv y el resumen en otra sección.
    # Mejor aún: guardamos en tabla_03_modelos_vision_colab.csv las filas de df_colab_comp con columnas clave de val/test incluidas como metadatos o una tabla combinada clara.
    df_colab_comp.to_csv(t3_csv_path, index=False)

    w_map = {r["Metrica"]: r for _, r in df_colab_comp.iterrows()}
    nota_t3 = (
        f"Pilotos reales entrenados en Google Colab GPU (2026-11-04; verificados en data/models/entrenados_colab/verificacion.json). "
        f"Comparativa estadística por época sobre 40 épocas comunes (1–40) en validación de PlantDoc (YOLO26n vs. YOLO11n; prueba pareada de Wilcoxon de rangos con signo, N = 40 pares): "
        f"mAP@0.50: W = {w_map['mAP@0.50']['Wilcoxon_W']:.1f}, Z = {w_map['mAP@0.50']['Wilcoxon_Z']:.2f}, p = {fmt_p_num(w_map['mAP@0.50']['Wilcoxon_p'])}, r = {w_map['mAP@0.50']['Rosenthal_r']:.3f}; "
        f"mAP@0.50:0.95: W = {w_map['mAP@0.50:0.95']['Wilcoxon_W']:.1f}, Z = {w_map['mAP@0.50:0.95']['Wilcoxon_Z']:.2f}, p = {fmt_p_num(w_map['mAP@0.50:0.95']['Wilcoxon_p'])}, r = {w_map['mAP@0.50:0.95']['Rosenthal_r']:.3f}; "
        f"Precision: W = {w_map['Precision']['Wilcoxon_W']:.1f}, Z = {w_map['Precision']['Wilcoxon_Z']:.2f}, p = {fmt_p_num(w_map['Precision']['Wilcoxon_p'])}, r = {w_map['Precision']['Rosenthal_r']:.3f}; "
        f"Recall: W = {w_map['Recall']['Wilcoxon_W']:.1f}, Z = {w_map['Recall']['Wilcoxon_Z']:.2f}, p = {fmt_p_num(w_map['Recall']['Wilcoxon_p'])}, r = {w_map['Recall']['Rosenthal_r']:.3f}. "
        f"Esta prueba pareada evalúa la dinámica de convergencia en validación (no equivale a inferencia sobre imágenes independientes de prueba); "
        f"el test único independiente de YOLO26n (n = 33 imágenes) obtuvo mAP@0.50 = 0.4926, mAP@0.50:0.95 = 0.3216, Precision = 0.4551, Recall = 0.5985. "
        f"Las cajas de PlantDoc delimitan hojas completas (no lesiones) y ambos datasets públicos no constituyen validación en el invernadero de La Paz."
    )
    escribir_md_apa(
        t3_md_path,
        "Tabla 3",
        "Resultados reales de modelos de visión por computadora entrenados en Google Colab sobre datasets públicos PlantVillage y PlantDoc",
        df_t3_apa,
        nota_t3,
    )
    print(f"[OK] Exportada Tabla 03: {t3_csv_path} y {t3_md_path}")

    # Figura 3: fig_est_curvas_colab_plantdoc.png
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.5), dpi=300, sharex=True)
    test_26 = m_26["test"]

    for ax, (col, nom) in zip(axes.flat, metricas_det):
        ax.plot(pd26_res["epoch"], pd26_res[col], color="#1B9E77", linewidth=2.0, marker="o", markersize=3, label="YOLO26n (Val, 40 ép.)")
        ax.plot(pd11_res["epoch"], pd11_res[col], color="#D95F02", linewidth=1.8, linestyle="--", marker="s", markersize=2.8, label="YOLO11n (Val, 43 ép.)")
        ax.axhline(test_26[col], color="#2B6CB0", linestyle=":", linewidth=1.5, label=f"YOLO26n Test único ({test_26[col]:.4f})")
        ax.axvline(40, color="#718096", linestyle="-.", linewidth=1.1, alpha=0.8)

        wr = w_map[nom]
        ax.set_title(f"{nom} en Validación por Época (PlantDoc)")
        ax.set_ylabel(nom)
        ax.set_ylim(0.0, 0.90)
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend(loc="lower right", fontsize=7.5)
        ax.text(
            0.03, 0.95,
            f"Wilcoxon 40 ép.: W = {wr['Wilcoxon_W']:.0f}, p = {fmt_p_num(wr['Wilcoxon_p'])}\n"
            f"r = {wr['Rosenthal_r']:.3f} | Mdn(Δ) = {wr['Diff_Mdn']:+.4f}",
            transform=ax.transAxes, va="top", fontsize=7.8,
            bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "alpha": 0.9, "edgecolor": "#CBD5E0"},
        )

    axes[1, 0].set_xlabel("Época de entrenamiento")
    axes[1, 1].set_xlabel("Época de entrenamiento")
    fig.suptitle(
        "Dinámica de Convergencia en Validación (Colab Real): YOLO26n vs. YOLO11n en PlantDoc (n = 219 imgs)",
        fontsize=12, fontweight="bold", y=0.98
    )
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    fig3_path = FIGURAS_DIR / "fig_est_curvas_colab_plantdoc.png"
    plt.savefig(fig3_path, dpi=300)
    plt.close(fig)
    print(f"[OK] Guardada figura: {fig3_path}")

    # Figura 4: fig_est_distribucion_datasets_reales.png
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.2), dpi=300)

    # Panel A: PlantVillage (2152 imgs)
    pv_classes = ["tizon_tardio", "tizon_temprano", "hoja_sana"]
    pv_labels = ["Tizón tardío", "Tizón temprano", "Hoja sana"]
    splits = ["train", "val", "test"]
    split_colors = {"train": "#2B6CB0", "val": "#ED8936", "test": "#38A169"}
    x_pv = np.arange(len(pv_classes))
    bottom = np.zeros(len(pv_classes))
    for sp in splits:
        vals = np.array([rep_pv["images_per_class"][sp][c] for c in pv_classes])
        ax1.bar(x_pv, vals, bottom=bottom, color=split_colors[sp], label=f"{sp.capitalize()} ({sum(vals)})", width=0.55, edgecolor="white")
        for i, v in enumerate(vals):
            if v >= 40:
                ax1.text(i, bottom[i] + v / 2, str(v), ha="center", va="center", color="white", fontsize=8.5, fontweight="bold")
        bottom += vals
    for i, tot in enumerate(bottom):
        ax1.text(i, tot + 18, f"Total: {int(tot)}\n({tot/bal_pv['total_unique_images']:.1%})", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
    ax1.set_xticks(x_pv)
    ax1.set_xticklabels(pv_labels)
    ax1.set_ylim(0, 1180)
    ax1.set_ylabel("Número de imágenes")
    ax1.set_title(f"(a) PlantVillage Clasificación (N = {bal_pv['total_unique_images']:,} imgs)\nRazón máx/mín = {bal_pv['imbalance_ratio_images']:.2f}:1 | H_norm = {bal_pv['shannon_norm_images']:.3f}")
    ax1.grid(True, axis="y", linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right")

    # Panel B: PlantDoc (219 imgs únicas, 569 cajas)
    pd_classes = ["tizon_tardio", "tizon_temprano"]
    pd_labels = ["Tizón tardío", "Tizón temprano"]
    x_pd = np.arange(len(pd_classes))
    w_bar = 0.34

    bottom_img = np.zeros(len(pd_classes))
    bottom_box = np.zeros(len(pd_classes))
    for sp in splits:
        vals_img = np.array([rep_pd["images_per_class"][sp][c] for c in pd_classes])
        vals_box = np.array([rep_pd["boxes_per_class"][sp][c] for c in pd_classes])
        ax2.bar(x_pd - w_bar / 2 - 0.02, vals_img, bottom=bottom_img, color=split_colors[sp], width=w_bar, edgecolor="white", alpha=0.9, label=f"Imgs {sp}" if sp == "train" else None)
        ax2.bar(x_pd + w_bar / 2 + 0.02, vals_box, bottom=bottom_box, color=split_colors[sp], width=w_bar, edgecolor="white", hatch="///", alpha=0.75)
        bottom_img += vals_img
        bottom_box += vals_box

    for i in range(len(pd_classes)):
        ax2.text(x_pd[i] - w_bar / 2 - 0.02, bottom_img[i] + 6, f"Pres. img:\n{int(bottom_img[i])}", ha="center", va="bottom", fontsize=8.2, fontweight="bold")
        ax2.text(x_pd[i] + w_bar / 2 + 0.02, bottom_box[i] + 6, f"Cajas:\n{int(bottom_box[i])}", ha="center", va="bottom", fontsize=8.2, fontweight="bold")

    ax2.set_xticks(x_pd)
    ax2.set_xticklabels(pd_labels)
    ax2.set_ylim(0, 380)
    ax2.set_ylabel("Cantidad (presencias en imagen / cajas anotadas)")
    ax2.set_title(
        f"(b) PlantDoc Detección (N = {bal_pd['total_unique_images']} imgs únicas, {bal_pd['total_boxes']} cajas)\n"
        f"Promedio = {bal_pd['boxes_per_image']:.2f} cajas/img | Razón cajas = {bal_pd['imbalance_ratio_boxes']:.2f}:1"
    )
    ax2.grid(True, axis="y", linestyle=":", alpha=0.6)

    # Leyenda manual clara para barras sólidas vs rayadas y splits
    from matplotlib.patches import Patch
    handles_pd = [
        Patch(facecolor="#2B6CB0", label="Train (70%)"),
        Patch(facecolor="#ED8936", label="Val (15%)"),
        Patch(facecolor="#38A169", label="Test (15%)"),
        Patch(facecolor="#A0AEC0", edgecolor="black", label="Imágenes (izq.)"),
        Patch(facecolor="#A0AEC0", edgecolor="black", hatch="///", label="Cajas hoja completa (der.)"),
    ]
    ax2.legend(handles=handles_pd, loc="upper left", fontsize=7.8)

    fig.suptitle("Balance de Clases y Partición Sin Fuga de Hash en Datasets Públicos Curados", fontsize=12, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig4_path = FIGURAS_DIR / "fig_est_distribucion_datasets_reales.png"
    plt.savefig(fig4_path, dpi=300)
    plt.close(fig)
    print(f"[OK] Guardada figura: {fig4_path}")

    return df_colab_comp, df_t3_apa, bal_pv, bal_pd


# ==============================================================================
# BLOQUE D: MODELOS DE RIESGO FASE 5 Y VERIFICACION DE SOFTWARE/FIRMWARE
# ==============================================================================
def analizar_riesgo_fase5(df_agro: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    print("\n" + "=" * 90)
    print("D. ANALISIS DE MODELOS DE RIESGO FITOPATOLOGICO (FASE 5) Y ARTEFACTOS REALES")
    print("=" * 90)

    riesgo_path = BASE_DIR / "data" / "synthetic" / "metricas_experimentos_fase5_riesgo.csv"
    df_riesgo = pd.read_csv(riesgo_path)

    # Verificar partición temporal estricta usada en scripts/ejecutar_fase5_riesgo_fusion.py
    n_train, n_val = 1296, 432
    df_tr = df_agro.iloc[:n_train]
    df_va = df_agro.iloc[n_train:n_train + n_val]
    df_te = df_agro.iloc[n_train + n_val:]

    split_info = {
        "train": {"n": len(df_tr), "pos": int(df_tr["riesgo_infeccion_gt"].sum()), "pct": float(df_tr["riesgo_infeccion_gt"].mean())},
        "val": {"n": len(df_va), "pos": int(df_va["riesgo_infeccion_gt"].sum()), "pct": float(df_va["riesgo_infeccion_gt"].mean())},
        "test": {"n": len(df_te), "pos": int(df_te["riesgo_infeccion_gt"].sum()), "pct": float(df_te["riesgo_infeccion_gt"].mean())},
        "concordancia_bu14_gt": float(np.mean((df_agro["blight_units_7d"] >= 14.0).astype(int) == df_agro["riesgo_infeccion_gt"])),
    }
    print(f"[INFO] Partición temporal Fase 5: Train={split_info['train']}, Val={split_info['val']}, Test={split_info['test']}")
    print(f"[INFO] Concordancia exacta (blight_units_7d >= 14.0 == riesgo_infeccion_gt): {split_info['concordancia_bu14_gt']:.4%}")

    # Calcular comparativa relativa respecto a XGBoost (Ganador ML) y Random Forest / SVM / LSTM
    ml_only = df_riesgo[~df_riesgo["Modelo"].str.contains("BlightManager")].copy()
    xgb_row = df_riesgo[df_riesgo["Modelo"].str.contains("XGBoost")].iloc[0]

    df_t4_csv = df_riesgo.copy()
    df_t4_csv["Delta_Brier_vs_XGBoost"] = (df_t4_csv["Brier Score"] - xgb_row["Brier Score"]).round(4)
    df_t4_csv["Delta_AUC_vs_XGBoost"] = (df_t4_csv["ROC-AUC"] - xgb_row["ROC-AUC"]).round(4)
    df_t4_csv["Tipo_Evidencia"] = np.where(
        df_t4_csv["Modelo"].str.contains("BlightManager"),
        "Línea base determinística (usa blight_units_7d)",
        "ML sobre 24 variables telemetría (sin blight_units_7d)",
    )

    df_t4_apa = df_t4_csv[[
        "Modelo", "ROC-AUC", "PR-AUC", "Brier Score", "F1-Score", "Latencia CPU (ms)", "Seleccionado"
    ]].copy()
    print("\n--- Tabla 04 (Modelos de Riesgo Fase 5) ---")
    print(df_t4_apa.to_string(index=False))

    t4_csv_path = TABLAS_DIR / "tabla_04_riesgo_fitopatologico.csv"
    t4_md_path = TABLAS_DIR / "tabla_04_riesgo_fitopatologico.md"
    df_t4_csv.to_csv(t4_csv_path, index=False)

    nota_t4 = (
        f"Evaluación sobre partición temporal estricta de la simulación agroclimática de 90 días "
        f"(Train = {split_info['train']['n']} h [{split_info['train']['pos']} pos., {split_info['train']['pct']:.1%}]; "
        f"Val = {split_info['val']['n']} h [{split_info['val']['pos']} pos., {split_info['val']['pct']:.1%}]; "
        f"Test = {split_info['test']['n']} h [{split_info['test']['pos']} pos., {split_info['test']['pct']:.1%}]). "
        f"BlightManager (Wallin 1962) obtiene ROC-AUC = 1.0000 y PR-AUC = 1.0000 porque evalúa directamente blight_units_7d, "
        f"variable con la cual se definió la etiqueta objetivo (riesgo_infeccion_gt = 1 si blight_units_7d >= 14.0; concordancia = 100.0%). "
        f"Los modelos de aprendizaje automático (Random Forest, XGBoost, SVM RBF y LSTM) predicen el riesgo usando exclusivamente "
        f"24 variables de telemetría y ventanas móviles (sin incluir blight_units_7d). Entre los modelos ML, XGBoost (calibración isotónica) "
        f"obtiene el menor Brier Score ({xgb_row['Brier Score']:.4f}) con latencia de {xgb_row['Latencia CPU (ms)']:.3f} ms en CPU, "
        f"mientras SVM RBF logra mayor discriminación ROC-AUC ({ml_only['ROC-AUC'].max():.4f}) y PR-AUC ({ml_only['PR-AUC'].max():.4f})."
    )
    escribir_md_apa(
        t4_md_path,
        "Tabla 4",
        "Evaluación comparativa de modelos de riesgo fitopatológico en conjunto de prueba temporal simulado (n = 432 horas)",
        df_t4_apa,
        nota_t4,
    )
    print(f"[OK] Exportada Tabla 04: {t4_csv_path} y {t4_md_path}")

    # Verificación directa de software / firmware en el repositorio (sin inventar)
    fw_bin = BASE_DIR / "firmware" / "esp32_control" / ".pio" / "build" / "esp32dev" / "firmware.bin"
    fw_size = fw_bin.stat().st_size if fw_bin.exists() else None
    db_path = BASE_DIR / "data" / "invernadero_relacional.db"
    db_counts = {}
    if db_path.exists():
        con = sqlite3.connect(db_path)
        for tbl in ["nodos_sensores", "detecciones_vision", "eventos_alarmas", "auditoria_control_pid", "experimentos_ensayos"]:
            db_counts[tbl] = int(con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0])
        con.close()

    e123_path = BASE_DIR / "data" / "synthetic" / "metricas_experimentos_e1_e2_e3.csv"
    df_e123 = pd.read_csv(e123_path)

    verif_hw_sw = {
        "firmware_bin_bytes": fw_size,
        "firmware_bin_kb": round(fw_size / 1024, 2) if fw_size else None,
        "sqlite_counts": db_counts,
        "e1_e2_e3_referencia_filas": len(df_e123),
    }
    print(f"[INFO] Verificación artefactos reales: firmware.bin = {fw_size} bytes ({verif_hw_sw['firmware_bin_kb']} KiB), SQLite = {db_counts}")
    return df_t4_csv, df_t4_apa, {"split": split_info, "artefactos": verif_hw_sw}


def main() -> None:
    print("=" * 90)
    print("EJECUCION INTEGRAL - AGENTE 5 (ANALISIS ESTADISTICO DE TESIS)")
    print("=" * 90)
    df_agro, _, _, _ = analizar_agroclimatico()
    analizar_fopdt_pid()
    analizar_colab_y_datasets()
    analizar_riesgo_fase5(df_agro)
    print("\n[OK] Pipeline estadistico completado exitosamente.")


if __name__ == "__main__":
    main()
