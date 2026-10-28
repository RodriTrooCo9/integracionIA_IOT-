"""Bounded, validated image storage shared by both HTTP frontends."""
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np

from server.app.core.config import settings


class ImageValidationError(ValueError):
    pass


def guardar_imagen(stream):
    data = stream.read(settings.MAX_UPLOAD_BYTES + 1)
    if not data or len(data) > settings.MAX_UPLOAD_BYTES:
        raise ImageValidationError("Imagen vacía o superior al límite permitido")
    # Check dimensions before full decode to limit decompression memory.
    from PIL import Image
    import io
    try:
        with Image.open(io.BytesIO(data)) as probe:
            if probe.format not in {"JPEG", "PNG"}:
                raise ImageValidationError("Solo se permiten imágenes JPEG y PNG")
            if probe.width * probe.height > settings.MAX_IMAGE_PIXELS:
                raise ImageValidationError("Resolución de imagen demasiado grande")
            probe.verify()
    except (OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise ImageValidationError("Archivo de imagen inválido") from exc
    img = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ImageValidationError("No se pudo decodificar la imagen")
    directory = Path(settings.UPLOAD_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{uuid4().hex}.jpg"
    if not cv2.imwrite(str(path), img):
        raise OSError("No se pudo guardar la imagen")
    return path
