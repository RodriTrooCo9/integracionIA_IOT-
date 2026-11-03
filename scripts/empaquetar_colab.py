#!/usr/bin/env python3
"""Build a private-data-free Colab bundle with prepared real datasets.

This creates a local archive only; it does not upload to Google Drive or train.
"""
import argparse
import json
from pathlib import Path
import sys
import zipfile

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from scripts.flujo_colab import DATASETS, NOTEBOOKS, inspect_progress


REQUIRED = ['requirements-datasets.txt', 'requirements-vision.txt',
            'scripts/preparar_datasets_reales.py', 'scripts/entrenar_yolo26.py', 'scripts/flujo_colab.py',
            'scripts/iniciar_colab.py', 'scripts/reparar_dataset_colab.py',
            *['notebooks/' + name for name in NOTEBOOKS.values()]]
OPTIONAL = ['notebooks/README.md', 'notebooks/control/README.md', 'notebooks/riesgo/README.md',
            'notebooks/control/01_identificacion_pid_fopdt.ipynb', 'notebooks/riesgo/01_modelo_riesgo_demo.ipynb',
            'docs/orden_cuadernos_colab.md', 'docs/yolo26.md', 'docs/datasets_reales_entrenamiento.md']


def build_package(root=BASE, output=None):
    root = Path(root).resolve()
    state = inspect_progress(root, verify_datasets=True)
    if any(d['estado'] != 'listo' for d in state['datasets'].values()):
        raise RuntimeError('Prepara/verifica ambos datasets antes de crear el paquete')
    missing = [name for name in REQUIRED if not (root / name).is_file()]
    if missing:
        raise RuntimeError('Faltan archivos del flujo: ' + ', '.join(missing))
    paths = {root / name for name in REQUIRED + OPTIONAL if (root / name).is_file()}
    for folder, task in DATASETS.values():
        dataset = root / 'data/processed' / folder
        manifest = json.loads((dataset / 'manifest.json').read_text())
        paths.update(dataset / name for name in ['manifest.json', 'report.json'])
        if task == 'detect':
            paths.add(dataset / 'data.yaml')
        for record in manifest['records']:
            paths.add(dataset / record['output_path'])
            if record.get('label_path'):
                paths.add(dataset / record['label_path'])
    # Keep upstream attribution, but not raw image duplicates or application secrets.
    for source in DATASETS:
        cache = root / 'data/raw/fuentes_reales' / source
        paths.update(p for p in cache.glob('*') if p.is_file() and p.name.lower().startswith(('readme', 'license', 'citation')))
    output = Path(output or root / 'data/processed/colab_yolo26_listo.zip').resolve()
    if output in paths or output == root:
        raise ValueError('El archivo de salida no puede sobrescribir una entrada')
    for path in paths:
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('No se incluyen enlaces ni archivos externos: ' + str(path))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.zip.part')
    instructions = '''PAQUETE LOCAL PARA COLAB — YOLO26
1. Sube colab_yolo26_listo.zip a Mi unidad en Google Drive.
2. Abre en Colab el cuaderno local actualizado notebooks/00_inicio_y_datasets.ipynb
   y ejecuta su celda 1. Monta Drive y extrae el ZIP automáticamente si falta el proyecto.
   Si tu cuaderno aún muestra el error antiguo, puedes extraer el paquete una vez:

from google.colab import drive
drive.mount('/content/drive')
from zipfile import ZipFile
with ZipFile('/content/drive/MyDrive/colab_yolo26_listo.zip') as package:
    package.extractall('/content/drive/MyDrive')

Se crea/actualiza Tesis_IOT_Papa con el flujo, scripts y datos preparados.
Luego abre Tesis_IOT_Papa/notebooks/00_inicio_y_datasets.ipynb.
Ruta corta: 00 -> 01 -> 02 -> 04. Comparación de tesis: 00 -> 01 -> 02 -> 03 -> 04.
Los datasets ya vienen divididos: no los vuelvas a dividir ni mezcles test con train.
Cada cuaderno numera sus celdas de código. Repite el inicio en cada sesión nueva.
No incluye .env, bases de datos, credenciales, venv, runs ni pesos entrenados.
Este archivo no acredita que se haya subido a Drive ni que se haya entrenado.
'''
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as package:
            package.writestr('Tesis_IOT_Papa/EMPEZAR_AQUI.txt', instructions)
            for path in sorted(paths):
                name = 'Tesis_IOT_Papa/' + path.relative_to(root).as_posix()
                if path.suffix == '.ipynb':
                    # Keep local results; distribute code without runtime output or private Drive listings.
                    document = json.loads(path.read_text())
                    for cell in document['cells']:
                        if cell['cell_type'] == 'code':
                            cell.update(execution_count=None, outputs=[])
                        cell.get('metadata', {}).pop('executionInfo', None)
                    package.writestr(name, json.dumps(document, ensure_ascii=False, indent=1) + '\n')
                else:
                    package.write(path, name)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=BASE)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = build_package(args.root, args.output)
    print('Paquete local:', output)
    print('Tamaño:', round(output.stat().st_size / 1024**2, 1), 'MiB')
    print('No se ha subido a Drive. Empieza en notebooks/00_inicio_y_datasets.ipynb.')


if __name__ == '__main__':
    main()
