"""Recovery regressions use model doubles, never claimed training measurements."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts import entrenar_yolo26 as training
from test_flujo_colab import workflow_root


@pytest.fixture
def interrupted_run(workflow_root, monkeypatch):
    plan = training.training_plan(workflow_root, 'plantdoc', 'yolov8')
    run = workflow_root / 'runs/datasets_reales/yolov8n_plantdoc_detect'
    weights = run / 'weights'
    weights.mkdir(parents=True)
    last, best = weights / 'last.pt', weights / 'best.pt'
    last.write_bytes(b'original-partial-unit-test-checkpoint')
    best.write_bytes(b'original-best-unit-test-checkpoint')
    args = {
        'model': 'yolov8n.pt', 'task': 'detect', 'mode': 'train',
        'data': str(Path(plan['dataset']) / 'data.yaml'),
        'epochs': 50, 'batch': 8, 'imgsz': 640, 'seed': 42,
        'optimizer': 'SGD', 'cos_lr': True, 'deterministic': True, 'patience': 15,
        'save_dir': str(run), 'project': str(run.parent), 'name': run.name,
        'fraction': 1.0, 'single_cls': False, 'classes': None,
    }
    (run / 'args.yaml').write_text(yaml.safe_dump(args))
    (run / 'results.csv').write_text('epoch,metrics/mAP50-95(B)\n1,0.1\n2,0.2\n')
    state = SimpleNamespace(
        plan=plan, root=workflow_root, run=run, last=last, best=best,
        args=args, epoch=1, optimizer={'state': {}, 'param_groups': []},
        names={0: 'tizon_tardio', 1: 'tizon_temprano'}, task='detect',
        yaml_file='yolov8n.yaml', trains=[], validations=[], loaded=[],
    )

    class FakeModel:
        def __init__(self, path):
            state.loaded.append(str(path))
            self.path = Path(path)
            self.ckpt_path = str(path)
            self.task = state.task
            self.names = state.names
            self.model = SimpleNamespace(yaml={'yaml_file': state.yaml_file, 'scale': 'n'},
                                         names=state.names, args=copy.deepcopy(state.args))
            self.ckpt = {
                'epoch': state.epoch, 'optimizer': copy.deepcopy(state.optimizer),
                'train_args': copy.deepcopy(state.args),
                'train_results': {'epoch': [1, 2]},
            }
            self.trainer = SimpleNamespace(save_dir=state.run, args=SimpleNamespace(**state.args))
            self.callbacks = {}

        def add_callback(self, event, callback):
            self.callbacks.setdefault(event, []).append(callback)

        def train(self, **kwargs):
            state.trains.append(kwargs)
            for callback in self.callbacks.get('on_pretrain_routine_end', []):
                callback(self.trainer)
            state.last.write_bytes(b'resumed-last-unit-test-checkpoint')
            state.best.write_bytes(b'resumed-best-unit-test-checkpoint')

        def val(self, **kwargs):
            state.validations.append(kwargs)
            return SimpleNamespace(results_dict={'metrics/mAP50-95(B)': 0.25})

    monkeypatch.setattr(training, '_yolo', lambda: FakeModel)
    return state


def test_partial_recovery_resumes_same_run_and_only_validates(interrupted_run):
    state = interrupted_run
    old_last, old_best = state.last.read_bytes(), state.best.read_bytes()
    record = training.recover_experiment(state.plan, state.last, device=0)
    assert len(state.trains) == 1
    assert state.trains[0]['resume'] is True
    assert state.trains[0]['device'] == 0
    assert Path(state.trains[0]['save_dir']) == state.run
    assert record['save_dir'] == str(state.run)
    assert record['best_weights'] == str(state.best)
    assert [call['split'] for call in state.validations] == ['val']
    assert 'test' not in record
    assert any(p != state.last and p.read_bytes() == old_last for p in state.run.rglob('last.pt'))
    assert any(p != state.best and p.read_bytes() == old_best for p in state.run.rglob('best.pt'))


@pytest.mark.parametrize('epoch,optimizer', [(-1, None), (49, {'state': {}, 'param_groups': []})])
def test_completed_run_is_finalized_without_training(interrupted_run, epoch, optimizer):
    state = interrupted_run
    state.epoch, state.optimizer = epoch, optimizer
    before = state.best.read_bytes()
    record = training.recover_experiment(state.plan, state.last, device=0)
    assert state.trains == []
    assert state.best.read_bytes() == before
    assert [call['split'] for call in state.validations] == ['val']
    assert record['validation'] == {'metrics/mAP50-95(B)': 0.25}
    assert (state.run / 'experiment.json').is_file()
    assert state.best.with_suffix('.metadata.json').is_file()


@pytest.mark.parametrize('key,value', [('epochs', 25), ('batch', 16), ('imgsz', 320), ('seed', 99),
                                     ('optimizer', 'Adam'), ('cos_lr', False)])
def test_incompatible_training_configuration_is_rejected(interrupted_run, key, value):
    state = interrupted_run
    state.args[key] = value
    before = state.last.read_bytes()
    with pytest.raises(ValueError):
        training.recover_experiment(state.plan, state.last, device=0)
    assert state.trains == []
    assert state.validations == []
    assert state.last.read_bytes() == before
    assert list(state.run.rglob('last.pt')) == [state.last]


@pytest.mark.parametrize('mismatch', ['dataset', 'taxonomy', 'family'])
def test_other_dataset_taxonomy_or_architecture_is_rejected(interrupted_run, mismatch):
    state = interrupted_run
    if mismatch == 'dataset':
        other = state.root / 'other-dataset.yaml'
        other.write_text(yaml.safe_dump({'path': str(state.root / 'other-dataset'),
            'train': 'images/train', 'val': 'images/val', 'test': 'images/test',
            'nc': 2, 'names': state.names}))
        state.args['data'] = str(other)
    elif mismatch == 'taxonomy':
        state.names = {0: 'person', 1: 'car'}
    else:
        state.args['model'] = 'yolo11n.pt'
        state.yaml_file = 'yolo11n.yaml'
    with pytest.raises(ValueError):
        training.recover_experiment(state.plan, state.last, device=0)
    assert state.trains == []
    assert state.validations == []
    assert list(state.run.rglob('last.pt')) == [state.last]


def test_snapshot_rejects_changed_dataset_digest(interrupted_run):
    state = interrupted_run
    snapshot = {**state.plan, 'dataset_manifest_sha256': 'different-historical-digest'}
    (state.run / 'run_plan.json').write_text(json.dumps(snapshot))
    with pytest.raises(ValueError):
        training.recover_experiment(state.plan, state.last, device=0)
    assert state.trains == []
    assert state.validations == []


def test_legacy_recovery_does_not_invent_historical_dataset_provenance(interrupted_run):
    state = interrupted_run
    record = training.recover_experiment(state.plan, state.last, device=0)
    recovery = record['recovery']
    assert recovery['provenance_verified'] is False
    assert recovery['historical_dataset_sha256'] is None
    assert recovery['dataset_manifest_sha256_at_recovery'] == state.plan['dataset_manifest_sha256']
    assert Path(recovery['backup_dir']).is_dir()


def test_matching_original_run_snapshot_verifies_historical_provenance(interrupted_run):
    state = interrupted_run
    (state.run / 'run_plan.json').write_text(json.dumps({
        **state.plan, 'dataset_provenance': 'verified_at_training_start'}))
    record = training.recover_experiment(state.plan, state.last, device=0)
    recovery = record['recovery']
    assert recovery['provenance_verified'] is True
    assert recovery['historical_dataset_sha256'] == state.plan['dataset_manifest_sha256']


def test_recovery_only_snapshot_does_not_gain_original_provenance(interrupted_run):
    state = interrupted_run
    (state.run / 'run_plan.json').write_text(json.dumps({
        **state.plan, 'dataset_provenance': 'verified_at_recovery_only'}))
    record = training.recover_experiment(state.plan, state.last, device=0)
    assert record['recovery']['provenance_verified'] is False
    assert record['recovery']['historical_dataset_sha256'] is None


def test_legacy_drive_runtime_yaml_rebases_to_verified_local_dataset(interrupted_run):
    state = interrupted_run
    state.args['data'] = '/content/drive/MyDrive/Tesis_IOT_Papa/runs/dataset_configs/plantdoc_936f2ce987f14cd8b3f4cac438b9c269.yaml'
    record = training.recover_experiment(state.plan, state.last, device=0)
    assert record['recovery']['provenance_verified'] is False
    assert len(state.trains) == 1
    runtime_config = yaml.safe_load(Path(state.trains[0]['data']).read_text())
    assert runtime_config['path'] == state.plan['dataset']


def test_recovery_writes_metadata_before_completed_record(interrupted_run, monkeypatch):
    state = interrupted_run
    state.epoch, state.optimizer = -1, None
    original = training._write_record
    calls = []

    def write_record(record):
        assert state.best.with_suffix('.metadata.json').is_file()
        calls.append(record)
        original(record)

    monkeypatch.setattr(training, '_write_record', write_record)
    training.recover_experiment(state.plan, state.last, device=0)
    assert len(calls) == 1
