#!/usr/bin/env python3
"""Train real potato pilots; YOLO26 by default, YOLO11/YOLOv8 for comparison.

Dataset verification and --dry-run are offline. Training downloads the selected
pretrained weights if necessary. Test evaluation is always an explicit step.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import shutil
import sys
import time
from uuid import uuid4

import yaml

# Works both as `python scripts/...` and as a module imported from a notebook.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.preparar_datasets_reales import verify_dataset

BASE = Path(__file__).resolve().parents[1]
FAMILIES = ("yolo26", "yolo11", "yolov8")
SOURCES = {
    "plantvillage": ("papa_plantvillage_clasificacion", "classify"),
    "plantdoc": ("papa_plantdoc_yolo", "detect"),
}


def training_plan(root=BASE, source="plantdoc", family="yolo26", epochs=50, batch=None):
    """Validate actual images/labels and return a plan without loading YOLO."""
    if source not in SOURCES or family not in FAMILIES:
        raise ValueError("Fuente o familia no soportada")
    if epochs < 1 or (batch is not None and batch < 1):
        raise ValueError("epochs y batch deben ser positivos")
    root = Path(root).expanduser().resolve()
    directory, task = SOURCES[source]
    dataset = root / "data/processed" / directory
    report = verify_dataset(dataset)
    manifest_path = dataset / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if report["source"] != source or report["task"] != task:
        raise ValueError("La procedencia/tarea del dataset no corresponde al experimento")
    return {
        "root": str(root), "dataset": str(dataset), "source": source,
        "task": task, "family": family,
        "initial_weights": f"{family}n{'-cls' if task == 'classify' else ''}.pt",
        "epochs": epochs, "imgsz": 224 if task == "classify" else 640,
        "batch": batch or (16 if task == "classify" else 8), "seed": 42,
        "revision": manifest.get("revision"),
        "dataset_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "limitations": manifest.get("limitations", []),
        "images": report["images"],
    }


def _yolo():
    import ultralytics
    from ultralytics import YOLO
    version = tuple(int(v) for v in ultralytics.__version__.split(".")[:2])
    if version < (8, 4):
        raise RuntimeError("YOLO26 requiere ultralytics>=8.4.0; instala requirements-vision.txt y reinicia el kernel")
    return YOLO


def _device(device):
    if device == "auto":
        import torch
        return 0 if torch.cuda.is_available() else "cpu"
    return device


def _data_argument(plan):
    dataset = Path(plan["dataset"])
    if plan["task"] == "classify":
        return str(dataset)
    # A copied Drive dataset may contain another machine's absolute YAML path.
    # Write a runtime configuration; never alter the original dataset/manifest.
    config = yaml.safe_load((dataset / "data.yaml").read_text())
    config["path"] = str(dataset)
    directory = Path(plan["root"]) / "runs/dataset_configs"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{plan['source']}_{uuid4().hex}.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False))
    return str(path)


def _metrics(result):
    return {key: float(value) for key, value in result.results_dict.items()}


def _write_record(record):
    _atomic_json(Path(record["save_dir"]) / "experiment.json", record)


def _atomic_json(path, value):
    temporary = path.with_name('.' + path.name + '.' + uuid4().hex + '.tmp')
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _attach_plan(model, plan, provenance='verified_at_training_start'):
    def save_plan(trainer):
        _atomic_json(Path(trainer.save_dir) / 'run_plan.json',
                     {**plan, 'dataset_provenance': provenance})
    if hasattr(model, 'add_callback'):
        model.add_callback('on_train_start', save_plan)


def train_experiment(plan, device="auto", workers=2):
    """Train and evaluate validation only; use best.pt from the actual run."""
    YOLO = _yolo()
    device = _device(device)
    model = YOLO(plan["initial_weights"])
    _attach_plan(model, plan)
    data = _data_argument(plan)
    model.train(
        data=data, epochs=plan["epochs"], imgsz=plan["imgsz"], batch=plan["batch"],
        seed=plan["seed"], deterministic=True, workers=workers, device=device,
        optimizer="SGD", cos_lr=True, patience=15, save=True,
        project=str(Path(plan["root"]) / "runs/datasets_reales"),
        name=f"{plan['family']}n_{plan['source']}_{plan['task']}",
    )
    return _finalize_experiment(plan, Path(model.trainer.save_dir), device, workers)


def _finalize_experiment(plan, save_dir, device, workers, recovery=None):
    """Validate saved best weights and publish metadata before the completion record."""
    save_dir = Path(save_dir).resolve()
    best = save_dir / "weights/best.pt"
    if not best.is_file():
        raise RuntimeError("El entrenamiento no generó weights/best.pt")
    trained = _yolo()(str(best))
    if trained.task != plan["task"]:
        raise ValueError("La tarea del checkpoint no coincide con el experimento")
    validation = trained.val(data=_data_argument(plan), split="val", imgsz=plan["imgsz"],
                             batch=plan["batch"], device=device, workers=workers)
    versions = {}
    for package in ("ultralytics", "torch", "torchvision", "numpy", "sahi"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            pass
    record = {**plan, "save_dir": str(save_dir), "best_weights": str(best),
              "validation": _metrics(validation), "versions": versions,
              "names": trained.names, "device": str(device)}
    if recovery is not None:
        record['recovery'] = recovery
    # Adjacent metadata travels with the checkpoint when deployed.
    metadata = {
        "family": plan["family"], "task": plan["task"], "names": trained.names,
        "box_semantics": "whole_leaf" if plan["task"] == "detect" else "none",
        "source": plan["source"], "revision": plan["revision"],
        "dataset_manifest_sha256": plan["dataset_manifest_sha256"],
        "limitations": plan["limitations"], "versions": versions,
        "weights_sha256": hashlib.sha256(best.read_bytes()).hexdigest(),
    }
    if recovery is not None:
        metadata['recovery'] = recovery
    _atomic_json(best.with_suffix('.metadata.json'), metadata)
    _write_record(record)
    return record


def _ordered_names(names):
    if isinstance(names, list):
        return names
    return [value for _, value in sorted((int(k), v) for k, v in names.items())]


def _validate_recovery_model(model, plan, run):
    args = model.ckpt.get('train_args', {})
    if model.task != plan['task'] or args.get('task', model.task) != plan['task']:
        raise ValueError('La tarea del checkpoint no coincide con el plan')
    architecture = getattr(getattr(model, 'model', None), 'yaml', {}) or {}
    candidates = [architecture.get('yaml_file'), args.get('model')]
    origins = [Path(str(name)).name for name in candidates if name]
    expected = Path(plan['initial_weights']).stem
    known = [Path(name).stem for name in origins
             if re.fullmatch(r'(?:yolo26|yolo11|yolov8)[nslmx](?:-cls)?\.(?:pt|yaml)', name)]
    if expected not in known or any(name != expected for name in known):
        raise ValueError('No se puede acreditar la familia/arquitectura del checkpoint para este plan')
    checks = {key: plan[key] for key in ('epochs', 'batch', 'imgsz', 'seed')}
    checks.update(optimizer='SGD', cos_lr=True, deterministic=True, patience=15)
    for key, expected_value in checks.items():
        actual = args.get(key)
        if key == 'imgsz' and isinstance(actual, (list, tuple)) and actual and len(set(actual)) == 1:
            actual = actual[0]
        if key == 'optimizer' and isinstance(actual, str):
            actual, expected_value = actual.lower(), expected_value.lower()
        if actual != expected_value:
            raise ValueError(f'Configuración incompatible al recuperar: {key}={actual!r}, esperado {expected_value!r}')
    if args.get('fraction', 1.0) != 1.0 or args.get('single_cls', False) or args.get('classes') is not None:
        raise ValueError('El checkpoint utilizó otra selección de datos/clases')
    dataset = Path(plan['dataset']).resolve()
    manifest = json.loads((dataset / 'manifest.json').read_text())
    if _ordered_names(model.names) != _ordered_names(manifest['classes']):
        raise ValueError('Las clases del checkpoint no corresponden al manifiesto')
    raw = Path(str(args.get('data', '')))
    expected_suffix = ('data', 'processed', SOURCES[plan['source']][0])
    if plan['task'] == 'classify':
        if raw.resolve() != dataset and (raw.exists() or tuple(raw.parts[-3:]) != expected_suffix):
            raise ValueError('El checkpoint pertenece a otro dataset de clasificación')
    else:
        runtime = tuple(raw.parts[-3:-1]) == ('runs', 'dataset_configs') and raw.name.startswith(plan['source'] + '_')
        direct = tuple(raw.parts[-4:-1]) == expected_suffix and raw.name == 'data.yaml'
        if not (runtime or direct):
            raise ValueError('El checkpoint pertenece a otro dataset de detección')
        config_path = raw if raw.is_file() else (Path(plan['root']) / 'runs/dataset_configs' / raw.name if runtime else dataset / 'data.yaml')
        # Legacy copied runs can lose their generated YAML. Class names and source-shaped paths
        # still establish compatibility, while the recovery record leaves historical hashes unknown.
        if not config_path.is_file():
            config_path = dataset / 'data.yaml'
        config = yaml.safe_load(config_path.read_text())
        origin = Path(str(config.get('path', '')))
        if origin.resolve() != dataset and (origin.exists() or tuple(origin.parts[-3:]) != expected_suffix):
            raise ValueError('El YAML apunta a otro dataset')
        if config.get('nc') != len(manifest['classes']) or _ordered_names(config.get('names', {})) != _ordered_names(manifest['classes']):
            raise ValueError('La taxonomía del YAML no coincide con el manifiesto')
        if any(config.get(split) != 'images/' + split for split in ('train', 'val', 'test')):
            raise ValueError('Las particiones del YAML no corresponden al plan')
    snapshot = run / 'run_plan.json'
    if snapshot.is_file():
        prior = json.loads(snapshot.read_text())
        keys = ('source', 'task', 'family', 'epochs', 'batch', 'imgsz', 'seed', 'dataset_manifest_sha256')
        if any(prior.get(key) != plan.get(key) for key in keys):
            raise ValueError('El plan/dataset actual difiere de run_plan.json')
        return prior.get('dataset_provenance', 'verified_at_training_start') == 'verified_at_training_start'
    return False


def recover_experiment(plan, checkpoint, device='auto', workers=2):
    """Resume an interrupted checkpoint or finish validation of a stripped completed run."""
    checkpoint = Path(checkpoint).resolve()
    root = Path(plan['root']).resolve()
    if (not checkpoint.is_file() or checkpoint.name != 'last.pt'
            or checkpoint.parent.name != 'weights'
            or not checkpoint.is_relative_to(root / 'runs/datasets_reales')):
        raise ValueError('Selecciona un last.pt existente dentro de runs/datasets_reales')
    run = checkpoint.parent.parent
    verify_dataset(Path(plan['dataset']))
    current_hash = hashlib.sha256((Path(plan['dataset']) / 'manifest.json').read_bytes()).hexdigest()
    if current_hash != plan['dataset_manifest_sha256']:
        raise ValueError('El manifiesto cambió después de crear el plan')
    model = _yolo()(str(checkpoint))
    historical_verified = _validate_recovery_model(model, plan, run)
    epoch = model.ckpt.get('epoch')
    optimizer = model.ckpt.get('optimizer')
    if not isinstance(epoch, int):
        raise ValueError('El checkpoint no contiene un contador de épocas válido')
    resumable = 0 <= epoch < plan['epochs'] - 1 and optimizer is not None
    finished = (epoch == -1 and optimizer is None) or epoch >= plan['epochs'] - 1
    if not resumable and not finished:
        raise ValueError('El checkpoint está incompleto y no conserva el optimizador para reanudar')
    best = run / 'weights/best.pt'
    if not best.is_file():
        raise ValueError('Falta best.pt; conserva last.pt y revisa el entrenamiento antes de recuperarlo')
    _validate_recovery_model(_yolo()(str(best)), plan, run)
    backup = run / 'recovery_backups' / uuid4().hex
    backup.mkdir(parents=True)
    for relative in ('weights/last.pt', 'weights/best.pt', 'weights/best.metadata.json',
                     'args.yaml', 'results.csv', 'run_plan.json', 'experiment.json'):
        original = run / relative
        if original.is_file():
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, saved)
    recovery = {
        'mode': 'resume' if resumable else 'finalize', 'checkpoint_epoch': epoch,
        'checkpoint_sha256': hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        'backup_dir': str(backup), 'provenance_verified': historical_verified,
        'historical_dataset_sha256': current_hash if historical_verified else None,
        'dataset_manifest_sha256_at_recovery': current_hash,
    }
    _atomic_json(backup / 'recovery.json', recovery)
    if not historical_verified:
        print('Recuperación de ejecución antigua: el hash histórico del dataset no estaba registrado.')
    device = _device(device)
    if resumable:
        print(f'Reanudando {plan["family"]} desde la época {epoch + 2} de {plan["epochs"]}:', checkpoint)
        provenance = 'verified_at_training_start' if historical_verified else 'verified_at_recovery_only'
        _attach_plan(model, plan, provenance)
        # Epoch and optimizer state have been checked: resume=True must never fall back to fresh training.
        model.train(resume=True, device=device, workers=workers, data=_data_argument(plan), save_dir=str(run))
        if Path(model.trainer.save_dir).resolve() != run:
            raise RuntimeError('La reanudación escribió en otra carpeta; conserva los respaldos y revisa el resultado')
    else:
        print('Checkpoint finalizado: recuperando validación y metadatos sin volver a entrenar:', best)
    return _finalize_experiment(plan, run, device, workers, recovery)


def evaluate_test(record, device="auto", workers=2):
    """Run only after freezing the model/configuration using validation."""
    trained = _yolo()(record["best_weights"])
    result = trained.val(data=_data_argument(record), split="test", imgsz=record["imgsz"],
                         batch=record["batch"], device=_device(device), workers=workers)
    record = {**record, "test": _metrics(result)}
    _write_record(record)
    return record


def benchmark_cpu(record, samples=10):
    """Measured inference on validation images, including YOLO preprocessing."""
    if samples < 1:
        raise ValueError("samples debe ser positivo")
    model = _yolo()(record["best_weights"])
    directory = Path(record["dataset"]) / ("val" if record["task"] == "classify" else "images/val")
    images = sorted(p for p in directory.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png"})[:samples]
    if not images:
        raise ValueError("No hay imágenes de validación para el benchmark")
    kwargs = {"device": "cpu", "imgsz": record["imgsz"], "verbose": False, "save": False}
    for _ in range(2):
        model.predict(str(images[0]), **kwargs)
    elapsed = []
    for image in images:
        start = time.perf_counter()
        model.predict(str(image), **kwargs)
        elapsed.append((time.perf_counter() - start) * 1000)
    result = {"mean_ms": sum(elapsed) / len(elapsed), "samples": len(elapsed), "split": "val"}
    record["benchmark_cpu"] = result
    _write_record(record)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=BASE)
    parser.add_argument("--source", choices=SOURCES, default="plantdoc")
    parser.add_argument("--family", choices=FAMILIES, default="yolo26")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch", type=int)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true", help="Verificar datos y mostrar plan; no descarga pesos ni entrena")
    parser.add_argument("--evaluate-test", action="store_true", help="Evaluar test después del entrenamiento, sin buscar hiperparámetros")
    args = parser.parse_args()
    plan = training_plan(args.root, args.source, args.family, args.epochs, args.batch)
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return
    result = train_experiment(plan, args.device, args.workers)
    if args.evaluate_test:
        result = evaluate_test(result, args.device, args.workers)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
