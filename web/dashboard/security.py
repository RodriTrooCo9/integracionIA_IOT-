"""Operator authorization; CSRF remains enforced by Django middleware."""
from functools import wraps
from django.http import JsonResponse


def operator_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Inicie sesión como operador'}, status=401)
        if not request.user.is_active or not request.user.is_staff:
            return JsonResponse({'status': 'error', 'message': 'Permisos de operador requeridos'}, status=403)
        return view(request, *args, **kwargs)
    return wrapped
