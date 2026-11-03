"""Workflow state/reuse regressions; temporary fixtures are never training data."""
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image
import pytest

from scripts import flujo_colab as flow
from scripts import entrenar_yolo26 as training
from scripts import preparar_datasets_reales as preparation


@pytest.fixture
def workflow_root(tmp_path):
    for source, (folder, task) in flow.DATASETS.items():
        destination = tmp_path / 'data/processed' / folder
        destination.mkdir(parents=True)
        classes = preparation.NAMES if task == 'classify' else {0: 'tizon_tardio', 1: 'tizon_temprano'}
        records = []
        for number, split in enumerate(['train', 'val', 'test']):
            for cid in classes:
                relative = Path('images') / split / f'{cid}.png' if task == 'detect' else Path(split) / classes[cid] / f'{cid}.png'
                path = destination / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.new('RGB', (10, 10), (number * 50 + cid * 10, 70, 80)).save(path)
                _, digest = preparation.image_info(path)
                record = {'output_path': str(relative), 'pixel_sha256': digest, 'source_group': f'{split}-{cid}',
                          'class_id': cid, 'split': split}
                if task == 'detect':
                    label = Path('labels') / split / f'{cid}.txt'
                    (destination / label).parent.mkdir(parents=True, exist_ok=True)
                    (destination / label).write_text(f'{cid} 0.5 0.5 1.0 1.0\n')
                    record.update(label_path=str(label), boxes=[[cid, .5, .5, 1, 1]])
                records.append(record)
        manifest = {'source': source, 'task': task, 'classes': classes, 'records': records,
                    'synthetic': False, 'limitations': ['UNIT TEST ONLY'], 'revision': 'unit-test-fixture'}
        (destination / 'manifest.json').write_text(json.dumps(manifest))
        if task == 'detect':
            import yaml
            (destination / 'data.yaml').write_text(yaml.safe_dump({'nc': 2, 'names': classes,
                'path': str(destination), 'train': 'images/train', 'val': 'images/val', 'test': 'images/test'}))
    return tmp_path


def saved_run(root, source, family='yolo26', test=False, score=.1):
    plan = training.training_plan(root, source, family)
    run = root / 'runs/datasets_reales' / f'{family}n_{source}_{plan["task"]}'
    best = run / 'weights/best.pt'
    best.parent.mkdir(parents=True)
    best.write_bytes(b'unit-test-only-checkpoint')
    metadata = {'family': family, 'task': plan['task'],
                'weights_sha256': hashlib.sha256(best.read_bytes()).hexdigest()}
    best.with_suffix('.metadata.json').write_text(json.dumps(metadata))
    record = {**plan, 'save_dir': str(run), 'best_weights': str(best),
              'validation': {'metrics/mAP50-95(B)': score}}
    if test:
        record['test'] = {'unit-test-metric': .2}
    (run / 'experiment.json').write_text(json.dumps(record))
    return flow.load_record(run / 'experiment.json', root)


def test_data_ready_does_not_claim_models_are_trained(workflow_root):
    state = flow.inspect_progress(workflow_root, verify_datasets=True)
    assert all(d['estado'] == 'listo' for d in state['datasets'].values())
    assert state['clasificador_yolo26'] is None
    assert state['detector_yolo26'] is None
    assert state['siguiente_cuaderno'] == flow.NOTEBOOKS['01']
    assert not state['evaluacion_final']


def test_missing_data_points_back_to_start(tmp_path):
    state = flow.inspect_progress(tmp_path)
    assert state['siguiente_cuaderno'] == flow.NOTEBOOKS['00']


def test_cli_works_from_outside_the_project(workflow_root, tmp_path_factory):
    import subprocess
    import sys
    script = Path(__file__).resolve().parents[1] / 'scripts/flujo_colab.py'
    result = subprocess.run([sys.executable, str(script), '--root', str(workflow_root), '--verify-datasets', '--json'],
                            cwd=tmp_path_factory.mktemp('other-cwd'), capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)['siguiente_cuaderno'] == flow.NOTEBOOKS['01']


def test_next_step_changes_with_actual_artifacts(workflow_root):
    saved_run(workflow_root, 'plantvillage')
    assert flow.inspect_progress(workflow_root)['siguiente_cuaderno'] == flow.NOTEBOOKS['02']
    saved_run(workflow_root, 'plantdoc')
    assert flow.inspect_progress(workflow_root)['siguiente_cuaderno'] == flow.NOTEBOOKS['04']


def test_reuse_skips_training_even_without_gpu(workflow_root, monkeypatch):
    record = saved_run(workflow_root, 'plantdoc')
    plan = training.training_plan(workflow_root, 'plantdoc')
    monkeypatch.setattr(training, 'train_experiment', lambda *a, **kw: pytest.fail('Must reuse, not retrain'))
    reused = flow.run_or_reuse(plan, device='cpu')
    assert reused['best_weights'] == record['best_weights']


def test_new_training_requires_gpu_or_explicit_cpu(workflow_root):
    plan = training.training_plan(workflow_root, 'plantdoc')
    with pytest.raises(RuntimeError, match='GPU'):
        flow.run_or_reuse(plan, device='cpu')


def test_partial_run_cannot_be_silently_restarted(workflow_root, monkeypatch):
    plan = training.training_plan(workflow_root, 'plantdoc')
    last = workflow_root / 'runs/datasets_reales/yolo26n_plantdoc_detect/weights/last.pt'
    last.parent.mkdir(parents=True)
    last.write_bytes(b'incomplete-unit-test')
    with pytest.raises(RuntimeError, match='incompleto'):
        flow.run_or_reuse(plan, device='cpu', allow_cpu=True)
    assert flow.inspect_progress(workflow_root)['entrenamientos_interrumpidos'] == [str(last)]
    monkeypatch.setattr(training, 'train_experiment', lambda *a, **kw: {'new_run': True})
    assert flow.run_or_reuse(plan, device='cpu', allow_cpu=True, retrain=True)['new_run']
    assert last.read_bytes() == b'incomplete-unit-test'


def partial_run(root, family='yolov8', suffix=''):
    last = root / 'runs/datasets_reales' / f'{family}n_plantdoc_detect{suffix}' / 'weights/last.pt'
    last.parent.mkdir(parents=True)
    last.write_bytes(b'unit-test-partial-checkpoint')
    return last


def test_resume_routes_the_single_partial_to_recovery(workflow_root, monkeypatch):
    last = partial_run(workflow_root)
    plan = training.training_plan(workflow_root, 'plantdoc', 'yolov8')
    calls = []

    def recover(received_plan, checkpoint, **kwargs):
        calls.append((received_plan, checkpoint, kwargs))
        return {'recovered': str(checkpoint)}

    monkeypatch.setattr(training, 'recover_experiment', recover)
    monkeypatch.setattr(training, 'train_experiment', lambda *a, **kw: pytest.fail('Must resume, not restart'))
    result = flow.run_or_reuse(plan, device=0, resume=True)
    assert result == {'recovered': str(last)}
    assert calls == [(plan, last, {'device': 0})]
    assert last.read_bytes() == b'unit-test-partial-checkpoint'


def test_resume_keeps_completed_families_and_recovers_only_the_pending_one(workflow_root, monkeypatch):
    completed = [saved_run(workflow_root, 'plantdoc', family) for family in ('yolo26', 'yolo11')]
    last = partial_run(workflow_root, 'yolov8')
    calls = []

    def recover(plan, checkpoint, **kwargs):
        calls.append((plan['family'], checkpoint))
        return {'family': plan['family'], 'best_weights': 'recovered-unit-test'}

    monkeypatch.setattr(training, 'recover_experiment', recover)
    monkeypatch.setattr(training, 'train_experiment', lambda *a, **kw: pytest.fail('No fresh training expected'))
    plans = [training.training_plan(workflow_root, 'plantdoc', family)
             for family in ('yolo26', 'yolo11', 'yolov8')]
    records = [flow.run_or_reuse(plan, device=0, resume=True) for plan in plans]
    assert [r['best_weights'] for r in records[:2]] == [r['best_weights'] for r in completed]
    assert calls == [('yolov8', last)]


def test_resume_does_not_choose_between_multiple_partial_runs(workflow_root, monkeypatch):
    first = partial_run(workflow_root)
    second = partial_run(workflow_root, suffix='2')
    plan = training.training_plan(workflow_root, 'plantdoc', 'yolov8')
    monkeypatch.setattr(training, 'recover_experiment', lambda *a, **kw: pytest.fail('Ambiguous checkpoint'))
    monkeypatch.setattr(training, 'train_experiment', lambda *a, **kw: pytest.fail('Must not restart'))
    with pytest.raises(RuntimeError, match='varios checkpoints') as error:
        flow.run_or_reuse(plan, device=0, resume=True)
    assert str(first) in str(error.value) and str(second) in str(error.value)


def test_resume_requires_gpu_unless_cpu_is_explicitly_allowed(workflow_root, monkeypatch):
    partial_run(workflow_root)
    plan = training.training_plan(workflow_root, 'plantdoc', 'yolov8')
    calls = []
    monkeypatch.setattr(training, 'recover_experiment', lambda *a, **kw: calls.append(kw) or {'recovered': True})
    with pytest.raises(RuntimeError, match='GPU'):
        flow.run_or_reuse(plan, device='cpu', resume=True)
    assert calls == []
    assert flow.run_or_reuse(plan, device='cpu', allow_cpu=True, resume=True)['recovered']
    assert calls == [{'device': 'cpu'}]


def test_explicit_retraining_takes_precedence_over_resume_and_preserves_partial(workflow_root, monkeypatch):
    last = partial_run(workflow_root)
    plan = training.training_plan(workflow_root, 'plantdoc', 'yolov8')
    calls = []
    monkeypatch.setattr(training, 'recover_experiment', lambda *a, **kw: pytest.fail('Retraining was explicit'))
    monkeypatch.setattr(training, 'train_experiment', lambda p, **kw: calls.append((p, kw)) or {'new_run': True})
    assert flow.run_or_reuse(plan, device=0, resume=True, retrain=True)['new_run']
    assert calls == [(plan, {'device': 0})]
    assert last.read_bytes() == b'unit-test-partial-checkpoint'


def test_changed_dataset_or_checkpoint_cannot_be_reused(workflow_root):
    record = saved_run(workflow_root, 'plantdoc')
    Path(record['best_weights']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='checkpoint'):
        flow.latest_experiment(workflow_root, 'plantdoc')
    assert flow.inspect_progress(workflow_root)['errores_experimentos']


def test_portable_selection_and_records_after_copy(workflow_root, tmp_path_factory):
    classifier = saved_run(workflow_root, 'plantvillage', test=True)
    detector = saved_run(workflow_root, 'plantdoc', score=.1)
    alternative = saved_run(workflow_root, 'plantdoc', family='yolo11', score=.2, test=True)
    selected = flow.freeze_detector([detector, alternative], workflow_root)
    assert selected['family'] == 'yolo11'
    moved = tmp_path_factory.mktemp('copied-root') / 'project'
    shutil.copytree(workflow_root, moved)
    restored = flow.final_records(moved)
    assert [r['family'] for r in restored] == ['yolo26', 'yolo11']
    assert all(Path(r['best_weights']).is_relative_to(moved) for r in restored)
    assert flow.inspect_progress(moved)['evaluacion_final']
    assert flow.inspect_progress(moved)['siguiente_cuaderno'] is None
    assert classifier['task'] == 'classify'


def test_mismatched_comparisons_are_rejected(workflow_root):
    record = saved_run(workflow_root, 'plantdoc')
    alternative = {**record, 'family': 'yolo11', 'epochs': record['epochs'] + 1}
    with pytest.raises(ValueError, match='misma configuración'):
        flow.freeze_detector([record, alternative], workflow_root)


def test_final_test_requires_freeze_and_does_not_repeat(workflow_root, monkeypatch):
    record = saved_run(workflow_root, 'plantdoc')
    with pytest.raises(RuntimeError, match='CONFIRMAR_MODELOS_FIJADOS'):
        flow.evaluate_once(record)
    calls = []
    def evaluate(record, **kwargs):
        calls.append(record)
        result = {**record, 'test': {'fixture': .5}}
        training._write_record(result)
        return result
    monkeypatch.setattr(training, 'evaluate_test', evaluate)
    evaluated = flow.evaluate_once(record, confirmed=True, device='cpu')
    assert len(calls) == 1
    # Re-run the cell using its original stale variable, as in an actual notebook.
    assert flow.evaluate_once(record, confirmed=False)['test'] == evaluated['test']
    assert len(calls) == 1


def test_no_test_evaluation_outside_last_notebook():
    root = Path(__file__).resolve().parents[1]
    for number, filename in flow.NOTEBOOKS.items():
        document = json.loads((root / 'notebooks' / filename).read_text())
        codes = [c for c in document['cells'] if c['cell_type'] == 'code']
        assert [c['metadata']['workflow']['step'] for c in codes] == list(range(1, len(codes) + 1))
        source = '\n'.join(''.join(c['source']) for c in codes)
        if number != '04':
            assert 'evaluate_once(' not in source and 'evaluate_test(' not in source
        if number in {'00', '04'}:
            assert 'run_or_reuse(' not in source
