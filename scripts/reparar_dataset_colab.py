"""Restore damaged prepared files from the matching bundle, keeping backups."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from uuid import uuid4
from zipfile import ZipFile

import yaml
from scripts.preparar_datasets_reales import image_info, verify_dataset


def repair_dataset(root, source, archive=None):
    root = Path(root).resolve()
    folder = {'plantdoc': 'papa_plantdoc_yolo',
              'plantvillage': 'papa_plantvillage_clasificacion'}[source]
    dataset = root / 'data/processed' / folder
    try:
        return verify_dataset(dataset)
    except (OSError, ValueError, KeyError) as original_error:
        candidates = ([Path(archive)] if archive else
                      [Path(os.environ['IOTTESIS_ZIP'])] if os.environ.get('IOTTESIS_ZIP') else
                      [root.parent / 'colab_yolo26_listo.zip',
                       root / 'data/processed/colab_yolo26_listo.zip', Path('/content/colab_yolo26_listo.zip')])
        bundle = next((p for p in candidates if p.is_file()), None)
        if bundle is None or not (dataset / 'manifest.json').is_file():
            raise RuntimeError('El dataset no pasa la verificación. Usa 00 para prepararlo o coloca '
                               'colab_yolo26_listo.zip en Mi unidad para restaurarlo. Detalle: '
                               + str(original_error)) from original_error

    manifest_bytes = (dataset / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    prefix = 'Tesis_IOT_Papa/data/processed/' + folder + '/'
    with tempfile.TemporaryDirectory(prefix='iot-restaurar-') as temporary, ZipFile(bundle) as package:
        staged = Path(temporary)
        bundled = json.loads(package.read(prefix + 'manifest.json'))
        # Excluded-source notes may have been expanded; keep the installed manifest intact.
        if any(manifest.get(k) != bundled.get(k)
               for k in ('source', 'task', 'revision', 'classes', 'records', 'synthetic')):
            raise ValueError('El ZIP contiene otra revisión, partición o anotación del dataset. No se sustituyó ningún archivo.')
        paths = []
        for record in manifest['records']:
            paths.append((record['output_path'], record['pixel_sha256']))
            if record.get('label_path'):
                paths.append((record['label_path'], None))
        if manifest['task'] == 'detect':
            paths.append(('data.yaml', None))
        seen = set()
        for relative, _ in paths:
            path = Path(relative)
            if path.is_absolute() or '..' in path.parts or relative in seen:
                raise ValueError('Ruta inválida o repetida en el manifiesto: ' + relative)
            seen.add(relative)
            target = dataset / path
            if not target.resolve().is_relative_to(dataset.resolve()) or target.is_symlink():
                raise ValueError('Destino externo o enlazado: ' + relative)
            output = staged / path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(package.read(prefix + relative))
        (staged / 'manifest.json').write_bytes(manifest_bytes)
        verify_dataset(staged)  # validate the full replacement before touching Drive

        changed = []
        for relative, expected_pixels in paths:
            current, replacement = dataset / relative, staged / relative
            try:
                if expected_pixels is not None:
                    intact = image_info(current)[1] == expected_pixels
                elif relative == 'data.yaml':
                    old, new = yaml.safe_load(current.read_text()), yaml.safe_load(replacement.read_text())
                    intact = old.get('nc') == new.get('nc') and old.get('names') == new.get('names')
                else:
                    intact = current.read_bytes() == replacement.read_bytes()
            except (OSError, ValueError, AttributeError, yaml.YAMLError):
                intact = False
            if not intact:
                changed.append(relative)
        if not changed:
            # A structural issue must not be disguised as a repaired image.
            return verify_dataset(dataset)

        backup = root / 'data/repair_backups' / uuid4().hex / folder
        backup.mkdir(parents=True)
        # Back up every existing input before replacing the first file.
        for relative in changed:
            current = dataset / relative
            if current.exists():
                saved = backup / relative
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(current, saved)
        log = {'source': source, 'archive': str(bundle), 'replaced': changed,
               'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(), 'status': 'restoring'}
        (backup / 'repair.json').write_text(json.dumps(log, ensure_ascii=False, indent=2))
        for relative in changed:
            target = dataset / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            pending = target.with_name('.' + target.name + '.restoring-' + uuid4().hex)
            try:
                shutil.copyfile(staged / relative, pending)
                pending.replace(target)
            finally:
                pending.unlink(missing_ok=True)
        result = verify_dataset(dataset)
        log['status'] = 'verified'
        (backup / 'repair.json').write_text(json.dumps(log, ensure_ascii=False, indent=2))
        print('Dataset restaurado:', source, '| Archivos:', len(changed), '| Respaldo:', backup)
        return result
