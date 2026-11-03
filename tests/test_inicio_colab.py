"""Exercise startup before project imports, without a live Colab/Drive session."""
import json
from pathlib import Path
import stat
import sys
from types import ModuleType, SimpleNamespace
from zipfile import ZipFile, ZipInfo

import pytest

from scripts.iniciar_colab import PROJECT_FILES, iniciar_colab
from scripts.organizar_ramas_colab import organize_branch


@pytest.fixture
def session(tmp_path, monkeypatch):
    monkeypatch.delenv('IOTTESIS_ROOT', raising=False)
    monkeypatch.delenv('IOTTESIS_ZIP', raising=False)
    monkeypatch.setattr(sys, 'path', sys.path.copy())
    monkeypatch.chdir(tmp_path)
    drive = tmp_path / 'drive/MyDrive'
    content = tmp_path / 'content'
    drive.mkdir(parents=True)
    content.mkdir()
    return {'drive_home': drive, 'content': content, 'mount': False}


def project(root):
    for name in PROJECT_FILES:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('unit-test-project-file')
    return root


def bundle(path, extra=None, complete=True):
    with ZipFile(path, 'w') as package:
        for name in PROJECT_FILES if complete else PROJECT_FILES[:1]:
            package.writestr('Tesis_IOT_Papa/' + name, 'unit-test-project-file')
        for name, value in (extra or {}).items():
            package.writestr(name, value)
    return path


def test_first_cell_works_without_any_project_files(session, monkeypatch):
    root = session['drive_home'] / 'Tesis_IOT_Papa'
    archive = bundle(session['drive_home'] / 'colab_yolo26_listo.zip')
    monkeypatch.setenv('IOTTESIS_ROOT', str(root))
    monkeypatch.setenv('IOTTESIS_ZIP', str(archive))
    mounted = []
    google = ModuleType('google')
    colab = ModuleType('google.colab')
    colab.drive = SimpleNamespace(mount=mounted.append)
    google.colab = colab
    monkeypatch.setitem(sys.modules, 'google', google)
    monkeypatch.setitem(sys.modules, 'google.colab', colab)
    notebook = Path(__file__).resolve().parents[1] / 'notebooks/00_inicio_y_datasets.ipynb'
    first = next(c for c in json.loads(notebook.read_text())['cells'] if c['cell_type'] == 'code')
    namespace = {}
    exec(compile(''.join(first['source']), str(notebook), 'exec'), namespace)
    assert mounted == ['/content/drive']
    assert namespace['PROJECT_ROOT'] == root
    assert all((root / name).is_file() for name in PROJECT_FILES)


def test_existing_renamed_project_is_found_without_extracting(session, monkeypatch):
    root = project(session['drive_home'] / 'Mi tesis revisada')
    monkeypatch.setattr('scripts.iniciar_colab.ZipFile', lambda *a: pytest.fail('Existing project must be reused'))
    assert iniciar_colab(**session) == root
    assert iniciar_colab(**session) == root


def test_nested_archive_folder_is_found(session, monkeypatch):
    wrapper = session['drive_home'] / 'otra-carpeta'
    root = project(wrapper / 'Tesis_IOT_Papa')
    monkeypatch.setenv('IOTTESIS_ROOT', str(wrapper))
    assert iniciar_colab(**session) == root


def test_upload_in_content_extracts_to_persistent_drive(session):
    root = session['drive_home'] / 'Tesis_IOT_Papa'
    bundle(session['content'] / 'colab_yolo26_listo.zip')
    assert iniciar_colab(**session) == root


def test_partial_install_adds_code_but_preserves_data_and_runs(session, monkeypatch):
    root = session['drive_home'] / 'Tesis_IOT_Papa'
    existing = root / 'data/processed/example/train/photo.jpg'
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b'existing-partition')
    best = root / 'runs/completed/weights/best.pt'
    best.parent.mkdir(parents=True)
    best.write_bytes(b'trained-checkpoint')
    secret = root / '.env'
    secret.write_text('PRIVATE=untouched')
    (root / PROJECT_FILES[0]).parent.mkdir(parents=True)
    (root / PROJECT_FILES[0]).write_text('incomplete-old-project')
    bundle(session['drive_home'] / 'colab_yolo26_listo.zip', {
        'Tesis_IOT_Papa/data/processed/example/train/photo.jpg': b'new-partition',
        'Tesis_IOT_Papa/data/processed/example/val/photo.jpg': b'new-file',
    })
    assert iniciar_colab(**session) == root
    assert existing.read_bytes() == b'existing-partition'
    assert (root / 'data/processed/example/val/photo.jpg').read_bytes() == b'new-file'
    assert best.read_bytes() == b'trained-checkpoint'
    assert secret.read_text() == 'PRIVATE=untouched'


def test_missing_project_explains_what_to_upload_without_listing_private_files(session):
    (session['drive_home'] / 'private-photo.jpg').write_bytes(b'private-file')
    with pytest.raises(RuntimeError) as error:
        iniciar_colab(**session)
    assert 'Sube colab_yolo26_listo.zip a Mi unidad' in str(error.value)
    assert str(session['drive_home'] / 'colab_yolo26_listo.zip') in str(error.value)
    assert str(session['drive_home'] / 'Tesis_IOT_Papa') in str(error.value)
    assert 'private-photo.jpg' not in str(error.value)


def test_explicit_path_does_not_silently_use_another_project(session, monkeypatch):
    project(session['drive_home'] / 'Tesis_IOT_Papa')
    monkeypatch.setenv('IOTTESIS_ROOT', str(session['drive_home'] / 'desired-project'))
    with pytest.raises(RuntimeError, match='No se encontró'):
        iniciar_colab(**session)


def test_multiple_renamed_projects_require_explicit_selection(session):
    project(session['drive_home'] / 'one')
    project(session['drive_home'] / 'two')
    with pytest.raises(RuntimeError, match='Hay varios proyectos'):
        iniciar_colab(**session)


@pytest.mark.parametrize('entry', [
    'Tesis_IOT_Papa/../escape.py', '/escape.py', 'other-project/scripts/code.py',
    'Tesis_IOT_Papa/runs/trained/weights/best.pt', 'Tesis_IOT_Papa/.env',
])
def test_bad_archive_does_not_write_any_files(session, entry):
    bundle(session['drive_home'] / 'colab_yolo26_listo.zip', {entry: 'bad'})
    with pytest.raises(ValueError):
        iniciar_colab(**session)
    assert not (session['drive_home'] / 'Tesis_IOT_Papa').exists()


def test_incomplete_zip_is_reported_before_extraction(session):
    bundle(session['drive_home'] / 'colab_yolo26_listo.zip', complete=False)
    with pytest.raises(ValueError, match='flujo completo'):
        iniciar_colab(**session)
    assert not (session['drive_home'] / 'Tesis_IOT_Papa').exists()


def test_link_inside_zip_cannot_be_extracted(session):
    archive = bundle(session['drive_home'] / 'colab_yolo26_listo.zip')
    with ZipFile(archive, 'a') as package:
        link = ZipInfo('Tesis_IOT_Papa/scripts/linked')
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        package.writestr(link, '/outside')
    with pytest.raises(ValueError, match='Ruta inválida'):
        iniciar_colab(**session)
    assert not (session['drive_home'] / 'Tesis_IOT_Papa').exists()


def test_existing_link_cannot_redirect_installation(session, tmp_path):
    root = session['drive_home'] / 'Tesis_IOT_Papa'
    root.mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()
    (root / 'scripts').symlink_to(outside, target_is_directory=True)
    bundle(session['drive_home'] / 'colab_yolo26_listo.zip')
    with pytest.raises(ValueError):
        iniciar_colab(**session)
    assert list(outside.iterdir()) == []


def test_branch_setup_updates_without_losing_saved_results():
    notebook = {'metadata': {}, 'cells': [
        {'cell_type': 'markdown', 'source': ['# RAMA INDEPENDIENTE · CONTROL']},
        {'cell_type': 'code', 'source': [
            'IOTTESIS_ROOT = "old"\nRUTA_BASE = str(PROJECT_ROOT)'], 'outputs': []},
        {'cell_type': 'code', 'source': ['result = 1'], 'outputs': [{'saved': 'measurement'}]},
    ]}
    updated = organize_branch(notebook, 'control')
    assert 'PROJECT_ROOT = iniciar_colab()' in ''.join(updated['cells'][1]['source'])
    assert updated['cells'][2] == notebook['cells'][2]
    assert organize_branch(updated, 'control') == updated
