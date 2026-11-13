#!/usr/bin/env python3
"""Baseline technical audit & CPU benchmark script (read-only on project/thesis)."""

import ast
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import psutil

ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "mejoras" / "benchmarks" / "diagnostico_baseline.json"


def measure_codebase():
    areas = {
        "server": ROOT / "server",
        "web": ROOT / "web",
        "scripts": ROOT / "scripts",
        "firmware": ROOT / "firmware" / "esp32_control",
        "tests": ROOT / "tests",
        "config": ROOT / "config",
    }
    stats = {}
    hardcoded_paths = []
    csrf_exempt_locs = []
    long_functions = []
    async_blocking_suspects = []
    secret_patterns = []

    secret_re = re.compile(
        r"(PASSWORD|SECRET_KEY|TOKEN|WIFI_PASSWORD|MQTT_PASSWORD)\s*[:=]\s*['\"][^'\"]+['\"]",
        re.IGNORECASE,
    )
    blocking_calls = {"open", "sleep", "copyfileobj", "copy2", "imread", "imwrite"}

    for name, path in areas.items():
        files = []
        total_lines = 0
        non_empty_lines = 0
        for p in path.rglob("*"):
            if not p.is_file():
                continue
            if any(part in p.parts for part in (".pio", "__pycache__", ".pytest_cache", "staticfiles")):
                continue
            if p.suffix in {".py", ".cpp", ".h", ".sql", ".sh", ".yml", ".yaml", ".conf", ".ini", ".html", ".js", ".css"}:
                files.append(p)
                text = p.read_text(encoding="utf-8", errors="replace")
                lines = text.splitlines()
                total_lines += len(lines)
                non_empty_lines += sum(1 for ln in lines if ln.strip())

                rel = str(p.relative_to(ROOT))
                if "/home/rodrigo" in text and p.suffix in {".py", ".sh", ".service", ".json"}:
                    for idx, ln in enumerate(lines, 1):
                        if "/home/rodrigo" in ln:
                            hardcoded_paths.append(f"{rel}:{idx}")
                if "@csrf_exempt" in text:
                    for idx, ln in enumerate(lines, 1):
                        if "@csrf_exempt" in ln:
                            csrf_exempt_locs.append(f"{rel}:{idx}")
                for idx, ln in enumerate(lines, 1):
                    if secret_re.search(ln) and not ln.strip().startswith("#"):
                        secret_patterns.append(f"{rel}:{idx}")

                if p.suffix == ".py":
                    try:
                        tree = ast.parse(text)
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                fn_len = (node.end_lineno or node.lineno) - node.lineno + 1
                                if fn_len > 60:
                                    long_functions.append({
                                        "file": rel,
                                        "function": node.name,
                                        "lines": fn_len,
                                        "start_line": node.lineno,
                                    })
                                if isinstance(node, ast.AsyncFunctionDef):
                                    for sub in ast.walk(node):
                                        if isinstance(sub, ast.Call):
                                            fn_name = ""
                                            if isinstance(sub.func, ast.Name):
                                                fn_name = sub.func.id
                                            elif isinstance(sub.func, ast.Attribute):
                                                fn_name = sub.func.attr
                                            if fn_name in blocking_calls:
                                                async_blocking_suspects.append(f"{rel}:{sub.lineno} ({node.name} -> {fn_name})")
                    except SyntaxError:
                        pass

        stats[name] = {
            "files": len(files),
            "total_lines": total_lines,
            "non_empty_lines": non_empty_lines,
        }

    # Flake8 C901 complexity items
    c901_proc = subprocess.run(
        [
            str(ROOT / ".venv" / "bin" / "flake8"),
            ".",
            "--select=C901",
            "--max-complexity=10",
            "--exclude=.venv,backups,data,fases,mejoras,tesis,thesis",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    c901_items = [ln.strip() for ln in c901_proc.stdout.splitlines() if ln.strip()]

    return {
        "loc_by_area": stats,
        "hardcoded_home_paths": hardcoded_paths,
        "csrf_exempt_count": len(csrf_exempt_locs),
        "csrf_exempt_locations": csrf_exempt_locs,
        "long_functions_gt_60_lines": sorted(long_functions, key=lambda x: -x["lines"]),
        "async_blocking_suspects": async_blocking_suspects,
        "secret_literal_matches": secret_patterns,
        "flake8_c901_gt_10": c901_items,
    }


def measure_storage_and_sqlite():
    def dir_size_mb(p: Path):
        if not p.exists():
            return 0.0
        if p.is_file():
            return round(p.stat().st_size / (1024 * 1024), 3)
        total = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        return round(total / (1024 * 1024), 3)

    db_path = ROOT / "data" / "invernadero_relacional.db"
    db_info = {"exists": db_path.is_file(), "size_mb": dir_size_mb(db_path)}
    if db_path.is_file():
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = conn.cursor()
        db_info["journal_mode"] = cur.execute("PRAGMA journal_mode;").fetchone()[0]
        db_info["synchronous"] = cur.execute("PRAGMA synchronous;").fetchone()[0]
        db_info["page_size"] = cur.execute("PRAGMA page_size;").fetchone()[0]
        db_info["page_count"] = cur.execute("PRAGMA page_count;").fetchone()[0]
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;").fetchall()]
        db_info["tables"] = {}
        for t in tables:
            db_info["tables"][t] = cur.execute(f"SELECT COUNT(*) FROM {t};").fetchone()[0]
        indexes = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;").fetchall()]
        db_info["indexes"] = indexes
        if "experimentos_ensayos" in tables:
            dups = cur.execute(
                "SELECT codigo_experimento, COUNT(*) FROM experimentos_ensayos GROUP BY codigo_experimento HAVING COUNT(*) > 1;"
            ).fetchall()
            db_info["experimentos_duplicates"] = [{"codigo": r[0], "count": r[1]} for r in dups]
        conn.close()

    return {
        "sizes_mb": {
            "data_total": dir_size_mb(ROOT / "data"),
            "data_models": dir_size_mb(ROOT / "data" / "models"),
            "data_processed": dir_size_mb(ROOT / "data" / "processed"),
            "data_raw": dir_size_mb(ROOT / "data" / "raw"),
            "data_synthetic": dir_size_mb(ROOT / "data" / "synthetic"),
            "backups": dir_size_mb(ROOT / "backups"),
            "notebooks": dir_size_mb(ROOT / "notebooks"),
            "firmware_bin_bytes": (ROOT / "firmware" / "esp32_control" / ".pio" / "build" / "esp32dev" / "firmware.bin").stat().st_size
            if (ROOT / "firmware" / "esp32_control" / ".pio" / "build" / "esp32dev" / "firmware.bin").is_file() else 0,
        },
        "sqlite": db_info,
    }


def benchmark_vision_and_apis():
    proc = psutil.Process(os.getpid())
    with tempfile.TemporaryDirectory(prefix="iot-audit-") as tmp:
        tmp_path = Path(tmp)
        db_file = tmp_path / "audit.db"
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_file) as conn:
            conn.executescript((ROOT / "server/app/models/schemas.sql").read_text())

        os.environ.update(
            SQLITE_DB_PATH=str(db_file),
            UPLOAD_DIR=str(upload_dir),
            VISION_DEMO_MODE="false",
            TELEGRAM_BOT_TOKEN="",
            TELEGRAM_CHAT_ID="",
            MQTT_BROKER_HOST="127.0.0.1",
        )
        sys.path.insert(0, str(ROOT))
        sys.path.insert(0, str(ROOT / "web"))

        # Disable MQTT network connect during benchmark
        from server.app.services.mqtt_client import mqtt_service
        mqtt_service.iniciar = lambda: None
        mqtt_service.publicar = lambda *a, **kw: False

        # Vision cold load + warm inference
        from server.app.services.vision_service import (
            VisionInferenceService,
            CATALOGO_MODELOS_COLAB,
            procesar_trampa_amarilla_colorimetria,
        )

        img_detect_src = ROOT / "data/processed/papa_plantdoc_yolo/images/test/11c98ab2be295c0cfebf03fc.jpg"
        img_cls_src = ROOT / "data/processed/papa_plantvillage_clasificacion/test/hoja_sana/0df518de395ebcac6b87894d.jpg"
        img_trap_src = ROOT / "data/raw/trampas/pulgon/trampa_pulgon_001.ppm"

        img_detect = tmp_path / "detect.jpg"
        img_cls = tmp_path / "cls.jpg"
        img_trap = tmp_path / "trap.ppm"
        shutil.copy2(img_detect_src, img_detect)
        shutil.copy2(img_cls_src, img_cls)
        shutil.copy2(img_trap_src, img_trap)

        vision_bench = {}
        for mid, info in CATALOGO_MODELOS_COLAB.items():
            wpath = Path(info["weights_path"])
            rss_before = proc.memory_info().rss / (1024 * 1024)
            t0 = time.perf_counter()
            svc = VisionInferenceService(wpath)
            cold_load_ms = (time.perf_counter() - t0) * 1000
            rss_after = proc.memory_info().rss / (1024 * 1024)

            target_img = img_cls if info["tarea"] == "classify" else img_detect
            # Warmup 1 + 5 timed runs
            _ = svc.procesar_imagen(str(target_img), tipo_origen="HOJA_FOLLAJE", usar_sahi=False)
            times = []
            for _ in range(5):
                t1 = time.perf_counter()
                res = svc.procesar_imagen(str(target_img), tipo_origen="HOJA_FOLLAJE", usar_sahi=False)
                times.append((time.perf_counter() - t1) * 1000)

            entry = {
                "weights_size_mb": round(wpath.stat().st_size / (1024 * 1024), 3),
                "cold_load_ms": round(cold_load_ms, 2),
                "rss_delta_mb": round(rss_after - rss_before, 2),
                "warm_mean_ms": round(float(np.mean(times)), 2),
                "warm_p50_ms": round(float(np.percentile(times, 50)), 2),
                "warm_p95_ms": round(float(np.percentile(times, 95)), 2),
                "warm_min_ms": round(float(np.min(times)), 2),
                "warm_max_ms": round(float(np.max(times)), 2),
                "sample_output_class": res["clase_detectada"],
                "sample_conf": res["confianza"],
            }
            if mid == "yolo26n_plantdoc_detect" and svc.sahi_model is not None:
                sahi_times = []
                for _ in range(3):
                    t1 = time.perf_counter()
                    _ = svc.procesar_imagen(str(img_detect), tipo_origen="HOJA_FOLLAJE", usar_sahi=True)
                    sahi_times.append((time.perf_counter() - t1) * 1000)
                entry["sahi_320_mean_ms"] = round(float(np.mean(sahi_times)), 2)
                entry["sahi_320_max_ms"] = round(float(np.max(sahi_times)), 2)
            vision_bench[mid] = entry

        # HSV Trap heuristic benchmark
        hsv_times = []
        for _ in range(5):
            t1 = time.perf_counter()
            res_hsv = procesar_trampa_amarilla_colorimetria(str(img_trap))
            hsv_times.append((time.perf_counter() - t1) * 1000)
        vision_bench["heuristica_trampa_hsv"] = {
            "warm_mean_ms": round(float(np.mean(hsv_times)), 2),
            "warm_p95_ms": round(float(np.percentile(hsv_times, 95)), 2),
            "sample_count": res_hsv["conteo_insectos"],
        }

        # FastAPI TestClient endpoints
        from fastapi.testclient import TestClient
        from server.app.main import app
        client = TestClient(app)

        fastapi_bench = {}
        for name, method, url, kwargs in [
            ("GET /", "get", "/", {}),
            ("GET /api/v1/health", "get", "/api/v1/health", {}),
            ("GET /api/v1/vision/modelos", "get", "/api/v1/vision/modelos", {}),
            ("GET /api/v1/vision/historial", "get", "/api/v1/vision/historial?limit=20", {}),
            ("GET /api/v1/alertas", "get", "/api/v1/alertas?limit=20", {}),
            ("POST /api/v1/control/setpoints", "post", "/api/v1/control/setpoints", {
                "json": {"sp_temperatura": 19.0, "sp_humedad": 72.0, "usuario_origen": "AUDIT_BENCH"}
            }),
        ]:
            ts = []
            for _ in range(10):
                t1 = time.perf_counter()
                r = getattr(client, method)(url, **kwargs)
                ts.append((time.perf_counter() - t1) * 1000)
            fastapi_bench[name] = {
                "status": r.status_code,
                "mean_ms": round(float(np.mean(ts)), 2),
                "p95_ms": round(float(np.percentile(ts, 95)), 2),
            }

        # FastAPI real vision inference endpoint
        raw_bytes = img_detect.read_bytes()
        inf_times = []
        for _ in range(3):
            t1 = time.perf_counter()
            r = client.post(
                "/api/v1/vision/inferir",
                files={"imagen": ("test_leaf.jpg", raw_bytes, "image/jpeg")},
                data={"nodo_camara": "cam_audit", "tipo_origen": "HOJA_FOLLAJE", "usar_sahi": "false"},
            )
            inf_times.append((time.perf_counter() - t1) * 1000)
        fastapi_bench["POST /api/v1/vision/inferir (yolo26n_detect)"] = {
            "status": r.status_code,
            "mean_ms": round(float(np.mean(inf_times)), 2),
            "p95_ms": round(float(np.percentile(inf_times, 95)), 2),
        }

        # Django Client endpoints
        os.environ["DJANGO_SETTINGS_MODULE"] = "invernadero_web.settings"
        from django.conf import settings as django_settings
        django_settings.DATABASES["default"]["NAME"] = str(db_file)
        django_settings.MEDIA_ROOT = str(upload_dir)
        import django
        django.setup()
        from scripts import seed_experiments
        seed_experiments.DB_PATH = db_file
        seed_experiments.poblar_ensayos()
        from django.test import Client as DjangoClient
        dj = DjangoClient()

        django_bench = {}
        for url in ["/", "/control-pid/", "/vision/", "/gemelo-digital/", "/experimentos/", "/api/telemetria/", "/api/autotune/"]:
            ts = []
            for _ in range(5):
                t1 = time.perf_counter()
                resp = dj.get(url)
                ts.append((time.perf_counter() - t1) * 1000)
            django_bench[f"GET {url}"] = {
                "status": resp.status_code,
                "mean_ms": round(float(np.mean(ts)), 2),
                "p95_ms": round(float(np.percentile(ts, 95)), 2),
                "bytes": len(resp.content),
            }

        from django.db import connections
        connections.close_all()

        return {
            "vision_cpu": vision_bench,
            "fastapi_endpoints": fastapi_bench,
            "django_endpoints": django_bench,
            "rss_peak_mb": round(proc.memory_info().rss / (1024 * 1024), 2),
        }


def benchmark_ml_and_sim():
    sys.path.insert(0, str(ROOT))
    from scripts.generar_dataset_agroclimatico import generar_dataset_invernadero
    from scripts.ejecutar_fase5_riesgo_fusion import ingenieria_caracteristicas
    from sklearn.preprocessing import StandardScaler
    from sklearn.isotonic import IsotonicRegression
    from sklearn.metrics import roc_auc_score, brier_score_loss
    import xgboost as xgb
    import shap

    t0 = time.perf_counter()
    df_syn = generar_dataset_invernadero(dias=90, seed=42)
    gen_ms = (time.perf_counter() - t0) * 1000

    t1 = time.perf_counter()
    df_feat = ingenieria_caracteristicas(df_syn)
    feat_ms = (time.perf_counter() - t1) * 1000

    feature_cols = [
        'temp_interior_c', 'hum_interior_pct', 'vpd_kpa', 'punto_rocio_c',
        'depresion_rocio_c', 'lwh_continuo_horas', 'grados_hora',
        'temp_in_media_6h', 'temp_in_media_24h', 'temp_in_std_24h', 'oscilacion_termica_24h',
        'hum_in_media_6h', 'hum_in_media_24h', 'hum_in_max_24h', 'hum_in_std_24h',
        'vpd_media_6h', 'vpd_media_24h', 'vpd_min_24h',
        'lwh_max_24h', 'lwh_suma_48h',
        'delta_vpd_1h', 'delta_temp_1h', 'delta_hum_1h', 'grados_hora_24h'
    ]
    n_train, n_val = 1296, 432
    scaler = StandardScaler()
    X_tr = scaler.fit_transform(df_feat.iloc[:n_train][feature_cols].values)
    y_tr = df_feat.iloc[:n_train]['riesgo_infeccion_gt'].values
    X_va = scaler.transform(df_feat.iloc[n_train:n_train+n_val][feature_cols].values)
    y_va = df_feat.iloc[n_train:n_train+n_val]['riesgo_infeccion_gt'].values
    X_te = scaler.transform(df_feat.iloc[n_train+n_val:][feature_cols].values)
    y_te = df_feat.iloc[n_train+n_val:]['riesgo_infeccion_gt'].values

    pos_weight = float((len(y_tr) - y_tr.sum()) / max(1, y_tr.sum()))
    t2 = time.perf_counter()
    model = xgb.XGBClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.05,
        scale_pos_weight=pos_weight, eval_metric='logloss', random_state=42
    )
    model.fit(X_tr, y_tr)
    iso = IsotonicRegression(out_of_bounds='clip')
    iso.fit(model.predict_proba(X_va)[:, 1], y_va)
    xgb_train_ms = (time.perf_counter() - t2) * 1000

    t3 = time.perf_counter()
    probs = iso.predict(model.predict_proba(X_te)[:, 1])
    xgb_infer_batch_ms = (time.perf_counter() - t3) * 1000

    t4 = time.perf_counter()
    explainer = shap.TreeExplainer(model)
    _ = explainer.shap_values(X_te)
    shap_ms = (time.perf_counter() - t4) * 1000

    return {
        "dataset_rows": len(df_syn),
        "dataset_gen_90d_ms": round(gen_ms, 2),
        "feature_eng_24cols_ms": round(feat_ms, 2),
        "xgb_train_calibrate_ms": round(xgb_train_ms, 2),
        "xgb_infer_432_rows_ms": round(xgb_infer_batch_ms, 3),
        "shap_treeexplainer_432_rows_ms": round(shap_ms, 2),
        "xgb_test_roc_auc": round(float(roc_auc_score(y_te, probs)), 4),
        "xgb_test_brier": round(float(brier_score_loss(y_te, probs)), 4),
    }


def main():
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "environment": {
            "python": sys.version.split()[0],
            "cpu_count_logical": os.cpu_count(),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "ram_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        },
        "codebase": measure_codebase(),
        "storage_and_sqlite": measure_storage_and_sqlite(),
        "ml_and_simulation": benchmark_ml_and_sim(),
        "runtime_benchmarks": benchmark_vision_and_apis(),
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Baseline written to {OUT_JSON}")


if __name__ == "__main__":
    main()
