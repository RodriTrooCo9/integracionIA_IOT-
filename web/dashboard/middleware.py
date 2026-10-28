"""Start MQTT within the serving process, including prefork WSGI deployments."""
import atexit
from server.app.services.mqtt_client import mqtt_service


class MQTTLifecycleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        atexit.register(mqtt_service.detener)

    def __call__(self, request):
        mqtt_service.iniciar()
        return self.get_response(request)


class UploadGuardMiddleware:
    """Reject unauthenticated uploads before CSRF triggers multipart parsing."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/api/subir-imagen/' and request.method == 'POST':
            from django.http import JsonResponse
            if not request.user.is_authenticated or not request.user.is_active or not request.user.is_staff:
                return JsonResponse({'status': 'error', 'message': 'Acceso de operador requerido'}, status=403)
            from django.core.files.uploadhandler import FileUploadHandler, StopUpload
            from server.app.core.config import settings

            class BoundedUploadHandler(FileUploadHandler):
                total = 0

                def receive_data_chunk(self, raw_data, start):
                    self.total += len(raw_data)
                    if self.total > settings.MAX_UPLOAD_BYTES:
                        raise StopUpload(connection_reset=True)
                    return raw_data

                def file_complete(self, file_size):
                    return None

            request.upload_handlers.insert(0, BoundedUploadHandler(request))
        return self.get_response(request)
