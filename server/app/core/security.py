"""Fail-closed authentication for operations exposed by FastAPI."""
import secrets
from fastapi import Header, HTTPException
from server.app.core.config import settings


def require_operator(x_api_key: str = Header(default="")):
    if not settings.API_KEY:
        raise HTTPException(503, "Configure API_KEY para habilitar operaciones")
    if not secrets.compare_digest(x_api_key.encode(), settings.API_KEY.encode()):
        raise HTTPException(401, "Credenciales inválidas")


class RequestGuardMiddleware:
    """Authorize before multipart parsing and bound streamed upload bodies."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        from starlette.responses import JSONResponse
        from starlette.exceptions import HTTPException as StarletteHTTPException
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        mutating = scope.get('method') not in {'GET', 'HEAD', 'OPTIONS'}
        if mutating and scope.get('path', '').startswith(settings.API_V1_STR + '/'):
            headers = dict(scope.get('headers', []))
            try:
                require_operator(headers.get(b'x-api-key', b'').decode('latin1'))
            except HTTPException as exc:
                return await JSONResponse({'detail': exc.detail}, status_code=exc.status_code)(scope, receive, send)
        size = 0

        async def bounded_receive():
            nonlocal size
            message = await receive()
            if scope.get('path') == settings.API_V1_STR + '/vision/inferir':
                size += len(message.get('body', b''))
                if size > settings.MAX_UPLOAD_BYTES + 65536:
                    raise StarletteHTTPException(413, 'Carga demasiado grande')
            return message
        await self.app(scope, bounded_receive, send)
