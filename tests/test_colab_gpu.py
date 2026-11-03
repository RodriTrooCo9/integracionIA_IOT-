"""Notebook configuration survives a restarted kernel without starting training."""
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest

from scripts.crear_notebooks_vision import NAMES
from test_flujo_colab import workflow_root, saved_run


def cell_source(number, step):
    path = Path(__file__).resolve().parents[1] / 'notebooks' / NAMES[number]
    cells = json.loads(path.read_text())['cells']
    return ''.join(next(c for c in cells if c['cell_type'] == 'code'
                        and c['metadata']['workflow']['step'] == step)['source'])


@pytest.fixture
def t4(monkeypatch):
    torch = ModuleType('torch')
    torch.__version__ = 'unit-test-fixture'
    torch.cuda = SimpleNamespace(is_available=lambda: True, get_device_name=lambda device: 'Tesla T4')
    ultralytics = ModuleType('ultralytics')
    ultralytics.__version__ = '8.4.0'
    monkeypatch.setitem(sys.modules, 'torch', torch)
    monkeypatch.setitem(sys.modules, 'ultralytics', ultralytics)
    return torch


@pytest.mark.parametrize('number,batch', [('01', 16), ('02', 8), ('03', 8)])
def test_configuration_imports_training_plan_in_a_fresh_namespace(workflow_root, t4, number, batch):
    namespace = {'PROJECT_ROOT': workflow_root}
    exec(compile(cell_source(number, 4), f'notebook-{number}:cell4', 'exec'), namespace)
    assert namespace['DEVICE'] == 0
    assert namespace['PERMITIR_CPU'] is False
    plans = namespace.get('plans', [namespace.get('plan')])
    assert all(p['batch'] == batch and p['epochs'] == 50 for p in plans)
    assert all(p['imgsz'] == (224 if number == '01' else 640) for p in plans)
    assert not (workflow_root / 'runs').exists()  # planning never starts training


@pytest.mark.parametrize('number', ['01', '02', '03', '04'])
def test_missing_project_after_runtime_change_explains_cell_order(number):
    with pytest.raises(RuntimeError, match='celdas 1, 2 y 3'):
        exec(compile(cell_source(number, 4), f'notebook-{number}:cell4', 'exec'), {})


@pytest.mark.parametrize('step', [3, 4])
def test_no_cuda_cannot_silently_switch_to_cpu(workflow_root, t4, step):
    t4.cuda.is_available = lambda: False
    with pytest.raises(RuntimeError, match='GPU T4'):
        exec(compile(cell_source('03', step), f'notebook-03:cell{step}', 'exec'),
             {'PROJECT_ROOT': workflow_root})
    assert not (workflow_root / 'runs').exists()


def test_evaluation_recovers_saved_runs_on_gpu_without_retraining(workflow_root, t4):
    saved_run(workflow_root, 'plantvillage')
    saved_run(workflow_root, 'plantdoc')
    namespace = {'PROJECT_ROOT': workflow_root}
    exec(compile(cell_source('04', 4), 'notebook-04:cell4', 'exec'), namespace)
    assert namespace['DEVICE'] == 0
    assert namespace['CONFIRMAR_MODELOS_FIJADOS'] is False
    assert len(namespace['records']) == 2
    assert all('test' not in record for record in namespace['records'])
