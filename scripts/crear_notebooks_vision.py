#!/usr/bin/env python3
"""Generate the ordered Colab workflow, with numbered executable cells."""
import argparse
import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
NAMES = {
    '00': '00_inicio_y_datasets.ipynb',
    '01': '01_entrenar_clasificador.ipynb',
    '02': '02_entrenar_detector.ipynb',
    '03': '03_comparar_detectores.ipynb',
    '04': '04_evaluacion_y_exportacion.ipynb',
}


def md(source):
    return {'cell_type': 'markdown', 'metadata': {}, 'source': (dedent(source).strip() + '\n').splitlines(keepends=True)}


def step(title, source, description='', kind='setup', optional=False):
    return [md(f"## {title}\n\n{description}"), {
        'cell_type': 'code', 'metadata': {'workflow': {'title': title, 'kind': kind, 'optional': optional}},
        'execution_count': None, 'outputs': [],
        'source': (dedent(source).strip() + '\n').splitlines(keepends=True),
    }]


def bootstrap_source():
    # The first cell must work before scripts/ exists in the runtime.
    return (ROOT / 'scripts/iniciar_colab.py').read_text() + '\nPROJECT_ROOT = iniciar_colab()\n'


def gpu_source():
    return dedent('''
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError('No hay una GPU CUDA disponible. En Colab selecciona GPU T4 en el tipo de entorno y vuelve a ejecutar las celdas 1, 2 y 3.')
        DEVICE = 0
        print('GPU:', torch.cuda.get_device_name(DEVICE), '| Dispositivo CUDA:', DEVICE)
    ''').strip() + '\n'


def repair_source(source):
    return (ROOT / 'scripts/reparar_dataset_colab.py').read_text() + f"\nrepair_dataset(PROJECT_ROOT, '{source}')\n"


def configuration_source(source):
    return dedent('''
        if 'PROJECT_ROOT' not in globals():
            raise RuntimeError('El entorno perdió sus variables. Ejecuta las celdas 1, 2 y 3 de este cuaderno y luego repite la 4.')
        import json
        from scripts.entrenar_yolo26 import training_plan
        from scripts.flujo_colab import (
            inspect_progress, print_progress, run_or_reuse, latest_experiment,
            freeze_detector, final_records, evaluate_once, comparable_detectors, write_summary,
        )
    ''').strip() + '\n' + gpu_source() + dedent(source).strip() + '\n'


def setup_cells(data_only=False):
    requirement = 'requirements-datasets.txt' if data_only else 'requirements-vision.txt'
    return [*step('Conectar Drive y localizar o extraer el proyecto', bootstrap_source(),
         'Repetir en cada cuaderno y después de reiniciar el entorno. Sube `colab_yolo26_listo.zip` '
         'a Mi unidad: si falta el proyecto, esta celda lo extrae automáticamente. '
         'Conserva los datos existentes y no escribe en `runs/`. Para otras rutas, define '
         '`IOTTESIS_ROOT` (carpeta que contiene `scripts/`) o `IOTTESIS_ZIP` (archivo ZIP). '
         'Ningún cuaderno depende de las variables de otro.'),
        *step('Instalar dependencias de esta sesión', f'''
        %pip install -q -r "{{PROJECT_ROOT / '{requirement}'}}"
    ''', 'Instala en el entorno actual. En 00 solo se instalan dependencias de datos; no se necesita GPU.' if data_only else
         'Instala visión en la sesión actual. Si ya se había importado otra versión de Ultralytics, reinicia el kernel y vuelve a empezar.'),
        *step('Comprobar entorno y cargar el flujo', '''
        import json
        from scripts.flujo_colab import inspect_progress, print_progress
        print_progress(inspect_progress(PROJECT_ROOT))
    ''' if data_only else dedent('''
        import json
        import torch
        import ultralytics
        from scripts.entrenar_yolo26 import training_plan
        from scripts.flujo_colab import (
            inspect_progress, print_progress, run_or_reuse, latest_experiment,
            freeze_detector, final_records, evaluate_once, comparable_detectors, write_summary,
        )
        if tuple(int(v) for v in ultralytics.__version__.split('.')[:2]) < (8, 4):
            raise RuntimeError('Instala Ultralytics >=8.4.0 y reinicia el kernel.')
    ''') + gpu_source() + dedent('''
        print('Ultralytics:', ultralytics.__version__, '| PyTorch:', torch.__version__, '| Dispositivo:', DEVICE)
        print_progress(inspect_progress(PROJECT_ROOT))
    '''), 'El estado se calcula a partir de datasets y checkpoints guardados; ejecutar una celda no cuenta como entrenamiento completado. '
         'En 01–04 selecciona GPU T4. Cambiar el entorno reinicia las variables: repite las celdas 1–3.')]


def start():
    return [md('''
        # 00 · EMPIEZA AQUÍ: proyecto, datasets y pendientes
        **Primero ejecuta este cuaderno. No entrena modelos.**

        Ruta corta: **00 → 01 → 02 → 04**.
        Para comparación de tesis: **00 → 01 → 02 → 03 → 04**.

        - PlantVillage: clasificación de tres clases.
        - PlantDoc: detector de hojas completas, dos enfermedades; no mide lesiones.
        - PID está en `control/`; riesgo climático demostrativo está en `riesgo/`.
        - `archivo/` conserva cuadernos anteriores y no es parte de la ruta actual.
        - Copiar archivos a Drive no ejecuta ni entrena nada.
    '''), *setup_cells(data_only=True),
        *step('Preparar o verificar ambos datasets',
              (ROOT / 'scripts/reparar_dataset_colab.py').read_text() + dedent('''
        import subprocess
        for source, folder in [('plantvillage', 'papa_plantvillage_clasificacion'), ('plantdoc', 'papa_plantdoc_yolo')]:
            if (PROJECT_ROOT / 'data/processed' / folder / 'manifest.json').is_file():
                repair_dataset(PROJECT_ROOT, source)
        subprocess.run([sys.executable, str(PROJECT_ROOT / 'scripts/preparar_datasets_reales.py'),
                        '--root', str(PROJECT_ROOT), '--source', 'all'], check=True)
        state = inspect_progress(PROJECT_ROOT)
        print_progress(state)
        if any(d['estado'] != 'listo' for d in state['datasets'].values()):
            raise RuntimeError('Los datasets no están listos. Revisa la salida del preparador.')
    '''), 'Si copiaste los datasets locales, se verifican y se reutilizan. Si hay archivos dañados, '
         'se restauran desde el ZIP de la misma partición, con respaldo en data/repair_backups/. '
         'Si faltan datasets, se descargan fuentes reales. '
         'No se borran particiones existentes ni se reemplazan imágenes fallidas por dibujos.', kind='data'),
        md('''
        ## Qué ejecutar después
        Si faltan pesos: abre **01_entrenar_clasificador.ipynb** en una sesión con GPU T4.
        Después ejecuta **02_entrenar_detector.ipynb**. Para comparar familias continúa
        con **03_comparar_detectores.ipynb**; para usar solo YOLO26 pasa a **04**.
        Al abrir otro cuaderno, repite sus tres celdas de inicio.

        Los datasets preparados son pilotos públicos. Falta revisión agronómica y
        un test propio del invernadero para afirmar desempeño de campo.
    ''')]


def training_notebook(source):
    is_classifier = source == 'plantvillage'
    number = '01' if is_classifier else '02'
    title = 'Entrenar clasificador YOLO26' if is_classifier else 'Entrenar detector YOLO26'
    artifact = 'yolo26n-cls.pt' if is_classifier else 'yolo26n.pt'
    detail = ('Clasifica una imagen de hoja en tres clases: sana, tizón tardío o temprano. '
              'El orden de clases se obtiene de las carpetas.' if is_classifier else
              'Localiza hojas completas con dos enfermedades. No detecta insectos ni calcula '
              'porcentaje de lesión a partir del tamaño de la hoja.')
    next_notebook = '02_entrenar_detector.ipynb' if is_classifier else '03_comparar_detectores.ipynb (opcional) o 04_evaluacion_y_exportacion.ipynb'
    return [md(f'''
        # {number} · {title}
        **Requisito:** ejecutar 00 para disponer del dataset verificado.
        {detail}

        Este cuaderno entrena y consulta validación. **No evalúa test**.
        Si ya hay una ejecución completa con la misma configuración, la reutiliza.
    '''), *setup_cells(),
        *step('Fijar la configuración y verificar el plan', configuration_source(repair_source(source) + dedent(f'''
        FAMILY = 'yolo26'
        EPOCHS = 50
        BATCH = {16 if is_classifier else 8}
        REENTRENAR = False  # True solo para iniciar otra ejecución deliberadamente.
        REANUDAR = True  # Recupera last.pt compatible y conserva respaldo.
        PERMITIR_CPU = False
        plan = training_plan(PROJECT_ROOT, '{source}', FAMILY, epochs=EPOCHS, batch=BATCH)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    ''')), f'Perfil GPU T4: dispositivo CUDA 0 y lote {16 if is_classifier else 8}. '
         'Verifica y restaura archivos dañados desde el ZIP, conservando respaldo y manifiesto. '
         f'Plan sin entrenamiento ni descarga de pesos. Checkpoint inicial esperado: `{artifact}`. '
         'Cambiar epochs/familia crea otro experimento; mantenerlos conserva la comparación.', kind='configuration'),
        *step('Entrenar o reutilizar una ejecución completa', '''
        import importlib
        from scripts import entrenar_yolo26 as training_module, flujo_colab as flow_module
        importlib.reload(training_module)
        importlib.reload(flow_module)
        run_or_reuse = flow_module.run_or_reuse
        record = run_or_reuse(plan, device=DEVICE, retrain=REENTRENAR,
                             allow_cpu=PERMITIR_CPU, resume=REANUDAR)
        print('Pesos:', record['best_weights'])
        print('Validación:', record['validation'])
        print('Clases:', record['names'])
    ''', 'Esta es la celda que entrena en GPU si no existe ya una ejecución equivalente. '
         'Con REANUDAR=True recupera last.pt compatible, con respaldo previo. '
         'Si ya terminó y falta el registro, completa la validación y los metadatos.', kind='train'),
        *step('Comprobar que quedaron guardados los resultados', f'''
        saved = latest_experiment(PROJECT_ROOT, '{source}', FAMILY, plan=plan)
        if saved is None:
            raise RuntimeError('Aún no existe un experimento completo para esta configuración.')
        print('Checkpoint:', saved['best_weights'])
        print('Registro:', saved['record_path'])
        print('Test:', 'guardado anteriormente' if 'test' in saved else 'reservado para el cuaderno 04')
        print_progress(inspect_progress(PROJECT_ROOT))
    ''', 'Comprueba archivos reales, tarea, familia, hash del checkpoint y procedencia del dataset. '
         'Se puede volver a ejecutar después de reiniciar la sesión.', kind='check'),
        md(f'''
        ## Siguiente paso
        Abre **{next_notebook}**. Guarda `best.pt`, `best.metadata.json` y `experiment.json`.
        No copies este modelo al ESP32: la inferencia se ejecuta en el servidor.
    ''')]


def comparison():
    return [md('''
        # 03 · Comparar detectores — OPCIONAL
        Requisito: dataset PlantDoc verificado en 00. Es recomendable completar 02;
        su ejecución YOLO26 se reutiliza si tiene la misma configuración.
        Compara YOLO26, YOLO11 y YOLOv8 sin inventar métricas.
        **Selecciona con validación; no toca test**. Usa 04 para la evaluación final.
        Si solo necesitas YOLO26, omite este cuaderno.
    '''), *setup_cells(),
        *step('Fijar la comparación', configuration_source(repair_source('plantdoc') + dedent('''
        FAMILIES = ['yolo26', 'yolo11', 'yolov8']
        EPOCHS = 50
        BATCH = 8
        REENTRENAR = False
        REANUDAR = True
        PERMITIR_CPU = False
        plans = [training_plan(PROJECT_ROOT, 'plantdoc', family, epochs=EPOCHS, batch=BATCH)
                 for family in FAMILIES]
        print([(p['family'], p['epochs'], p['batch'], p['images']) for p in plans])
    ''')), 'Perfil GPU T4: dispositivo CUDA 0 y lote 8. La celda importa training_plan explícitamente. '
         'Restaura imágenes dañadas desde el ZIP compatible y guarda respaldo. '
         'Mismas particiones, semilla, lote, épocas, tamaño, SGD y scheduler cosine. '
         'No cambies estos parámetros entre familias para la misma comparación.', kind='configuration'),
        *step('Entrenar solo las familias que falten', '''
        import importlib
        from scripts import entrenar_yolo26 as training_module, flujo_colab as flow_module
        importlib.reload(training_module)
        importlib.reload(flow_module)
        run_or_reuse = flow_module.run_or_reuse
        records = [run_or_reuse(plan, device=DEVICE, retrain=REENTRENAR,
                               allow_cpu=PERMITIR_CPU, resume=REANUDAR)
                   for plan in plans]
        for record in records:
            print(record['family'], record['validation'], record['best_weights'])
    ''', 'Puede iniciar dos o tres entrenamientos, según lo que ya esté guardado. '
         'No vuelve a entrenar YOLO26 de 02 si la configuración coincide. '
         'REANUDAR=True continúa checkpoints compatibles desde la época guardada; respalda antes de modificar.', kind='train', optional=True),
        *step('Seleccionar por validación y guardar la decisión', '''
        winner = freeze_detector(records, PROJECT_ROOT)
        print('Seleccionado por mAP50-95 de validación:', winner['family'])
        print('Pesos:', winner['best_weights'])
        print('Selección:', PROJECT_ROOT / 'runs/datasets_reales/seleccion_por_validacion.json')
    ''', 'No se declara un ganador anticipadamente y no se consulta test para elegirlo. '
         'La referencia se guarda con una ruta portable para abrir 04 en otra sesión.', kind='selection'),
        md('''
        ## Siguiente paso
        Abre **04_evaluacion_y_exportacion.ipynb**. Allí se cargarán el clasificador
        de 01 y el detector seleccionado aquí. Si deseas reportar todas las familias
        en test, puedes evaluarlas una vez después de congelar esta selección;
        no vuelvas a elegir el ganador a partir de esos resultados.
    ''')]


def evaluation():
    return [md('''
        # 04 · Evaluación final y entrega de modelos
        Requisitos: 01 y 02 completos. Si ejecutaste 03, se utiliza su selección
        por validación. Si lo omitiste, se utiliza YOLO26 elegido de antemano.
        **No entrena modelos.** Recupera los registros desde disco, aunque abras
        una sesión nueva de Colab. Test requiere confirmar que fijaste los modelos.
    '''), *setup_cells(),
        *step('Recuperar modelos guardados y fijar la evaluación', configuration_source('''
        FAMILY_CLASIFICADOR = 'yolo26'
        FAMILY_DETECTOR = 'yolo26'
        USAR_COMPARACION_SI_EXISTE = True
        CONFIRMAR_MODELOS_FIJADOS = False  # Cambiar a True tras revisar validación.
        records = final_records(PROJECT_ROOT, FAMILY_CLASIFICADOR, FAMILY_DETECTOR,
                                use_comparison=USAR_COMPARACION_SI_EXISTE)
        for record in records:
            print(record['task'], record['family'], record['best_weights'])
            print('Validación:', record['validation'])
    '''), 'Evaluación en GPU. Revisa las rutas y las métricas de validación. Si todavía vas a cambiar '
         'parámetros o comparar familias, vuelve a 01–03 y no ejecutes test.', kind='configuration'),
        *step('Evaluar test final una vez', '''
        evaluated = [evaluate_once(record, confirmed=CONFIRMAR_MODELOS_FIJADOS, device=DEVICE)
                     for record in records]
        for record in evaluated:
            print(record['task'], record['family'], 'TEST:', record['test'])
    ''', 'Si test ya está registrado, se muestra sin volver a evaluarlo. '
         'Si falta y la confirmación anterior sigue en False, la celda se detiene con instrucciones.', kind='test'),
        *step('Guardar resumen y mostrar archivos de entrega', '''
        directory = PROJECT_ROOT / 'runs/datasets_reales'
        summary = write_summary(evaluated, PROJECT_ROOT)
        for record in evaluated:
            best = Path(record['best_weights'])
            print('PESOS:', best)
            print('METADATOS:', best.with_suffix('.metadata.json'))
            print('REGISTRO:', Path(record['save_dir']) / 'experiment.json')
        print('Resumen:', summary)
        print_progress(inspect_progress(PROJECT_ROOT))
    ''', 'Clasificación y detección son tareas diferentes: no comparar accuracy con mAP '
         'como si fueran la misma métrica. El registro conserva resultados y versiones.', kind='delivery'),
        *step('Evaluar los demás detectores de 03 — OPCIONAL', '''
        EVALUAR_OTROS_DETECTORES = False
        if EVALUAR_OTROS_DETECTORES:
            reference = next(r for r in records if r['task'] == 'detect')
            others = comparable_detectors(PROJECT_ROOT, reference)
            existing = {r['best_weights'] for r in evaluated}
            evaluated += [evaluate_once(r, confirmed=CONFIRMAR_MODELOS_FIJADOS, device=DEVICE)
                          for r in others if r['best_weights'] not in existing]
            print('Resumen ampliado:', write_summary(evaluated, PROJECT_ROOT))
        else:
            print('Omitido: solo se evalúan el clasificador y el detector seleccionado.')
    ''', 'Solo después de congelar la selección en 03. No vuelve a elegir el ganador '
         'a partir del test ni entrena familias faltantes.', kind='test', optional=True),
        *step('Medir latencia CPU — OPCIONAL', '''
        MEDIR_LATENCIA_CPU = False
        if MEDIR_LATENCIA_CPU:
            from scripts.entrenar_yolo26 import benchmark_cpu
            for record in evaluated:
                print(record['task'], benchmark_cpu(record, samples=10))
        else:
            print('Omitido: no es necesario para obtener best.pt.')
    ''', 'Usa imágenes de validación, calentamiento y tiempo medido; no inicia entrenamiento.', kind='benchmark', optional=True),
        *step('Exportar ONNX — OPCIONAL', '''
        EXPORTAR_ONNX = False
        if EXPORTAR_ONNX:
            import subprocess
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'onnx', 'onnxruntime'], check=True)
            from ultralytics import YOLO
            for record in evaluated:
                output = YOLO(record['best_weights']).export(format='onnx', imgsz=record['imgsz'], device='cpu')
                print('ONNX:', output)
        else:
            print('Omitido: el backend actual puede usar directamente los pesos .pt.')
    ''', 'Solo si necesitas ONNX. Su salida no sustituye automáticamente el modelo .pt '
         'ni configura el backend.', kind='export', optional=True),
        md('''
        ## Qué queda después de este cuaderno
        Copia al servidor el checkpoint que vayas a usar y su archivo de metadatos.
        Configura `MODEL_WEIGHTS_PATH` con la ruta real y verifica una imagen propia.
        Los pilotos foliares no calculan daño por segmentación ni incluyen insectos.
        Falta test local de invernadero, revisión agronómica y validación de integración.
        No se envían órdenes al ESP32 desde estos cuadernos.
    ''')]


GENERATORS = {'00': start, '01': lambda: training_notebook('plantvillage'),
              '02': lambda: training_notebook('plantdoc'), '03': comparison, '04': evaluation}


def write_notebook(path, cells):
    import copy
    cells = copy.deepcopy(cells)
    index = 0
    for position, cell in enumerate(cells):
        if cell['cell_type'] == 'code':
            index += 1
            workflow = cell['metadata']['workflow']
            workflow['step'] = index
            title = workflow['title']
            heading = f"Celda {index:02d} · {title}"
            cells[position - 1]['source'][0] = '## ' + heading + '\n'
            cell['source'].insert(0, f'# {heading}\n')
    document = {'cells': cells, 'metadata': {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python'}, 'workflow': {'numbered_code_cells': index}},
        'nbformat': 4, 'nbformat_minor': 4}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=1) + '\n')
    print(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--notebook', choices=[*GENERATORS, '05', 'all'], default='all')
    args = parser.parse_args()
    # Old invocation --notebook 05 now generates the separated training notebooks.
    selected = ['01', '02'] if args.notebook == '05' else list(GENERATORS) if args.notebook == 'all' else [args.notebook]
    for number in selected:
        write_notebook(ROOT / 'notebooks' / NAMES[number], GENERATORS[number]())


if __name__ == '__main__':
    main()
