"""
Enrutamiento URL para la aplicación Dashboard
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('control-pid/', views.control_pid_view, name='control_pid'),
    path('vision/', views.vision_view, name='vision'),
    path('gemelo-digital/', views.gemelo_digital_view, name='gemelo_digital'),
    path('experimentos/', views.experimentos_view, name='experimentos'),
    path('experimentos/exportar-csv/', views.exportar_experimentos_csv, name='exportar_csv'),
    
    # APIs interactivas
    path('api/telemetria/', views.api_telemetria, name='api_telemetria'),
    path('api/setpoints/', views.api_actualizar_setpoints, name='api_setpoints'),
    path('api/pid/', views.api_actualizar_pid, name='api_pid'),
    path('api/autotune/', views.api_autotune, name='api_autotune'),
    path('api/modo-gemelo/', views.api_cambiar_modo_gemelo, name='api_modo_gemelo'),
    path('api/subir-imagen/', views.api_subir_imagen_vision, name='api_subir_imagen'),
]
