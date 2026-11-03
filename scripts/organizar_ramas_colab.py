"""Annotate independent control/risk branches without regenerating saved results."""
import copy
from textwrap import dedent

from scripts.crear_notebooks_vision import bootstrap_source


def _cell(kind, text):
    cell = {'cell_type': kind, 'metadata': {}, 'source': (dedent(text).strip() + '\n').splitlines(keepends=True)}
    if kind == 'code':
        cell.update(execution_count=None, outputs=[])
    return cell


def _setup(branch):
    setup = bootstrap_source() + '\nRUTA_BASE = str(PROJECT_ROOT)\n'
    if branch == 'riesgo':
        return '''EJECUTAR_DEMO_RIESGO = False
if not EJECUTAR_DEMO_RIESGO:
    raise RuntimeError('Rama opcional: faltan datos/etiquetas reales. Para explorar el generador sintético, cambia EJECUTAR_DEMO_RIESGO=True.')
''' + setup
    return setup + "\nOUTPUT_DIR = PROJECT_ROOT / 'runs/control'\nOUTPUT_DIR.mkdir(parents=True, exist_ok=True)\n"


def organize_branch(notebook, branch):
    notebook = copy.deepcopy(notebook)
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            source = source.replace("label=f'Escalón de Potencia", "label=rf'Escalón de Potencia")
            source = source.replace('[✔]', '[OK]').replace('✔ ', '[OK] ').replace('⭐', '[seleccionado]')
            cell['source'] = source.splitlines(keepends=True)
    marker = 'RAMA INDEPENDIENTE · ' + branch.upper()
    if any(marker in ''.join(c['source']) for c in notebook['cells']):
        for cell in notebook['cells']:
            source = ''.join(cell['source'])
            if cell['cell_type'] == 'code' and 'RUTA_BASE = str(PROJECT_ROOT)' in source and 'IOTTESIS_ROOT' in source:
                cell['source'] = _setup(branch).splitlines(keepends=True)
                break
        return notebook
    intro = f'''# {marker}

Este cuaderno no es un requisito de los pasos 00–04 de visión.
Los cuadernos conservados pueden contener salidas de sesiones anteriores;
ejecutar desde el principio en una sesión nueva evita variables fuera de orden.
'''
    if branch == 'riesgo':
        intro += '''\n**DEMOSTRACIÓN SINTÉTICA, no entrenamiento fitopatológico validado.**
Faltan series temporales y etiquetas reales. El generador usa el umbral del
baseline para producir la etiqueta; métricas perfectas no demuestran predicción
real. Solo ejecutar esta rama como demostración consciente.
'''
    else:
        intro += '''\nIdentificación FOPDT y PID: se puede ejecutar en CPU y en paralelo a visión.
Si falta el CSV térmico, el cuaderno genera un ensayo sintético. Las figuras y
tablas se guardan en `runs/control/`; no prueban una calibración de hardware real.
'''
    setup = _setup(branch)
    if branch == 'riesgo':
        dependencies = '%pip install -q scikit-learn xgboost shap torch pandas numpy matplotlib'
    else:
        dependencies = '%pip install -q optuna scipy pandas matplotlib seaborn'
    prefix = [_cell('markdown', intro), _cell('code', setup),
              _cell('markdown', '## Dependencias de esta rama: ejecutar antes de los imports del cuaderno original'),
              _cell('code', dependencies)]
    for cell in notebook['cells']:
        if cell['cell_type'] != 'code':
            continue
        source = ''.join(cell['source'])
        if branch == 'control' and "drive.mount('/content/drive')" in source:
            source = "RUTA_BASE = str(PROJECT_ROOT)\nprint('Proyecto:', RUTA_BASE)\n"
        source = source.replace('Path("../data/synthetic/dataset_agroclimatico_invernadero.csv")',
                                '(PROJECT_ROOT / "data/synthetic/dataset_agroclimatico_invernadero.csv")')
        if branch == 'control':
            for name in ['fig_fopdt_ajuste_escalon.png', 'fig_comparativa_onoff_vs_pid.png', 'tabla_comparativa_controladores.csv']:
                source = source.replace("'" + name + "'", "str(OUTPUT_DIR / '" + name + "')")
        cell['source'] = source.splitlines(keepends=True)
    notebook['cells'] = prefix + notebook['cells']
    notebook['metadata']['workflow'] = {'branch': branch, 'required_for_vision': False,
                                        'synthetic_demo': branch == 'riesgo'}
    return notebook
