"""Self-contained Colab startup, also embedded in the notebooks before imports."""
import importlib
from itertools import islice
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
from zipfile import ZipFile


PROJECT_FILES = (
    'scripts/flujo_colab.py', 'scripts/entrenar_yolo26.py', 'scripts/preparar_datasets_reales.py',
    'requirements-datasets.txt', 'requirements-vision.txt',
)


def iniciar_colab(*, drive_home='/content/drive/MyDrive', content='/content', mount=True):
    """Find a complete project, or install the local bundle without replacing data."""
    drive_home, content = Path(drive_home), Path(content)
    if mount:
        try:
            from google.colab import drive
        except ImportError:
            drive = None
        if drive is not None:
            drive.mount(str(drive_home.parent))

    default_root = drive_home / 'Tesis_IOT_Papa'
    configured = os.environ.get('IOTTESIS_ROOT')
    requested = Path(configured).expanduser().resolve() if configured else None
    # The previous notebook set this default even when the folder did not exist.
    explicit = requested is not None and requested != default_root.resolve()
    bases = [requested] if explicit else [default_root, drive_home / 'IOTtesis',
                                         content / 'IOTtesis', content / 'Tesis_IOT_Papa',
                                         Path.cwd(), *Path.cwd().parents]

    def ready(path):
        return all((path / name).is_file() for name in PROJECT_FILES)

    candidates = list(bases)
    for base in bases:
        candidates.extend(base / name for name in ('Tesis_IOT_Papa', 'IOTtesis'))
        if base.name == 'notebooks':
            candidates.append(base.parent)
    root = next((p.resolve() for p in candidates if ready(p)), None)
    if root is None and not explicit and drive_home.is_dir():
        # Bounded discovery: renamed project folders, and one enclosing folder.
        discovered = set()
        for folder in islice(drive_home.iterdir(), 200):
            if folder.name.startswith('.') or not folder.is_dir():
                continue
            for candidate in (folder, folder / 'Tesis_IOT_Papa', folder / 'IOTtesis'):
                if ready(candidate):
                    discovered.add(candidate.resolve())
        if len(discovered) > 1:
            raise RuntimeError('Hay varios proyectos. Define os.environ["IOTTESIS_ROOT"] con uno de: '
                               + ', '.join(str(p) for p in sorted(discovered)))
        root = next(iter(discovered), None)

    if root is None:
        zip_override = os.environ.get('IOTTESIS_ZIP')
        archives = ([Path(zip_override).expanduser()] if zip_override else
                    [base / 'colab_yolo26_listo.zip' for base in (drive_home, content, Path.cwd())])
        archive = next((p for p in archives if p.is_file()), None)
        if archive is None:
            raise RuntimeError(
                'No se encontró el proyecto completo ni el ZIP.\n'
                'Sube colab_yolo26_listo.zip a Mi unidad y vuelve a ejecutar esta celda.\n'
                f'ZIP esperado: {archives[0]}\n'
                'Si usas otras rutas, define os.environ["IOTTESIS_ROOT"] con la carpeta '
                'que contiene scripts/ y os.environ["IOTTESIS_ZIP"] con el archivo ZIP.\n'
                f'Carpeta de proyecto esperada: {requested or default_root}')
        root = requested if requested is not None else (
            default_root if drive_home.is_dir() else
            (content if content.is_dir() else Path.cwd()) / 'Tesis_IOT_Papa')
        root = root.resolve()
        with ZipFile(archive) as package:
            entries = []
            seen = set()
            for member in package.infolist():
                path = PurePosixPath(member.filename)
                parts = path.parts
                if ('\\' in member.filename or path.is_absolute() or '..' in parts
                        or not parts or parts[0] != 'Tesis_IOT_Papa'
                        or stat.S_ISLNK(member.external_attr >> 16)):
                    raise ValueError('Ruta inválida en el ZIP: ' + member.filename)
                if len(parts) == 1 or member.is_dir():
                    continue
                relative = PurePosixPath(*parts[1:])
                if (relative.parts[0] not in {'scripts', 'notebooks', 'data', 'docs',
                                             'requirements-datasets.txt', 'requirements-vision.txt',
                                             'EMPEZAR_AQUI.txt'}
                        or any(part.startswith('.') for part in relative.parts)
                        or relative.suffix.lower() in {'.pt', '.db', '.sqlite3', '.key', '.pem'}):
                    raise ValueError('Archivo ajeno al paquete de Colab: ' + str(relative))
                target = root / str(relative)
                if relative in seen or not target.resolve().is_relative_to(root):
                    raise ValueError('Ruta repetida o externa en el ZIP: ' + str(relative))
                seen.add(relative)
                entries.append((member, target, relative.parts[0] == 'data'))
            if not all(PurePosixPath(name) in seen for name in PROJECT_FILES):
                raise ValueError('El ZIP no contiene el flujo completo. Usa colab_yolo26_listo.zip actualizado.')
            # Check all paths before writing; never follow existing linked directories.
            for _, target, _ in entries:
                if target.is_symlink() or any(p.is_symlink() for p in target.parents if p != root and p.is_relative_to(root)):
                    raise ValueError('Destino enlazado: ' + str(target))
                if target.exists() and not target.is_file():
                    raise ValueError('El destino no es un archivo: ' + str(target))
            preserved = 0
            for member, target, is_data in entries:
                if is_data and target.exists():
                    preserved += 1
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with package.open(member) as source, target.open('wb') as destination:
                    shutil.copyfileobj(source, destination)
        print('Proyecto extraído desde:', archive)
        if preserved:
            print('Datos existentes conservados:', preserved, '| Verifícalos en 00, celda 4.')

    os.environ['IOTTESIS_ROOT'] = str(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    importlib.invalidate_caches()
    print('Proyecto:', root)
    return root
