"""Offline regressions for the YOLO26 integration; doubles are not training data."""
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock

import cv2
import numpy as np
import pytest

from scripts import entrenar_yolo26 as training
from server.app.core.config import settings
from server.app.services import vision_service as vision


@pytest.fixture
def plan_fixture(tmp_path, monkeypatch):
    def create(source='plantdoc', family='yolo26'):
        folder, task = training.SOURCES[source]
        directory = tmp_path / 'data/processed' / folder
        directory.mkdir(parents=True, exist_ok=True)
        manifest = {'task': task, 'source': source, 'revision': 'unit-fixture-not-real-source',
                    'limitations': ['UNIT TEST FIXTURE']}
        (directory / 'manifest.json').write_text(json.dumps(manifest))
        if task == 'detect':
            (directory / 'data.yaml').write_text('path: /old/machine\ntrain: images/train\nval: images/val\ntest: images/test\nnc: 2\nnames: [tizon_tardio, tizon_temprano]\n')
        monkeypatch.setattr(training, 'verify_dataset', lambda path: {'source': source, 'task': task, 'images': 3})
        return training.training_plan(tmp_path, source, family, epochs=1)
    return create


def test_yolo26_plans_use_separate_tasks(plan_fixture):
    detector = plan_fixture()
    classifier = plan_fixture('plantvillage')
    assert detector['initial_weights'] == 'yolo26n.pt'
    assert classifier['initial_weights'] == 'yolo26n-cls.pt'
    assert detector['task'] == 'detect' and classifier['task'] == 'classify'
    assert plan_fixture('plantdoc', 'yolo11')['initial_weights'] == 'yolo11n.pt'


def test_synthetic_or_invalid_dataset_is_not_bypassed(tmp_path, monkeypatch):
    def reject(path):
        raise ValueError('Expected an explicitly real classification/detection manifest')
    monkeypatch.setattr(training, 'verify_dataset', reject)
    with pytest.raises(ValueError, match='explicitly real'):
        training.training_plan(tmp_path)


def test_moved_dataset_keeps_original_yaml(plan_fixture):
    plan = plan_fixture()
    original = Path(plan['dataset']) / 'data.yaml'
    before = original.read_text()
    runtime = training._data_argument(plan)
    import yaml
    assert yaml.safe_load(Path(runtime).read_text())['path'] == plan['dataset']
    assert original.read_text() == before


def test_training_uses_actual_run_and_holds_out_test(plan_fixture, monkeypatch, tmp_path):
    plan = plan_fixture()
    actual_run = tmp_path / 'runs/incremented-name2'
    validation_splits = []
    factories = []

    class FakeModel:
        task = 'detect'
        names = {0: 'tizon_tardio', 1: 'tizon_temprano'}
        trainer = SimpleNamespace(save_dir=actual_run)

        def train(self, **kwargs):
            assert kwargs['optimizer'] == 'SGD' and kwargs['seed'] == 42
            assert kwargs['data'] != str(Path(plan['dataset']) / 'data.yaml')
            (actual_run / 'weights').mkdir(parents=True)
            (actual_run / 'weights/best.pt').write_bytes(b'unit-test-checkpoint')

        def val(self, **kwargs):
            validation_splits.append(kwargs['split'])
            return SimpleNamespace(results_dict={'metrics/mAP50-95(B)': 0.125})

    def factory(path):
        factories.append(path)
        return FakeModel()
    monkeypatch.setattr(training, '_yolo', lambda: factory)
    result = training.train_experiment(plan, device='cpu')
    assert factories[0] == 'yolo26n.pt'
    assert result['best_weights'] == str(actual_run / 'weights/best.pt')
    assert result['validation']['metrics/mAP50-95(B)'] == 0.125
    assert validation_splits == ['val']
    metadata = json.loads((actual_run / 'weights/best.metadata.json').read_text())
    assert metadata['box_semantics'] == 'whole_leaf'
    assert metadata['weights_sha256'] == hashlib.sha256(b'unit-test-checkpoint').hexdigest()
    result = training.evaluate_test(result, device='cpu')
    assert validation_splits == ['val', 'test']
    assert result['test']['metrics/mAP50-95(B)'] == 0.125


@pytest.fixture
def model_fixture(tmp_path, monkeypatch):
    """Install in-memory Ultralytics/SAHI doubles, without downloads."""
    factory = Mock()
    ultralytics = ModuleType('ultralytics')
    ultralytics.YOLO = factory
    monkeypatch.setitem(sys.modules, 'ultralytics', ultralytics)
    sahi = ModuleType('sahi')
    sahi.AutoDetectionModel = SimpleNamespace(from_pretrained=Mock(return_value=object()))
    monkeypatch.setitem(sys.modules, 'sahi', sahi)
    monkeypatch.setattr(settings, 'VISION_DEMO_MODE', False)
    monkeypatch.setattr(settings, 'VISION_BOX_SEMANTICS', 'unknown')
    image_path = tmp_path / 'leaf.png'
    cv2.imwrite(str(image_path), np.zeros((100, 100, 3), dtype=np.uint8))

    def load(task='detect', names=None, boxes=None, semantics=None):
        weights = tmp_path / 'best.pt'
        weights.write_bytes(b'unit-test-weights')
        metadata_path = weights.with_suffix('.metadata.json')
        if metadata_path.exists():
            metadata_path.unlink()
        names = names or {0: 'tizon_tardio', 1: 'tizon_temprano'}
        if semantics is not None:
            metadata_path.write_text(json.dumps({'task': task, 'names': names, 'box_semantics': semantics}))
        model = Mock()
        model.task = task
        model.names = names
        result = SimpleNamespace(boxes=boxes or [], probs=SimpleNamespace(top1=0, top1conf=np.float32(.95)))
        model.return_value = [result]
        factory.return_value = model
        service = vision.VisionInferenceService(weights)
        return service, image_path, model, factory, sahi
    return load


def box(cid, coords=(0, 0, 100, 100)):
    return SimpleNamespace(cls=np.array([cid]), conf=np.array([.9]), xyxy=np.array([coords]))


def test_missing_weights_do_not_download_generic_model(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'VISION_DEMO_MODE', False)
    service = vision.VisionInferenceService(tmp_path / 'missing.pt')
    image = tmp_path / 'image.jpg'
    cv2.imwrite(str(image), np.zeros((10, 10, 3), dtype=np.uint8))
    with pytest.raises(vision.VisionUnavailable, match='pesos entrenados'):
        service.procesar_imagen(image)


def test_coco_classes_are_rejected_without_fallback(model_fixture):
    service, image, _, factory, _ = model_fixture(names={0: 'person', 1: 'bicycle'})
    assert service.modelo is None
    with pytest.raises(vision.VisionUnavailable, match='Clases incompatibles'):
        service.procesar_imagen(image)
    assert factory.call_count == 1


def test_classifier_uses_learned_order_and_never_estimates_severity(model_fixture):
    service, image, _, _, sahi = model_fixture(task='classify', names={0: 'hoja_sana', 1: 'tizon_tardio', 2: 'tizon_temprano'})
    result = service.procesar_imagen(image)
    assert result['clase_detectada'] == 'hoja_sana'
    assert result['tarea_modelo'] == 'classify'
    assert result['severidad_disponible'] is False
    assert result['apto_supervision'] is False
    assert result['conteo_insectos'] == 0
    assert json.loads(result['bbox_json']) == []
    sahi.AutoDetectionModel.from_pretrained.assert_not_called()
    with pytest.raises(ValueError, match='no admite'):
        service.procesar_imagen(image, usar_sahi=True)


def test_whole_leaf_detector_is_not_lesion_severity(model_fixture):
    service, image, _, _, sahi = model_fixture(boxes=[box(0)], semantics='whole_leaf')
    result = service.procesar_imagen(image)
    assert result['clase_detectada'] == 'tizon_tardio'
    assert result['severidad_porcentaje'] == 0
    assert not result['severidad_disponible']
    assert not result['apto_supervision']
    assert result['conteo_insectos'] == 0
    assert sahi.AutoDetectionModel.from_pretrained.call_args.kwargs['model_type'] == 'ultralytics'
    with pytest.raises(ValueError, match='no incluye clases'):
        service.procesar_imagen(image, tipo_origen='TRAMPA_AMARILLA')


def test_metadata_must_match_the_checkpoint(model_fixture):
    service, _, _, _, _ = model_fixture(semantics='whole_leaf')
    metadata = service.weights_path.with_suffix('.metadata.json')
    record = json.loads(metadata.read_text())
    record['weights_sha256'] = 'wrong-hash'
    metadata.write_text(json.dumps(record))
    rejected = vision.VisionInferenceService(service.weights_path)
    assert rejected.modelo is None
    assert 'hash' in rejected.error_modelo


def test_lesion_boxes_use_union_and_exclude_healthy(model_fixture):
    service, image, _, _, _ = model_fixture(names={0: 'hoja_sana', 1: 'tizon_tardio'},
        boxes=[box(0), box(1, (0, 0, 50, 50)), box(1, (0, 0, 50, 50))], semantics='lesion')
    result = service.procesar_imagen(image)
    assert result['severidad_porcentaje'] == 25
    assert result['severidad_disponible']
    assert result['conteo_insectos'] == 0


def test_sahi_uses_model_names_and_semantics(model_fixture, monkeypatch):
    service, image, _, _, _ = model_fixture(semantics='whole_leaf')
    predict = ModuleType('sahi.predict')
    predict.get_sliced_prediction = Mock(return_value=SimpleNamespace(object_prediction_list=[
        SimpleNamespace(category=SimpleNamespace(id=1), score=SimpleNamespace(value=.9),
                        bbox=SimpleNamespace(minx=0, miny=0, maxx=100, maxy=100))]))
    monkeypatch.setitem(sys.modules, 'sahi.predict', predict)
    result = service.procesar_imagen(image, usar_sahi=True)
    assert result['clase_detectada'] == 'tizon_temprano'
    assert result['procesado_con_sahi']
    assert result['severidad_porcentaje'] == 0


def test_sahi_initialization_failure_keeps_standard_yolo(model_fixture):
    service, image, _, _, sahi = model_fixture(boxes=[box(0)])
    sahi.AutoDetectionModel.from_pretrained.side_effect = RuntimeError('SAHI unavailable')
    reloaded = vision.VisionInferenceService(service.weights_path)
    assert reloaded.modelo is not None
    assert reloaded.sahi_model is None
    assert reloaded.procesar_imagen(image)['clase_detectada'] == 'tizon_tardio'
    with pytest.raises(vision.VisionUnavailable, match='SAHI'):
        reloaded.procesar_imagen(image, usar_sahi=True)


def test_pilot_api_does_not_publish_or_send_alerts(model_fixture, monkeypatch, tmp_path):
    from server.app.api import endpoints
    from fastapi.testclient import TestClient
    from server.app.main import app
    service, image, _, _, _ = model_fixture(boxes=[box(0)], semantics='whole_leaf')
    monkeypatch.setattr(endpoints, 'vision_service', service)
    monkeypatch.setattr(settings, 'UPLOAD_DIR', str(tmp_path / 'uploads'))
    monkeypatch.setattr(endpoints.db_service, 'registrar_deteccion', AsyncMock(return_value=1))
    publish = Mock()
    alert = AsyncMock()
    monkeypatch.setattr(endpoints.mqtt_service, 'publicar', publish)
    monkeypatch.setattr(endpoints.telegram_service, 'enviar_alerta_con_foto', alert)
    response = TestClient(app).post('/api/v1/vision/inferir', files={'imagen': ('leaf.png', image.read_bytes(), 'image/png')})
    assert response.status_code == 200
    assert response.json()['publicado_mqtt'] is False
    assert response.json()['alerta_telegram_disparada'] is False
    publish.assert_not_called()
    alert.assert_not_called()


def test_generated_notebooks_parse_and_have_no_fabricated_metrics(tmp_path):
    try:
        from IPython.core.interactiveshell import InteractiveShell
        transform = InteractiveShell.instance().input_transformer_manager.transform_cell
    except ImportError:
        # The only magic in the generated notebooks is a standalone %pip line.
        transform = lambda source: '\n'.join(line for line in source.splitlines() if not line.lstrip().startswith('%'))
    root = Path(__file__).resolve().parents[1]
    from scripts.crear_notebooks_vision import GENERATORS, NAMES, write_notebook
    paths = []
    for number, generator in GENERATORS.items():
        generated = tmp_path / NAMES[number]
        write_notebook(generated, generator())
        paths.extend([(generated, True), (root / 'notebooks' / NAMES[number], False)])
    for path, fresh in paths:
        document = json.loads(path.read_text())
        assert document['nbformat'] == 4
        for index, cell in enumerate(document['cells']):
            if cell['cell_type'] == 'code':
                source = ''.join(cell['source'])
                transformed = transform(source)
                compile(transformed, f'{path.name}:cell{index}', 'exec')
                if fresh:
                    assert cell['execution_count'] is None and cell['outputs'] == []
                assert '0.884' not in source
