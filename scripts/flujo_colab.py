#!/usr/bin/env python3
"""Progress and reusable experiments for the ordered Colab workflow.

Inspecting progress never trains, downloads weights or contacts greenhouse services.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
DATASETS = {
    'plantvillage': ('papa_plantvillage_clasificacion', 'classify'),
    'plantdoc': ('papa_plantdoc_yolo', 'detect'),
}
NOTEBOOKS = {
    '00': '00_inicio_y_datasets.ipynb',
    '01': '01_entrenar_clasificador.ipynb',
    '02': '02_entrenar_detector.ipynb',
    '03': '03_comparar_detectores.ipynb',
    '04': '04_evaluacion_y_exportacion.ipynb',
}
PLAN_KEYS = ('source', 'task', 'family', 'epochs', 'batch', 'imgsz', 'seed', 'dataset_manifest_sha256')


def _dataset(root, source):
    return Path(root) / 'data/processed' / DATASETS[source][0]


def load_record(path, root):
    """Resolve a copied run using its current directory, not old absolute paths."""
    path, root = Path(path).resolve(), Path(root).resolve()
    record = json.loads(path.read_text())
    source = record['source']
    if source not in DATASETS or record['task'] != DATASETS[source][1]:
        raise ValueError('Tarea/fuente de experimento inválida')
    run = path.parent
    best = run / 'weights/best.pt'
    metadata_path = best.with_suffix('.metadata.json')
    if not best.is_file() or not metadata_path.is_file():
        raise ValueError('Faltan best.pt o sus metadatos: ' + str(run))
    metadata = json.loads(metadata_path.read_text())
    digest = hashlib.sha256(best.read_bytes()).hexdigest()
    if metadata.get('weights_sha256') != digest:
        raise ValueError('El checkpoint cambió o no corresponde a los metadatos: ' + str(best))
    if metadata.get('task') != record['task'] or metadata.get('family') != record['family']:
        raise ValueError('La tarea/familia de los metadatos no corresponde al experimento')
    manifest = _dataset(root, source) / 'manifest.json'
    if not manifest.is_file() or hashlib.sha256(manifest.read_bytes()).hexdigest() != record['dataset_manifest_sha256']:
        raise ValueError('El dataset actual difiere del usado para entrenar: ' + source)
    return {**record, 'root': str(root), 'dataset': str(_dataset(root, source)),
            'save_dir': str(run), 'best_weights': str(best), 'record_path': str(path)}


def experiments(root, source=None, family=None):
    """Newest completed records first; keep damaged runs visible as errors."""
    paths = sorted((Path(root) / 'runs/datasets_reales').glob('**/experiment.json'),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    results, errors = [], []
    for path in paths:
        try:
            raw = json.loads(path.read_text())
            if source and raw.get('source') != source:
                continue
            if family and raw.get('family') != family:
                continue
            results.append(load_record(path, root))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append({'path': str(path), 'error': str(exc)})
    return results, errors


def latest_experiment(root, source, family='yolo26', plan=None):
    records, errors = experiments(root, source, family)
    for record in records:
        if plan is None or all(record.get(key) == plan.get(key) for key in PLAN_KEYS):
            return record
    if errors:
        raise ValueError('Hay resultados incompletos o incompatibles; revisa el estado: ' + errors[0]['error'])
    return None


def run_or_reuse(plan, device='auto', retrain=False, allow_cpu=False, resume=False):
    """Reuse matching validated runs across notebooks and restarted kernels."""
    from scripts.entrenar_yolo26 import train_experiment, recover_experiment, _device
    previous = None if retrain else latest_experiment(plan['root'], plan['source'], plan['family'], plan)
    if previous is not None and not retrain:
        print('Ya entrenado; reutilizando:', previous['best_weights'])
        return previous
    partials = [p for p in (Path(plan['root']) / 'runs/datasets_reales').glob(
        f"{plan['family']}n_{plan['source']}_{plan['task']}*/weights/last.pt")
        if not (p.parent.parent / 'experiment.json').is_file()]
    if partials and not retrain and not resume:
        raise RuntimeError('Hay un entrenamiento incompleto con last.pt. Revísalo antes de repetir; '
                           'REANUDAR=True recupera la ejecución compatible; REENTRENAR=True inicia otra: ' + str(partials[0]))
    resolved = _device(device)
    if str(resolved) == 'cpu' and not allow_cpu:
        raise RuntimeError('Activa una GPU para entrenar. Para una prueba deliberada en CPU, cambia PERMITIR_CPU=True.')
    if partials and not retrain:
        if len(partials) != 1:
            raise RuntimeError('Hay varios checkpoints pendientes para esta familia. Revisa sus rutas antes de elegir: '
                               + ', '.join(str(p) for p in sorted(partials)))
        return recover_experiment(plan, partials[0], device=resolved)
    return train_experiment(plan, device=resolved)


def freeze_detector(records, root):
    """Select on validation only; save a portable reference to the chosen run."""
    if not records or any(r['task'] != 'detect' or r['source'] != 'plantdoc' for r in records):
        raise ValueError('La comparación requiere detectores del mismo piloto PlantDoc')
    common = ('epochs', 'batch', 'imgsz', 'seed', 'dataset_manifest_sha256')
    if any(any(r.get(key) != records[0].get(key) for key in common) for r in records):
        raise ValueError('Los experimentos no tienen la misma configuración/dataset')
    metric = 'metrics/mAP50-95(B)'
    winner = max(records, key=lambda r: r['validation'][metric])
    output = Path(root) / 'runs/datasets_reales/seleccion_por_validacion.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        'criterio': metric, 'family': winner['family'],
        'experiment': str(Path(winner['save_dir']).resolve().relative_to(Path(root).resolve()) / 'experiment.json'),
        'dataset_manifest_sha256': winner['dataset_manifest_sha256'],
        'validation': winner['validation'],
    }, indent=2))
    return winner


def final_records(root, classification_family='yolo26', detection_family='yolo26', use_comparison=True):
    """Read saved checkpoints in a new session; no dependency on kernel variables."""
    root = Path(root).resolve()
    classifier = latest_experiment(root, 'plantvillage', classification_family)
    selection = root / 'runs/datasets_reales/seleccion_por_validacion.json'
    if use_comparison and selection.is_file():
        info = json.loads(selection.read_text())
        if 'experiment' not in info:
            raise ValueError('Selección antigua: ejecuta la celda de selección del cuaderno 03 actualizado')
        path = (root / info['experiment']).resolve()
        if not path.is_relative_to(root / 'runs/datasets_reales'):
            raise ValueError('Referencia de selección fuera de runs/datasets_reales')
        detector = load_record(path, root)
        if detector['source'] != 'plantdoc' or detector['task'] != 'detect':
            raise ValueError('La selección no corresponde a un detector PlantDoc')
    else:
        detector = latest_experiment(root, 'plantdoc', detection_family)
    if classifier is None or detector is None:
        raise RuntimeError('Falta entrenar: ejecuta 01 para clasificación y 02 para detección antes de 04')
    return [classifier, detector]


def evaluate_once(record, confirmed=False, device='auto'):
    """A completed test is displayed without re-evaluation or retraining."""
    saved = Path(record.get('record_path', Path(record['save_dir']) / 'experiment.json'))
    if saved.is_file():
        record = load_record(saved, record['root'])
    if 'test' in record:
        print('Test ya guardado; no se repite:', record['best_weights'])
        return record
    if not confirmed:
        raise RuntimeError('Fija los modelos por validación y cambia CONFIRMAR_MODELOS_FIJADOS=True en 04')
    from scripts.entrenar_yolo26 import evaluate_test
    return evaluate_test(record, device=device)


def comparable_detectors(root, reference):
    """Get saved matching families; never create new runs during final evaluation."""
    candidates, errors = experiments(root, 'plantdoc')
    keys = ('epochs', 'batch', 'imgsz', 'seed', 'dataset_manifest_sha256')
    selected = {}
    for record in candidates:
        if all(record.get(key) == reference.get(key) for key in keys):
            selected.setdefault(record['family'], record)
    if errors:
        raise ValueError('Revisa los experimentos antes de comparar: ' + errors[0]['error'])
    return list(selected.values())


def write_summary(records, root):
    if not records or any(not record.get('test') for record in records):
        raise ValueError('Faltan métricas de test para el resumen final')
    path = Path(root) / 'runs/datasets_reales/resumen_evaluacion_final.csv'
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [{'task': r['task'], 'family': r['family'], 'best_weights': r['best_weights'], **r['test']}
            for r in records]
    columns = list(dict.fromkeys(key for row in rows for key in row))
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return path


def inspect_progress(root=BASE, verify_datasets=False):
    root = Path(root).resolve()
    datasets = {}
    for source, (folder, task) in DATASETS.items():
        directory = root / 'data/processed' / folder
        try:
            manifest = json.loads((directory / 'manifest.json').read_text())
            if manifest.get('synthetic') is not False or manifest.get('task') != task or manifest.get('source') != source:
                raise ValueError('Se requiere un manifiesto real de la tarea/fuente correspondiente')
            records = manifest['records']
            missing = sum(not (directory / r['output_path']).is_file() or
                          (r.get('label_path') is not None and not (directory / r['label_path']).is_file())
                          for r in records)
            if not records or missing:
                raise ValueError(f'Dataset vacío o {missing} registros incompletos')
            if verify_datasets:
                from scripts.preparar_datasets_reales import verify_dataset
                verify_dataset(directory)
            datasets[source] = {'estado': 'listo', 'images': len(records), 'task': task,
                                'verificacion_profunda': verify_datasets,
                                'splits': {s: sum(r['split'] == s for r in records) for s in ['train', 'val', 'test']}}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            datasets[source] = {'estado': 'pendiente', 'motivo': str(exc)}
    records, errors = experiments(root)
    classification = next((r for r in records if r['source'] == 'plantvillage' and r['family'] == 'yolo26'), None)
    detection = next((r for r in records if r['source'] == 'plantdoc' and r['family'] == 'yolo26'), None)
    chosen = None
    if classification and detection:
        try:
            chosen = final_records(root)
        except (ValueError, RuntimeError, OSError, KeyError) as exc:
            errors.append({'path': 'seleccion_por_validacion.json', 'error': str(exc)})
    if any(d['estado'] != 'listo' for d in datasets.values()):
        next_step = '00'
    elif classification is None:
        next_step = '01'
    elif detection is None:
        next_step = '02'
    elif chosen is None or not all('test' in r for r in chosen):
        next_step = '04'
    else:
        next_step = None
    partials = [str(p) for p in (root / 'runs/datasets_reales').glob('**/weights/last.pt')
                if not (p.parent.parent / 'experiment.json').is_file()]
    return {'root': str(root), 'datasets': datasets,
            'clasificador_yolo26': classification['best_weights'] if classification else None,
            'detector_yolo26': detection['best_weights'] if detection else None,
            'experimentos_completos': len(records), 'errores_experimentos': errors,
            'entrenamientos_interrumpidos': partials,
            'evaluacion_final': bool(chosen) and all('test' in r for r in chosen),
            'siguiente_cuaderno': NOTEBOOKS[next_step] if next_step else None,
            'comparacion': 'opcional: ejecutar 03 antes del test final si compararás familias',
            'riesgo_real': 'pendiente de serie temporal y etiquetas reales; demo separada',
            'drive': 'la copia a Drive y la ejecución de Colab no se deducen del estado local'}


def print_progress(state):
    print('PROYECTO:', state['root'])
    for source, data in state['datasets'].items():
        print(f"Datos {source}: {data['estado']} | {data.get('images', 0)} imágenes")
    for key, label in [('clasificador_yolo26', '01 Clasificador'), ('detector_yolo26', '02 Detector')]:
        print(label + ':', state[key] or 'PENDIENTE de entrenamiento')
    print('03 Comparación: opcional, antes de evaluar test')
    print('04 Test final:', 'GUARDADO' if state['evaluacion_final'] else 'PENDIENTE')
    print('Siguiente paso de la ruta corta:', state['siguiente_cuaderno'] or 'Modelos evaluados; revisar entrega al servidor')
    if state['entrenamientos_interrumpidos'] or state['errores_experimentos']:
        print('REVISAR:', state['entrenamientos_interrumpidos'], state['errores_experimentos'])
    print('Riesgo real:', state['riesgo_real'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=BASE)
    parser.add_argument('--verify-datasets', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    state = inspect_progress(args.root, args.verify_datasets)
    if args.json:
        print(json.dumps(state, indent=2, ensure_ascii=False))
    else:
        print_progress(state)


if __name__ == '__main__':
    main()
