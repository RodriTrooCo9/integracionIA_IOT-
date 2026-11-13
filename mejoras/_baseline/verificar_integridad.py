#!/usr/bin/env python3
"""
Verificador reproducible de integridad de la línea base de la tesis (FASE 0).
Comprueba:
1. Que el tag Git `tesis-v1` exista y apunte al commit base esperado.
2. Que los 77 archivos protegidos coincidan exactamente en tamaño y SHA-256 con baseline_sha256.json.
3. Que no existan archivos nuevos o faltantes en /tesis/.
4. Que la copia inmutable en mejoras/_baseline/tesis_snapshot/ coincida byte a byte con /tesis/.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/rodrigo/Desktop/IOTtesis")
BASELINE_JSON = ROOT / "mejoras" / "_baseline" / "baseline_sha256.json"
SNAPSHOT_DIR = ROOT / "mejoras" / "_baseline" / "tesis_snapshot"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not BASELINE_JSON.is_file():
        print(f"[FAIL] Falta manifiesto base: {BASELINE_JSON}")
        return 1

    baseline = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    errors = []

    # 1. Verificar tag Git tesis-v1
    expected_head = baseline["git_head"]
    res = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--verify", "tesis-v1"],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        errors.append("Tag Git 'tesis-v1' no existe.")
    elif res.stdout.strip() != expected_head:
        errors.append(f"Tag 'tesis-v1' apunta a {res.stdout.strip()}, se esperaba {expected_head}.")

    # 2. Verificar SHA-256 y tamaño de los archivos registrados
    expected_files = baseline["files"]
    for rel, meta in expected_files.items():
        target = ROOT / rel
        if not target.is_file():
            errors.append(f"Archivo faltante: {rel}")
            continue
        actual_bytes = target.stat().st_size
        actual_sha = sha256_file(target)
        if actual_bytes != meta["bytes"] or actual_sha != meta["sha256"]:
            errors.append(
                f"Archivo modificado: {rel} (esperado {meta['bytes']}B / {meta['sha256'][:12]}, "
                f"actual {actual_bytes}B / {actual_sha[:12]})"
            )

    # 3. Verificar que no haya archivos agregados en /tesis/
    expected_tesis = {k for k in expected_files if k.startswith("tesis/")}
    actual_tesis = {str(p.relative_to(ROOT)) for p in (ROOT / "tesis").rglob("*") if p.is_file()}
    extra_tesis = sorted(actual_tesis - expected_tesis)
    if extra_tesis:
        errors.append(f"Archivos no autorizados en /tesis/: {extra_tesis}")

    # 4. Verificar snapshot inmutable contra /tesis/
    for p in sorted(SNAPSHOT_DIR.rglob("*")):
        if p.is_file():
            rel_snapshot = p.relative_to(SNAPSHOT_DIR)
            orig = ROOT / "tesis" / rel_snapshot
            if not orig.is_file():
                errors.append(f"Original faltante respecto al snapshot: tesis/{rel_snapshot}")
            elif sha256_file(p) != sha256_file(orig):
                errors.append(f"Discrepancia snapshot vs original en tesis/{rel_snapshot}")

    if errors:
        print(f"[FAIL] Se detectaron {len(errors)} violaciones de integridad:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(
        f"[OK] Integridad 100% verificada: {len(expected_files)}/{len(expected_files)} archivos SHA-256 intactos, "
        f"tag tesis-v1={expected_head[:7]}, snapshot=/tesis/ idénticos."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
