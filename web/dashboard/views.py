"""
Vistas de Django para el Panel Web Hiperinteractivo del Invernadero
Proyecto de Tesis - La Paz, Bolivia
"""

import csv
import json
import time
from datetime import datetime
from pathlib import Path

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from asgiref.sync import async_to_sync
from pydantic import ValidationError
from .security import operator_required
from server.app.api.endpoints import SetpointsRequest, PIDRequest
from server.app.services.operations import comandar_control, inferir_y_registrar
from server.app.services.storage import guardar_imagen, ImageValidationError
from server.app.services.vision_service import VisionUnavailable
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import default_storage

from .models import NodoSensor, DeteccionVision, EventoAlarma, AuditoriaControlPID, ExperimentoEnsayo
from .services import (
    ESTADO_GEMELO_DIGITAL, actualizar_gemelo_digital, ejecutar_autotune_pid,
    obtener_explicacion_riesgo_shap, calcular_psicrometria
)

from server.app.core.config import settings as server_settings

# ------------------------------------------------------------------------------
# 1. Vistas de Renderizado de Páginas HTML
# ------------------------------------------------------------------------------
@ensure_csrf_cookie
def index(request):
    """Vista principal: KPIs en vivo, semáforo explicado y telemetría."""
    estado = actualizar_gemelo_digital()
    explicacion = obtener_explicacion_riesgo_shap(estado["score_riesgo"], estado["hum_interior"], estado["vpd_kpa"])
    ultimas_alarmas = EventoAlarma.objects.order_by('-timestamp')[:5]
    ultimas_detecciones = DeteccionVision.objects.order_by('-timestamp')[:6]

    context = {
        "estado": estado,
        "explicacion": explicacion,
        "alarmas": ultimas_alarmas,
        "detecciones": ultimas_detecciones,
        "titulo": "Panel de Control y Monitoreo en Vivo"
    }
    return render(request, "dashboard/index.html", context)

@ensure_csrf_cookie
def control_pid_view(request):
    """Vista de control de setpoints, ganancias PID y autotuning."""
    estado = actualizar_gemelo_digital()
    auditorias = AuditoriaControlPID.objects.order_by('-timestamp')[:8]
    context = {
        "estado": estado,
        "auditorias": auditorias,
        "titulo": "Control PID, Setpoints y Autotuning"
    }
    return render(request, "dashboard/control_pid.html", context)

@ensure_csrf_cookie
def vision_view(request):
    """Vista de visión artificial: visor de inferencias YOLO+SAHI y subida interactiva."""
    detecciones = list(DeteccionVision.objects.order_by('-timestamp')[:24])
    for detection in detecciones:
        detection.imagen_url = FileSystemStorage().url(Path(detection.ruta_imagen_anotada or detection.ruta_imagen_original).name)
    context = {
        "detecciones": detecciones,
        "titulo": "Visor de Patologías y Plagas (YOLO11n + SAHI)"
    }
    return render(request, "dashboard/vision.html", context)

@ensure_csrf_cookie
def gemelo_digital_view(request):
    """Vista del Gemelo Digital interactivo con inyección de perturbaciones."""
    estado = actualizar_gemelo_digital()
    context = {
        "estado": estado,
        "titulo": "Gemelo Digital del Invernadero y Simulación de Perturbaciones"
    }
    return render(request, "dashboard/gemelo_digital.html", context)

def experimentos_view(request):
    """Tablero de experimentos científicos E1 a E8 con exportación."""
    ensayos = ExperimentoEnsayo.objects.order_by('codigo_experimento')
    context = {
        "ensayos": ensayos,
        "titulo": "Tablero de Ensayos Experimentales (E1 a E8)"
    }
    return render(request, "dashboard/experimentos.html", context)

# ------------------------------------------------------------------------------
# 2. Endpoints de API JSON para Interactividad en Vivo (Fetch / Asíncrono)
# ------------------------------------------------------------------------------
def api_telemetria(request):
    """Retorna el estado dinámico del microclima y actuadores para actualizar gráficos en vivo."""
    estado = actualizar_gemelo_digital()
    explicacion = obtener_explicacion_riesgo_shap(estado["score_riesgo"], estado["hum_interior"], estado["vpd_kpa"])
    return JsonResponse({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "estado": estado,
        "explicacion": explicacion
    })

@operator_required
def api_actualizar_setpoints(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    try:
        data = SetpointsRequest.model_validate_json(request.body)
        result = async_to_sync(comandar_control)(
            {'sp_temperatura': data.sp_temperatura, 'sp_humedad': data.sp_humedad},
            f'WEB:{request.user.pk}', data.justificacion)
        return JsonResponse(result, status=200 if result['publicado_mqtt'] else 503)
    except (ValidationError, ValueError) as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)


@operator_required
def api_actualizar_pid(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    try:
        data = PIDRequest.model_validate_json(request.body)
        result = async_to_sync(comandar_control)(
            data.model_dump(), f'WEB:{request.user.pk}', 'Ajuste de ganancias PID',
            topic=server_settings.TOPIC_CONTROL_GANANCIAS)
        return JsonResponse(result, status=200 if result['publicado_mqtt'] else 503)
    except (ValidationError, ValueError) as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)

def api_autotune(request):
    """Ejecuta simulación de autotune Cohen-Coon u Optuna y devuelve ganancias recomendadas."""
    metodo = request.GET.get("metodo", "OPTUNA")
    resultado = ejecutar_autotune_pid(metodo=metodo)
    return JsonResponse(resultado)

@operator_required
def api_cambiar_modo_gemelo(request):
    """Cambia la perturbación ambiental activa en el gemelo digital."""
    if request.method != "POST":
        return JsonResponse({"status": "error"}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
        modo = data.get("modo", "NORMAL").upper()
        if modo in ["NORMAL", "HELADA", "TEMPORAL_NIEBLA", "OLA_CALOR", "PLAGA_PULGON"]:
            ESTADO_GEMELO_DIGITAL["modo_perturbacion"] = modo
            return JsonResponse({"status": "success", "modo": modo})
        return JsonResponse({"status": "error", "message": "Modo no reconocido"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

@operator_required
def api_subir_imagen_vision(request):
    """Recibe imagen desde el navegador web y ejecuta inferencia instantánea."""
    if request.method != "POST" or "imagen" not in request.FILES:
        return JsonResponse({"status": "error", "message": "Se requiere archivo de imagen"}, status=400)

    try:
        path = guardar_imagen(request.FILES['imagen'])
        response = async_to_sync(inferir_y_registrar)(
            path, 'cam_web_upload', request.POST.get('tipo_origen', 'HOJA_FOLLAJE'),
            request.POST.get('usar_sahi', 'false').lower() == 'true')
    except VisionUnavailable as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=503)
    except (ImageValidationError, ValueError) as exc:
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)
    result = response['resultado']
    return JsonResponse({
        'status': 'success', 'id': response['id_registro'], **result,
        'tiempo_ms': result['tiempo_inferencia_ms'],
        'publicado_mqtt': response['publicado_mqtt'],
        'ruta_anotada': FileSystemStorage().url(Path(result['ruta_imagen_anotada']).name),
    })


def exportar_experimentos_csv(request):
    """Exporta los ensayos E1 a E8 a un archivo CSV descargable."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="experimentos_invernadero_papa_{datetime.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Codigo', 'Nombre Ensayo', 'Tratamiento', 'Fecha Inicio', 'Fecha Fin', 'Duracion (Horas)', 'Observaciones', 'Metricas JSON'])

    for e in ExperimentoEnsayo.objects.all():
        writer.writerow([
            e.codigo_experimento,
            e.nombre_ensayo,
            e.tratamiento,
            e.fecha_inicio,
            e.fecha_fin or '',
            e.duracion_horas or '',
            e.observaciones or '',
            e.metricas_resumen_json or ''
        ])

    return response


@operator_required
def media_imagen(request, filename):
    """Serve uploaded images safely even when DEBUG is disabled."""
    from django.http import FileResponse, Http404
    if Path(filename).name != filename or Path(filename).suffix.lower() not in {'.jpg', '.png', '.jpeg'}:
        raise Http404
    path = Path(settings.MEDIA_ROOT) / filename
    if not path.is_file():
        raise Http404
    return FileResponse(path.open('rb'), content_type='image/png' if path.suffix.lower() == '.png' else 'image/jpeg')
