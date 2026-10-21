"""
Modelos ORM de Django vinculados a las tablas de SQLite de la Tesis
Base de datos: data/invernadero_relacional.db
"""

from django.db import models

class NodoSensor(models.Model):
    nodo_id = models.CharField(max_length=32, primary_key=True, verbose_name="ID del Nodo")
    nombre = models.CharField(max_length=64, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    ip_asignada = models.CharField(max_length=45, blank=True, null=True, verbose_name="IP Asignada")
    mac_address = models.CharField(max_length=17, blank=True, null=True, verbose_name="Dirección MAC")
    firmware_version = models.CharField(max_length=16, blank=True, null=True, verbose_name="Versión Firmware")
    estado = models.CharField(max_length=16, default='ACTIVO', verbose_name="Estado")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    class Meta:
        db_table = 'nodos_sensores'
        verbose_name = 'Nodo Sensor / Cámara'
        verbose_name_plural = 'Nodos Sensores y Cámaras'

    def __str__(self):
        return f"{self.nombre} ({self.nodo_id})"

class DeteccionVision(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha / Hora")
    nodo_camara = models.ForeignKey(NodoSensor, on_delete=models.CASCADE, db_column='nodo_camara', verbose_name="Cámara")
    tipo_origen = models.CharField(max_length=16, verbose_name="Tipo de Origen") # 'TRAMPA_AMARILLA', 'HOJA_FOLLAJE'
    ruta_imagen_original = models.TextField(verbose_name="Ruta Imagen Original")
    ruta_imagen_anotada = models.TextField(blank=True, null=True, verbose_name="Ruta Imagen Anotada")
    clase_detectada = models.CharField(max_length=64, verbose_name="Patología / Plaga Detectada")
    confianza = models.FloatField(verbose_name="Confianza [0.0 - 1.0]")
    bbox_json = models.TextField(verbose_name="Coordenadas Bounding Box (JSON)")
    conteo_insectos = models.IntegerField(default=1, verbose_name="Conteo de Individuos")
    severidad_porcentaje = models.FloatField(default=0.0, verbose_name="Severidad Foliar (%)")
    tiempo_inferencia_ms = models.FloatField(blank=True, null=True, verbose_name="Tiempo de Inferencia (ms)")
    procesado_con_sahi = models.BooleanField(default=False, verbose_name="Procesado con SAHI")

    class Meta:
        db_table = 'detecciones_vision'
        ordering = ['-timestamp']
        verbose_name = 'Detección de Visión Artificial'
        verbose_name_plural = 'Detecciones de Visión Artificial'

    def __str__(self):
        return f"{self.clase_detectada} ({self.confianza:.2f}) - {self.timestamp}"

class EventoAlarma(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha / Hora")
    tipo_evento = models.CharField(max_length=32, verbose_name="Tipo de Incidente")
    nivel_severidad = models.CharField(max_length=16, verbose_name="Nivel de Severidad") # INFO, WARNING, CRITICAL
    mensaje = models.TextField(verbose_name="Mensaje de Alerta")
    valor_disparador = models.FloatField(blank=True, null=True, verbose_name="Valor que Disparó la Alerta")
    accion_ejecutada = models.TextField(blank=True, null=True, verbose_name="Acción Automatizada")
    notificado_telegram = models.BooleanField(default=False, verbose_name="Notificado a Telegram")

    class Meta:
        db_table = 'eventos_alarmas'
        ordering = ['-timestamp']
        verbose_name = 'Evento o Alarma del Sistema'
        verbose_name_plural = 'Eventos y Alarmas del Sistema'

    def __str__(self):
        return f"[{self.nivel_severidad}] {self.tipo_evento} - {self.timestamp}"

class AuditoriaControlPID(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha / Hora")
    usuario_origen = models.CharField(max_length=32, default='SISTEMA_IA', verbose_name="Origen del Cambio")
    variable_control = models.CharField(max_length=32, verbose_name="Variable Controlada")
    sp_anterior = models.FloatField(verbose_name="Setpoint Anterior")
    sp_nuevo = models.FloatField(verbose_name="Setpoint Nuevo")
    kp = models.FloatField(blank=True, null=True, verbose_name="Kp")
    ki = models.FloatField(blank=True, null=True, verbose_name="Ki")
    kd = models.FloatField(blank=True, null=True, verbose_name="Kd")
    justificacion = models.TextField(blank=True, null=True, verbose_name="Justificación Técnica")

    class Meta:
        db_table = 'auditoria_control_pid'
        ordering = ['-timestamp']
        verbose_name = 'Auditoría de Control PID'
        verbose_name_plural = 'Auditoría de Control PID'

    def __str__(self):
        return f"{self.usuario_origen}: {self.sp_anterior} -> {self.sp_nuevo} ({self.timestamp})"

class ExperimentoEnsayo(models.Model):
    id = models.AutoField(primary_key=True)
    codigo_experimento = models.CharField(max_length=8, verbose_name="Código Ensayo (E1-E8)")
    nombre_ensayo = models.CharField(max_length=128, verbose_name="Nombre del Experimento")
    tratamiento = models.CharField(max_length=32, verbose_name="Tratamiento")
    fecha_inicio = models.DateTimeField(verbose_name="Fecha Inicio")
    fecha_fin = models.DateTimeField(blank=True, null=True, verbose_name="Fecha Fin")
    duracion_horas = models.FloatField(blank=True, null=True, verbose_name="Duración (Horas)")
    metricas_resumen_json = models.TextField(blank=True, null=True, verbose_name="Métricas Resumen (JSON)")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones Agronómicas")

    class Meta:
        db_table = 'experimentos_ensayos'
        ordering = ['codigo_experimento']
        verbose_name = 'Experimento / Ensayo Científico'
        verbose_name_plural = 'Experimentos y Ensayos Científicos'

    def __str__(self):
        return f"[{self.codigo_experimento}] {self.nombre_ensayo} ({self.tratamiento})"
