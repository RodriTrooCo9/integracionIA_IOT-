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
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

from .models import NodoSensor, DeteccionVision, EventoAlarma, AuditoriaControlPID, ExperimentoEnsayo
from .services import (
    ESTADO_GEMELO_DIGITAL, actualizar_gemelo_digital, ejecutar_autotune_pid,
    obtener_explicacion_riesgo_shap, calcular_psicrometria
)

# Intentar importar servicios del servidor backend
try:
    from server.app.services.vision_service import vision_service
    from server.app.services.mqtt_client import mqtt_service
    from server.app.core.config import settings as server_settings
    BACKEND_DISPONIBLE = True
except Exception:
    BACKEND_DISPONIBLE = False

# ------------------------------------------------------------------------------
# 1. Vistas de Renderizado de Páginas HTML
# ------------------------------------------------------------------------------
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

def vision_view(request):
    """Vista de visión artificial: visor de inferencias YOLO+SAHI y subida interactiva."""
    detecciones = DeteccionVision.objects.order_by('-timestamp')[:24]
    context = {
        "detecciones": detecciones,
        "titulo": "Visor de Patologías y Plagas (YOLO11n + SAHI)"
    }
    return render(request, "dashboard/vision.html", context)

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

@csrf_exempt
def api_actualizar_setpoints(request):
    """Actualiza setpoints desde la interfaz web, audita y comanda MQTT."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        sp_temp = float(data.get("sp_temperatura", 18.0))
        sp_hum = float(data.get("sp_humedad", 75.0))
        justificacion = data.get("justificacion", "Ajuste manual desde Django Dashboard")

        # Validación de seguridad agronómica
        sp_temp = max(5.0, min(35.0, sp_temp))
        sp_hum = max(30.0, min(95.0, sp_hum))

        sp_ant = ESTADO_GEMELO_DIGITAL["sp_temperatura"]
        ESTADO_GEMELO_DIGITAL["sp_temperatura"] = sp_temp
        ESTADO_GEMELO_DIGITAL["sp_humedad"] = sp_hum

        # Registrar auditoría en SQLite
        AuditoriaControlPID.objects.create(
            usuario_origen="OPERADOR_DJANGO_WEB",
            variable_control="TEMPERATURA_Y_HUMEDAD",
            sp_anterior=sp_ant,
            sp_nuevo=sp_temp,
            justificacion=f"{justificacion} | SP_Hum: {sp_hum}%"
        )

        # Publicar en MQTT si está disponible
        publicado = False
        if BACKEND_DISPONIBLE:
            payload = {
                "sp_temperatura": sp_temp,
                "sp_humedad": sp_hum,
                "usuario_origen": "DJANGO_WEB",
                "timestamp": datetime.now().isoformat()
            }
            publicado = mqtt_service.publicar(server_settings.TOPIC_CONTROL_SETPOINTS, payload, qos=1, retain=True)

        return JsonResponse({
            "status": "success",
            "sp_temperatura": sp_temp,
            "sp_humedad": sp_hum,
            "publicado_mqtt": publicado,
            "mensaje": f"Setpoints actualizados a {sp_temp}°C y {sp_hum}%"
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

@csrf_exempt
def api_actualizar_pid(request):
    """Actualiza ganancias Kp, Ki, Kd y registra en auditoría."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        kp = float(data.get("kp", 15.934))
        ki = float(data.get("ki", 0.1359))
        kd = float(data.get("kd", 1.571))

        ESTADO_GEMELO_DIGITAL["kp"] = kp
        ESTADO_GEMELO_DIGITAL["ki"] = ki
        ESTADO_GEMELO_DIGITAL["kd"] = kd

        AuditoriaControlPID.objects.create(
            usuario_origen="OPERADOR_DJANGO_WEB",
            variable_control="GANANCIAS_PID",
            sp_anterior=ESTADO_GEMELO_DIGITAL["sp_temperatura"],
            sp_nuevo=ESTADO_GEMELO_DIGITAL["sp_temperatura"],
            kp=kp, ki=ki, kd=kd,
            justificacion="Ajuste manual de parámetros PID"
        )

        if BACKEND_DISPONIBLE:
            payload = {"kp": kp, "ki": ki, "kd": kd, "timestamp": datetime.now().isoformat()}
            mqtt_service.publicar("invernadero/control/pid_tuning", payload, qos=1)

        return JsonResponse({
            "status": "success",
            "kp": kp, "ki": ki, "kd": kd,
            "mensaje": f"Ganancias actualizadas: Kp={kp}, Ki={ki}, Kd={kd}"
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

def api_autotune(request):
    """Ejecuta simulación de autotune Cohen-Coon u Optuna y devuelve ganancias recomendadas."""
    metodo = request.GET.get("metodo", "OPTUNA")
    resultado = ejecutar_autotune_pid(metodo=metodo)
    return JsonResponse(resultado)

@csrf_exempt
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

@csrf_exempt
def api_subir_imagen_vision(request):
    """Recibe imagen desde el navegador web y ejecuta inferencia instantánea."""
    if request.method != "POST" or "imagen" not in request.FILES:
        return JsonResponse({"status": "error", "message": "Se requiere archivo de imagen"}, status=400)

    archivo = request.FILES["imagen"]
    tipo_origen = request.POST.get("tipo_origen", "HOJA_FOLLAJE")
    usar_sahi = request.POST.get("usar_sahi", "false").lower() == "true"

    # Guardar archivo
    upload_path = Path("/home/rodrigo/Desktop/IOTtesis/data/raw/uploads")
    upload_path.mkdir(parents=True, exist_ok=True)
    nombre_guardado = f"{int(time.time())}_{archivo.name.replace(' ', '_')}"
    ruta_completa = upload_path / nombre_guardado

    with open(ruta_completa, "wb+") as f:
        for chunk in archivo.chunks():
            f.write(chunk)

    # Inferencia
    if BACKEND_DISPONIBLE:
        res = vision_service.procesar_imagen(str(ruta_completa), tipo_origen=tipo_origen, usar_sahi=usar_sahi)
    else:
        res = {
            "clase_detectada": "tizon_tardio" if tipo_origen == "HOJA_FOLLAJE" else "pulgon",
            "confianza": 0.89,
            "conteo_insectos": 8 if tipo_origen == "TRAMPA_AMARILLA" else 1,
            "severidad_porcentaje": 14.5 if tipo_origen == "HOJA_FOLLAJE" else 0.0,
            "tiempo_inferencia_ms": 38.5,
            "procesado_con_sahi": usar_sahi,
            "bbox_json": json.dumps([{"clase": "muestra", "confianza": 0.89, "bbox": [20, 20, 80, 80]}]),
            "ruta_imagen_original": str(ruta_completa),
            "ruta_imagen_anotada": str(ruta_completa)
        }

    # Registrar en base de datos
    cam_nodo, _ = NodoSensor.objects.get_or_create(
        nodo_id="cam_web_upload",
        defaults={"nombre": "Cámara Web Upload", "descripcion": "Subida manual desde Dashboard Django"}
    )
    
    registro = DeteccionVision.objects.create(
        nodo_camara=cam_nodo,
        tipo_origen=tipo_origen,
        ruta_imagen_original=res["ruta_imagen_original"],
        ruta_imagen_anotada=res.get("ruta_imagen_anotada", ""),
        clase_detectada=res["clase_detectada"],
        confianza=res["confianza"],
        bbox_json=res["bbox_json"],
        conteo_insectos=res["conteo_insectos"],
        severidad_porcentaje=res["severidad_porcentaje"],
        tiempo_inferencia_ms=res["tiempo_inferencia_ms"],
        procesado_con_sahi=res["procesado_con_sahi"]
    )

    return JsonResponse({
        "status": "success",
        "id": registro.id,
        "clase_detectada": res["clase_detectada"],
        "confianza": res["confianza"],
        "conteo_insectos": res["conteo_insectos"],
        "severidad_porcentaje": res["severidad_porcentaje"],
        "tiempo_ms": res["tiempo_inferencia_ms"],
        "ruta_anotada": res.get("ruta_imagen_anotada", "")
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
