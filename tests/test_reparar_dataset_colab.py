"""Repair integrity errors from a matching bundle; never revise training labels."""
import json
from pathlib import Path
from zipfile import ZipFile

from PIL import Image
import pytest

from scripts.flujo_colab import DATASETS
from scripts.reparar_dataset_colab import repair_dataset
from scripts.preparar_datasets_reales import verify_dataset
from test_flujo_colab import workflow_root


def package_dataset(root, source='plantdoc', change=None):
    dataset = root / 'data/processed' / DATASETS[source][0]
    output = root / 'colab_yolo26_listo.zip'
    with ZipFile(output, 'w') as package:
        for path in dataset.rglob('*'):
            if path.is_file():
                content = path.read_bytes()
                if change:
                    content = change(path.relative_to(dataset).as_posix(), content)
                package.writestr('Tesis_IOT_Papa/' + path.relative_to(root).as_posix(), content)
    return dataset, output


@pytest.mark.parametrize('damage', ['changed-image', 'missing-image', 'invalid-label'])
def test_restore_only_damaged_files_and_keep_durable_backups(workflow_root, damage):
    dataset, archive = package_dataset(workflow_root)
    manifest = (dataset / 'manifest.json').read_bytes()
    relative = 'labels/train/0.txt' if damage == 'invalid-label' else 'images/train/0.png'
    target = dataset / relative
    expected = target.read_bytes()
    if damage == 'changed-image':
        Image.new('RGB', (10, 10), (250, 0, 0)).save(target)
    elif damage == 'missing-image':
        target.unlink()
    else:
        target.write_text('0 0.5 0.5 0.1 0.1\n')
    damaged = target.read_bytes() if target.exists() else None
    result = repair_dataset(workflow_root, 'plantdoc', archive)
    assert result['images'] == 6
    assert target.read_bytes() == expected
    assert (dataset / 'manifest.json').read_bytes() == manifest
    logs = list((workflow_root / 'data/repair_backups').glob('*/papa_plantdoc_yolo/repair.json'))
    assert len(logs) == 1
    assert json.loads(logs[0].read_text())['status'] == 'verified'
    saved = logs[0].parent / relative
    assert saved.read_bytes() == damaged if damaged is not None else not saved.exists()
    repair_dataset(workflow_root, 'plantdoc', archive)
    assert len(list((workflow_root / 'data/repair_backups').glob('*/papa_plantdoc_yolo/repair.json'))) == 1


def test_expanded_exclusion_notes_do_not_change_the_installed_manifest(workflow_root):
    dataset, archive = package_dataset(workflow_root)
    manifest_path = dataset / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['excluded'] = [{'reason': 'expanded source notes'}]
    manifest_path.write_text(json.dumps(manifest))
    before = manifest_path.read_bytes()
    (dataset / 'images/train/0.png').write_bytes(b'broken-unit-test-image')
    repair_dataset(workflow_root, 'plantdoc', archive)
    assert manifest_path.read_bytes() == before
    verify_dataset(dataset)


def test_another_dataset_revision_cannot_replace_files(workflow_root):
    def change(name, content):
        if name == 'manifest.json':
            manifest = json.loads(content)
            manifest['revision'] = 'another-revision'
            return json.dumps(manifest).encode()
        return content
    dataset, archive = package_dataset(workflow_root, change=change)
    target = dataset / 'images/train/0.png'
    target.write_bytes(b'preserve-this-damaged-input')
    with pytest.raises(ValueError, match='otra revisión'):
        repair_dataset(workflow_root, 'plantdoc', archive)
    assert target.read_bytes() == b'preserve-this-damaged-input'
    assert not (workflow_root / 'data/repair_backups').exists()


def test_bad_replacement_is_rejected_before_touching_the_dataset(workflow_root):
    def change(name, content):
        return b'bad-archive-image' if name == 'images/train/0.png' else content
    dataset, archive = package_dataset(workflow_root, change=change)
    target = dataset / 'images/train/0.png'
    target.write_bytes(b'damaged-input')
    with pytest.raises(OSError):
        repair_dataset(workflow_root, 'plantdoc', archive)
    assert target.read_bytes() == b'damaged-input'
    assert not (workflow_root / 'data/repair_backups').exists()


def test_healthy_dataset_does_not_need_or_open_a_bundle(workflow_root):
    repair_dataset(workflow_root, 'plantvillage', workflow_root / 'missing.zip')
    assert not (workflow_root / 'data/repair_backups').exists()
