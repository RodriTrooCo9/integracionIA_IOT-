"""Only explicit workflow inputs and prepared records enter the portable archive."""
import json
import zipfile

import pytest

from scripts.empaquetar_colab import REQUIRED, build_package
from test_flujo_colab import workflow_root  # reuse the small offline dataset fixture


def add_project_files(root):
    for name in REQUIRED:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == '.ipynb':
            path.write_text(json.dumps({'cells': [{'cell_type': 'code', 'source': ['value = 1'],
                'execution_count': 3, 'outputs': [{'output_type': 'stream', 'text': ['private-runtime-output']}],
                'metadata': {'executionInfo': {'user': 'private-user'}}}], 'metadata': {}, 'nbformat': 4, 'nbformat_minor': 4}))
        else:
            path.write_text('unit-test-workflow-file')


def test_package_has_data_and_no_application_secrets(workflow_root):
    add_project_files(workflow_root)
    (workflow_root / '.env').write_text('SECRET=must-not-be-exported')
    (workflow_root / 'private.db').write_bytes(b'private')
    extra = workflow_root / 'data/processed/papa_plantdoc_yolo/.env'
    extra.write_text('unrelated private file in dataset directory')
    output = build_package(workflow_root)
    with zipfile.ZipFile(output) as package:
        names = package.namelist()
        assert package.testzip() is None
        assert 'Tesis_IOT_Papa/notebooks/00_inicio_y_datasets.ipynb' in names
        assert 'Tesis_IOT_Papa/data/processed/papa_plantdoc_yolo/manifest.json' in names
        assert 'Tesis_IOT_Papa/scripts/flujo_colab.py' in names
        assert all(name.startswith('Tesis_IOT_Papa/') and '..' not in name.split('/') for name in names)
        assert not any(name.endswith(('.env', '.db', '.key')) for name in names)
        portable = package.read('Tesis_IOT_Papa/notebooks/00_inicio_y_datasets.ipynb').decode()
        assert 'private-runtime-output' not in portable and 'private-user' not in portable
        cell = json.loads(portable)['cells'][0]
        assert cell['execution_count'] is None and cell['outputs'] == []
    original = json.loads((workflow_root / 'notebooks/00_inicio_y_datasets.ipynb').read_text())
    assert original['cells'][0]['execution_count'] == 3  # do not clear the user's saved results


def test_package_requires_complete_datasets(tmp_path):
    add_project_files(tmp_path)
    with pytest.raises(RuntimeError, match='ambos datasets'):
        build_package(tmp_path)
