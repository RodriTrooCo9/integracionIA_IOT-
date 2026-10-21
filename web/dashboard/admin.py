"""
Configuración del Panel Administrativo de Django (Backoffice de Tesis)
"""

from django.contrib import admin
from .models import NodoSensor, DeteccionVision, EventoAlarma, AuditoriaControlPID, ExperimentoEnsayo

@admin.register(NodoSensor)
class NodoSensorAdmin(admin.ModelAdmin):
    list_display = ('nodo_id', 'nombre', 'estado', 'ip_asignada', 'firmware_version', 'creado_en')
    search_fields = ('nodo_id', 'nombre', 'ip_asignada')
    list_filter = ('estado',)

@admin.register(DeteccionVision)
class DeteccionVisionAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'nodo_camara', 'tipo_origen', 'clase_detectada', 'confianza', 'conteo_insectos', 'severidad_porcentaje', 'procesado_con_sahi')
    list_filter = ('tipo_origen', 'clase_detectada', 'procesado_con_sahi')
    search_fields = ('clase_detectada', 'nodo_camara__nombre')
    readonly_fields = ('timestamp',)

@admin.register(EventoAlarma)
class EventoAlarmaAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'tipo_evento', 'nivel_severidad', 'mensaje', 'notificado_telegram')
    list_filter = ('nivel_severidad', 'tipo_evento', 'notificado_telegram')
    search_fields = ('mensaje', 'tipo_evento')
    readonly_fields = ('timestamp',)

@admin.register(AuditoriaControlPID)
class AuditoriaControlPIDAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'usuario_origen', 'variable_control', 'sp_anterior', 'sp_nuevo', 'kp', 'ki', 'kd')
    list_filter = ('usuario_origen', 'variable_control')
    readonly_fields = ('timestamp',)

@admin.register(ExperimentoEnsayo)
class ExperimentoEnsayoAdmin(admin.ModelAdmin):
    list_display = ('codigo_experimento', 'nombre_ensayo', 'tratamiento', 'fecha_inicio', 'fecha_fin', 'duracion_horas')
    list_filter = ('tratamiento', 'codigo_experimento')
    search_fields = ('codigo_experimento', 'nombre_ensayo')
