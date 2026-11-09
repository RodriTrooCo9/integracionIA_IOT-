"""
Vistas de Django para el Panel Web Hiperinteractivo del Invernadero
Proyecto de Tesis - La Paz, Bolivia
"""

import csv
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

from .models import NodoSensor, DeteccionVision, EventoAlarma, AuditoriaControlPID, ExperimentoEnsayo
from .services import (
    ESTADO_GEMELO_DIGITAL, PERFILES_FENOLOGICOS, actualizar_gemelo_digital,
    ejecutar_autotune_pid, obtener_explicacion_riesgo_shap,
    calcular_psicrometria, obtener_recomendacion_mip
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Intentar importar servicios del servidor backend
try:
    from server.app.services.vision_service import (
        vision_service, VisionUnavailable, obtener_servicio_modelo,
        obtener_resumen_modelos_entrenados, procesar_trampa_amarilla_colorimetria
    )
    from server.app.services.mqtt_client import mqtt_service
    from server.app.core.config import settings as server_settings
    BACKEND_DISPONIBLE = True
except Exception:
    BACKEND_DISPONIBLE = False

# Muestras reales verificadas del repositorio para prueba inmediata en 1 clic
MUESTRAS_DATASET_REALES = {
    "plantdoc_tizon_tardio": {
        "id": "plantdoc_tizon_tardio",
        "titulo": "Hoja con Tizón Tardío (PlantDoc Test)",
        "subtitulo": "Phytophthora infestans · Detección de cajas",
        "ruta": REPO_ROOT / "data" / "processed" / "papa_plantdoc_yolo" / "images" / "test" / "11c98ab2be295c0cfebf03fc.jpg",
        "tipo_origen": "HOJA_FOLLAJE",
        "modelo_sugerido": "yolo26n_plantdoc_detect",
        "usar_sahi": False,
    },
    "plantdoc_tizon_temprano": {
        "id": "plantdoc_tizon_temprano",
        "titulo": "Hoja con Tizón Temprano (PlantDoc Test)",
        "subtitulo": "Alternaria solani · Detección multi-caja",
        "ruta": REPO_ROOT / "data" / "processed" / "papa_plantdoc_yolo" / "images" / "test" / "02f0dc21ed2f80fb4ab4d8df.jpg",
        "tipo_origen": "HOJA_FOLLAJE",
        "modelo_sugerido": "yolo26n_plantdoc_detect",
        "usar_sahi": False,
    },
    "plantvillage_hoja_sana": {
        "id": "plantvillage_hoja_sana",
        "titulo": "Hoja Sana de Papa (PlantVillage Test)",
        "subtitulo": "Solanum tuberosum · Clasificación Top-1",
        "ruta": REPO_ROOT / "data" / "processed" / "papa_plantvillage_clasificacion" / "test" / "hoja_sana" / "0df518de395ebcac6b87894d.jpg",
        "tipo_origen": "HOJA_FOLLAJE",
        "modelo_sugerido": "yolo26n_plantvillage_classify",
        "usar_sahi": False,
    },
    "trampa_amarilla_pulgon": {
        "id": "trampa_amarilla_pulgon",
        "titulo": "Trampa Cromática Amarilla ( vectores )",
        "subtitulo": "Inspección morfocromática HSV de micro-insectos",
        "ruta": REPO_ROOT / "data" / "raw" / "trampas" / "pulgon" / "trampa_pulgon_001.ppm",
        "tipo_origen": "TRAMPA_AMARILLA",
        "modelo_sugerido": "heuristica_trampa",
        "usar_sahi": True,
    },
}

FIGURAS_TESIS_CATALOGO = [
    {"archivo": "fig_fopdt_ajuste_escalon.png", "titulo": "Identificación Dinámica Térmica FOPDT", "categoria": "Control PID (E2)"},
    {"archivo": "fig_optuna_convergencia.png", "titulo": "Convergencia Bayesiana Optuna TPE (ITAE)", "categoria": "Control PID (E3)"},
    {"archivo": "fig_comparativa_sintonias_pid.png", "titulo": "Comparativa Ziegler-Nichols vs Cohen-Coon vs Optuna", "categoria": "Control PID (E3)"},
    {"archivo": "fig_comparativa_onoff_vs_pid.png", "titulo": "Desempeño Lazo Cerrado PID vs Control On-Off", "categoria": "Control PID (E4)"},
    {"archivo": "fig_comparativa_map_modelos.png", "titulo": "Comparativa de Precisión mAP@0.5 entre Arquitecturas YOLO", "categoria": "Visión IA (E5)"},
    {"archivo": "fig_matriz_confusion_vision.png", "titulo": "Matriz de Confusión de Diagnóstico Fitosanitario", "categoria": "Visión IA (E5)"},
    {"archivo": "fig_sahi_mejora_objetos_pequenos.png", "titulo": "Ganancia de Recall con Slicing SAHI en Micro-objetos", "categoria": "Visión IA + SAHI (E6)"},
    {"archivo": "fig_latencia_vs_map_cpu.png", "titulo": "Frontera de Pareto: Latencia CPU vs mAP@0.5", "categoria": "Visión IA (E5/E6)"},
    {"archivo": "fig_blightmanager_vs_ml_roc.png", "titulo": "Curva ROC: Fusión Multimodal vs Reglas Clásicas", "categoria": "Riesgo Climático (E7)"},
    {"archivo": "fig_curvas_calibracion_probabilidad.png", "titulo": "Calibración de Probabilidad y Brier Score", "categoria": "Riesgo Climático (E7)"},
    {"archivo": "fig_shap_importancia_bioclimatica.png", "titulo": "Importancia Explicable SHAP de Variables Bioclimáticas", "categoria": "Explicabilidad IA (E7)"},
    {"archivo": "fig_simulacion_fusion_lazo_externo.png", "titulo": "Respuesta del Lazo Supervisor en Cascada 24/7", "categoria": "Integración Total (E8)"},
]


def _ruta_a_media_url(ruta_str: str) -> str:
    """Convierte una ruta absoluta o relativa en disco en una URL servible bajo /media/."""
    if not ruta_str:
        return ""
    p = Path(ruta_str)
    media_root = Path(settings.MEDIA_ROOT)
    try:
        rel = p.resolve().relative_to(media_root.resolve())
        return f"{settings.MEDIA_URL}{rel.as_posix()}"
    except Exception:
        candidate = media_root / p.name
        if candidate.is_file():
            return f"{settings.MEDIA_URL}{p.name}"
        return f"{settings.MEDIA_URL}{p.name}"


def _enriquecer_detecciones(queryset):
    """Agrega atributos listos para plantilla (URL de imagen, cajas parseadas y recomendación MIP)."""
    items = []
    for d in queryset:
        d.url_imagen_anotada = _ruta_a_media_url(d.ruta_imagen_anotada or d.ruta_imagen_original)
        d.url_imagen_original = _ruta_a_media_url(d.ruta_imagen_original)
        try:
            cajas = json.loads(d.bbox_json) if d.bbox_json else []
        except Exception:
            cajas = []
        d.cajas_lista = cajas
        d.total_cajas = len(cajas)
        d.nombre_legible = (d.clase_detectada or "sin_deteccion").replace("_", " ").title()
        d.mip = obtener_recomendacion_mip(d.clase_detectada, d.severidad_porcentaje, d.conteo_insectos)
        items.append(d)
    return items


# ------------------------------------------------------------------------------
# 1. Vistas de Renderizado de Páginas HTML
# ------------------------------------------------------------------------------
def index(request):
    """Vista principal: KPIs en vivo, semáforo explicado y telemetría."""
    estado = actualizar_gemelo_digital()
    explicacion = obtener_explicacion_riesgo_shap(estado["score_riesgo"], estado["hum_interior"], estado["vpd_kpa"])
    ultimas_alarmas = EventoAlarma.objects.order_by('-timestamp')[:5]
    ultimas_detecciones = _enriquecer_detecciones(DeteccionVision.objects.order_by('-timestamp')[:4])

    context = {
        "estado": estado,
        "explicacion": explicacion,
        "perfiles_fenologicos": PERFILES_FENOLOGICOS,
        "alarmas": ultimas_alarmas,
        "detecciones": ultimas_detecciones,
        "titulo": "Panel de Control y Monitoreo en Vivo"
    }
    return render(request, "dashboard/index.html", context)


def control_pid_view(request):
    """Vista de control de setpoints, ganancias PID y autotuning."""
    estado = actualizar_gemelo_digital()
    auditorias = AuditoriaControlPID.objects.order_by('-timestamp')[:10]
    context = {
        "estado": estado,
        "perfiles_fenologicos": PERFILES_FENOLOGICOS,
        "auditorias": auditorias,
        "titulo": "Control PID, Setpoints y Autotuning"
    }
    return render(request, "dashboard/control_pid.html", context)


def vision_view(request):
    """Vista de visión artificial: visor de inferencias YOLO+SAHI y subida interactiva."""
    detecciones = _enriquecer_detecciones(DeteccionVision.objects.order_by('-timestamp')[:24])
    modelos_entrenados = obtener_resumen_modelos_entrenados() if BACKEND_DISPONIBLE else []
    context = {
        "detecciones": detecciones,
        "modelos_entrenados": modelos_entrenados,
        "muestras_reales": list(MUESTRAS_DATASET_REALES.values()),
        "titulo": "Visor de Patologías y Plagas (YOLO26 / YOLO11 + SAHI)"
    }
    return render(request, "dashboard/vision.html", context)


def gemelo_digital_view(request):
    """Vista del Gemelo Digital interactivo con inyección de perturbaciones."""
    estado = actualizar_gemelo_digital()
    context = {
        "estado": estado,
        "perfiles_fenologicos": PERFILES_FENOLOGICOS,
        "titulo": "Gemelo Digital del Invernadero y Simulación de Perturbaciones"
    }
    return render(request, "dashboard/gemelo_digital.html", context)


def experimentos_view(request):
    """Tablero de experimentos científicos E1 a E8 con exportación y galería de figuras."""
    ensayos_qs = ExperimentoEnsayo.objects.order_by('codigo_experimento')
    # Garantizar unicidad por código E1..E8 en vista y parsear métricas JSON para presentación limpia
    vistos = set()
    ensayos = []
    for e in ensayos_qs:
        if e.codigo_experimento in vistos:
            continue
        vistos.add(e.codigo_experimento)
        try:
            e.metricas_dict = json.loads(e.metricas_resumen_json) if e.metricas_resumen_json else {}
        except Exception:
            e.metricas_dict = {}
        ensayos.append(e)

    context = {
        "ensayos": ensayos,
        "figuras_tesis": FIGURAS_TESIS_CATALOGO,
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
def api_aplicar_fenologia(request):
    """Aplica el perfil de setpoints correspondiente a la fase fenológica de la papa."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
    try:
        data = json.loads(request.body.decode("utf-8"))
        fase = data.get("fase", "FLORACION").upper()
        if fase not in PERFILES_FENOLOGICOS:
            return JsonResponse({"status": "error", "message": "Fase fenológica no válida"}, status=400)

        perfil = PERFILES_FENOLOGICOS[fase]
        sp_ant = ESTADO_GEMELO_DIGITAL["sp_temperatura"]
        ESTADO_GEMELO_DIGITAL["fase_fenologica"] = fase
        ESTADO_GEMELO_DIGITAL["sp_temperatura"] = perfil["sp_temperatura"]
        ESTADO_GEMELO_DIGITAL["sp_humedad"] = perfil["sp_humedad"]
        ESTADO_GEMELO_DIGITAL["hum_suelo"] = perfil["vwc_optimo_pct"]

        AuditoriaControlPID.objects.create(
            usuario_origen="PERFIL_FENOLOGICO_PAPA",
            variable_control="SETPOINTS_FENOLOGIA",
            sp_anterior=sp_ant,
            sp_nuevo=perfil["sp_temperatura"],
            justificacion=f"Fase {perfil['nombre']} -> SP_Temp: {perfil['sp_temperatura']}°C, SP_Hum: {perfil['sp_humedad']}%, VWC: {perfil['vwc_optimo_pct']}%"
        )

        return JsonResponse({
            "status": "success",
            "fase": fase,
            "perfil": perfil,
            "mensaje": f"Perfil '{perfil['nombre']}' aplicado con éxito."
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
    """Ejecuta simulación de autotune Cohen-Coon, IMC u Optuna y devuelve ganancias recomendadas."""
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


def api_modelos_vision(request):
    """Devuelve la lista de modelos entrenados en Colab y sus métricas verificadas."""
    if not BACKEND_DISPONIBLE:
        return JsonResponse({"status": "error", "modelos": []}, status=503)
    return JsonResponse({
        "status": "success",
        "modelos": obtener_resumen_modelos_entrenados(),
        "muestras": [
            {k: v for k, v in m.items() if k != "ruta"}
            for m in MUESTRAS_DATASET_REALES.values()
        ]
    })


@csrf_exempt
def api_subir_imagen_vision(request):
    """
    Recibe una imagen subida desde el navegador web (o un ID de muestra real del dataset),
    la pasa al servicio de inferencia del backend (YOLO26 / YOLO11 / SAHI),
    persiste el resultado en SQLite y devuelve las rutas/URLs de la imagen original y anotada.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

    muestra_id = request.POST.get("muestra_id", "").strip()
    if "imagen" not in request.FILES and not muestra_id:
        return JsonResponse({"status": "error", "message": "Se requiere archivo de imagen o seleccionar una muestra."}, status=400)

    if not BACKEND_DISPONIBLE:
        return JsonResponse({"status": "error", "message": "Backend de visión no disponible"}, status=503)

    tipo_origen = request.POST.get("tipo_origen", "HOJA_FOLLAJE")
    usar_sahi = request.POST.get("usar_sahi", "false").lower() == "true"
    modelo_id = request.POST.get("modelo_id", "").strip()
    nodo_camara_id = request.POST.get("nodo_camara", "cam_web_upload").strip() or "cam_web_upload"

    media_root = Path(settings.MEDIA_ROOT)
    media_root.mkdir(parents=True, exist_ok=True)
    ts_prefix = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Guardar imagen en MEDIA_ROOT (desde archivo subido o desde muestra verificada)
    if "imagen" in request.FILES:
        archivo = request.FILES["imagen"]
        suffix = Path(archivo.name).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp", ".ppm", ".bmp"}:
            suffix = ".jpg"
        nombre_guardado = default_storage.save(f"{ts_prefix}_{uuid4().hex[:8]}{suffix}", archivo)
        ruta_completa = Path(default_storage.path(nombre_guardado))
    else:
        muestra = MUESTRAS_DATASET_REALES.get(muestra_id)
        if not muestra or not Path(muestra["ruta"]).is_file():
            return JsonResponse({"status": "error", "message": "Muestra de dataset no encontrada"}, status=404)
        tipo_origen = request.POST.get("tipo_origen") or muestra["tipo_origen"]
        if not modelo_id:
            modelo_id = muestra["modelo_sugerido"]
        if "usar_sahi" not in request.POST:
            usar_sahi = muestra["usar_sahi"]
        origen_path = Path(muestra["ruta"])
        # Si es .ppm, convertir a .jpg para visualización directa en cualquier navegador
        nombre_guardado = f"{ts_prefix}_{muestra_id}.jpg"
        ruta_completa = media_root / nombre_guardado
        if origen_path.suffix.lower() == ".ppm":
            import cv2
            img_ppm = cv2.imread(str(origen_path))
            cv2.imwrite(str(ruta_completa), img_ppm)
        else:
            shutil.copy2(origen_path, ruta_completa)

    # 2. Ejecutar inferencia en el motor seleccionado
    try:
        if modelo_id == "heuristica_trampa" or (
            tipo_origen == "TRAMPA_AMARILLA" and request.POST.get("auto_trampa_hsv", "false").lower() == "true"
        ):
            res = procesar_trampa_amarilla_colorimetria(str(ruta_completa), usar_sahi=usar_sahi)
        else:
            servicio = vision_service if not modelo_id else obtener_servicio_modelo(modelo_id)
            res = servicio.procesar_imagen(str(ruta_completa), tipo_origen=tipo_origen, usar_sahi=usar_sahi)
    except VisionUnavailable as exc:
        ruta_completa.unlink(missing_ok=True)
        return JsonResponse({"status": "error", "message": str(exc)}, status=503)
    except ValueError as exc:
        ruta_completa.unlink(missing_ok=True)
        return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    except Exception as exc:
        ruta_completa.unlink(missing_ok=True)
        return JsonResponse({"status": "error", "message": f"Error en inferencia: {exc}"}, status=500)

    # 3. Registrar en base de datos SQLite
    cam_nodo, _ = NodoSensor.objects.get_or_create(
        nodo_id=nodo_camara_id,
        defaults={"nombre": f"Cámara ({nodo_camara_id})", "descripcion": "Captura desde Dashboard Web / Invernadero"}
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

    try:
        detecciones_lista = json.loads(res.get("bbox_json", "[]"))
    except Exception:
        detecciones_lista = []

    recomendacion_mip = obtener_recomendacion_mip(
        res["clase_detectada"], res["severidad_porcentaje"], res["conteo_insectos"]
    )

    return JsonResponse({
        "status": "success",
        "id": registro.id,
        "timestamp": registro.timestamp.strftime("%d/%m/%Y %H:%M:%S") if registro.timestamp else datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "nodo_camara": nodo_camara_id,
        "tipo_origen": tipo_origen,
        "clase_detectada": res["clase_detectada"],
        "clase_legible": res["clase_detectada"].replace("_", " ").title(),
        "confianza": res["confianza"],
        "conteo_insectos": res["conteo_insectos"],
        "severidad_porcentaje": res["severidad_porcentaje"],
        "tiempo_ms": res["tiempo_inferencia_ms"],
        "ruta_original": res["ruta_imagen_original"],
        "ruta_anotada": res.get("ruta_imagen_anotada", ""),
        "url_original": _ruta_a_media_url(res["ruta_imagen_original"]),
        "url_anotada": _ruta_a_media_url(res.get("ruta_imagen_anotada", "")),
        "severidad_disponible": res["severidad_disponible"],
        "conteo_disponible": res["conteo_disponible"],
        "tarea_modelo": res["tarea_modelo"],
        "semantica_cajas": res.get("semantica_cajas", "whole_leaf"),
        "pesos_utilizados": res.get("pesos_utilizados", modelo_id or "yolo26n_plantdoc_detect"),
        "procesado_con_sahi": res["procesado_con_sahi"],
        "simulado": res["simulado"],
        "total_cajas": len(detecciones_lista),
        "detecciones_lista": detecciones_lista,
        "recomendacion_mip": recomendacion_mip,
    })


def servir_figura_tesis(request, nombre_figura: str):
    """Sirve de forma segura las figuras científicas generadas en thesis/figuras/."""
    nombre_limpio = Path(nombre_figura).name
    ruta = REPO_ROOT / "thesis" / "figuras" / nombre_limpio
    if not ruta.is_file() or ruta.suffix.lower() != ".png":
        raise Http404("Figura no encontrada")
    return FileResponse(open(ruta, "rb"), content_type="image/png")


def exportar_experimentos_csv(request):
    """Exporta los ensayos E1 a E8 a un archivo CSV descargable."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="experimentos_invernadero_papa_{datetime.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Codigo', 'Nombre Ensayo', 'Tratamiento', 'Fecha Inicio', 'Fecha Fin', 'Duracion (Horas)', 'Observaciones', 'Metricas JSON'])

    vistos = set()
    for e in ExperimentoEnsayo.objects.order_by('codigo_experimento'):
        if e.codigo_experimento in vistos:
            continue
        vistos.add(e.codigo_experimento)
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
