# Correcciones aplicadas a la auditoría

Fecha: 28 de octubre de 2026.

## Estado

Se aplicaron cambios para los 22 hallazgos del informe original. El control distingue una publicación confirmada por el broker de una aplicación confirmada por el dispositivo; no se presenta la primera como la segunda.

| Hallazgos | Cambio |
| --- | --- |
| 1, 4 | Validación del sensor, apagado de salidas por fallo/SAFE, límite térmico crudo, control de humedad con histéresis y flotador. Bomba de riego permanece deshabilitada por carecer de controlador. Solo se admiten AUTO y SAFE. |
| 2, 3 | Autenticación del ESP32, tópicos/campos uniformes, rangos en dispositivo y comandos con caducidad. Red en tarea independiente y DS18B20 sin espera de conversión. |
| 5 | Cuenta de operador para Django, CSRF activo, validación de ganancias, API key para escrituras FastAPI, DEBUG desactivado y hosts explícitos. |
| 6, 7 | Docker inicializa desde el esquema SQL; dependencias compartidas y compatibles, OpenCV/multipart declarados, inferencia real opcional. Contexto de construcción excluye datos y secretos. |
| 8, 16 | Cliente MQTT iniciado en el proceso Django, inicio idempotente, ids distintos por proceso y callbacks paho 2 correctos. Publicar espera confirmación del broker. |
| 9, 10, 18 | Pesos y taxonomía validados, sin YOLO genérico; lesiones/insectos/sanas separados, unión de cajas sin doble conteo y área también en SAHI. Demo explícita, sin publicaciones ni alarmas físicas. Procedencia persistida. |
| 11, 12 | Duraciones medidas con timestamps, cálculo local de horas húmedas, ventana de 48 h agregada por minuto, rechazo de sensores inválidos/repeticiones y caducidad de fuentes. |
| 13 | Reintentos de órdenes fallidas; recuperación con histéresis y estado supervisor persistido para reinicios. Comandos no retenidos y vigencia de 120 s. |
| 14, 15 | Variables por cliente, credenciales alineadas con hashes existentes, campos opcionales por tópico, score y setpoints normalizados; todas las mediciones usan `telemetria`, como espera Grafana. Datasource y consultas usan bucket configurable. |
| 17 | Django y FastAPI comparten inferencia, persistencia y publicación de eventos reales. |
| 19 | Ledger transaccional de fixtures: las cargas posteriores no duplican ensayos y no borran registros anteriores. |
| 20 | Imágenes JPEG/PNG verificadas, límites de bytes/píxeles, nombres UUID, rutas configurables y acceso a medios con permisos aun con DEBUG desactivado. |
| 21 | Tiempo monotónico, pasos independientes del número de visitantes, términos P/I/D efectivos y constante térmica consistente. El panel declara que usa simulación por proceso. |
| 22 | Estado anterior publicado, desconocido como NULL, auditorías transaccionales, errores de entrega visibles y Telegram confirmado solo con respuesta real `ok=true`. Tests aislados automáticamente. |

## Verificación

- 53 pruebas locales: correctas; incluye contrato MQTT, credenciales contra hashes, rechazo de pesos incompatibles, imágenes sanas, SAHI, caducidad, recuperación y permisos/CSRF.
- Suite con dependencias declaradas dentro de Python 3.11: **53 passed**, con ocho advertencias de deprecación. Suite local: **53 passed**, con una advertencia.
- Imagen `iot-audit-server:test`: construida desde el contexto sin base local ni secretos; comprobado arranque, creación de esquema, rechazo de usuarios sin API key y HTTP 503 con broker ausente.
- Firmware ESP32: compilación PlatformIO correcta; no se cargó a un dispositivo.
- MQTT/Telegraf: validación en red Docker interna y contenedores temporales, mediante `scripts/verificar_integracion_mqtt.py`. La prueba usa contenedores independientes de los servicios del invernadero.
- Django system check, lint crítico, configuración Compose y `git diff --check`: correctos.

El firmware conserva advertencias de bibliotecas de terceros/ArduinoJson deprecado. Los tests producen advertencias de deprecación de TestClient/httpx, sin fallos.

## Base y acceso locales

Se respaldó SQLite antes de aplicar los cambios en `backups/antes_auditoria_20261028_102816.db`. Se preservaron 2 nodos, 12 detecciones, 11 alarmas, 37 auditorías y 80 ensayos. Los duplicados históricos de ensayos se conservaron para no eliminar datos; el nuevo ledger evita nuevas duplicaciones por seed.

Se habilitaron las tablas de autenticación. La cuenta inicial de operador está en `data/credenciales_operador.key`, archivo ignorado por Git y con permisos 0600. No es superusuario. La clave API se generó en `.env`, sin imprimirla ni incluirla en archivos versionados. La clave Django es local, aleatoria y persistente.

## Uso después del cambio

1. Iniciar con `make server`; acceder a `/accounts/login/` usando las credenciales locales. Cambiar la contraseña con `.venv/bin/python web/manage.py changepassword operador_iot`.
2. Para un clon limpio: Python 3.11/3.12, instalar `requirements.txt`, copiar `.env.example`, generar una `API_KEY`, ejecutar `make init-db` y crear un operador con `.venv/bin/python web/manage.py createsuperuser`.
3. Las escrituras FastAPI requieren cabecera `X-API-Key`. Si falta la configuración, quedan deshabilitadas. HTTP 503 significa que no se confirmó publicación al broker.
4. La inferencia real necesita `server/requirements-vision.txt` y pesos propios con las seis clases esperadas en `data/models/yolo11n_papa.pt`. Docker admite `--build-arg INSTALL_VISION=true`. Sin pesos devuelve 503; `VISION_DEMO_MODE=true` habilita únicamente una demostración, sin eventos para el supervisor.
5. Para un túnel, configurar su host en `DJANGO_ALLOWED_HOSTS`, su origen HTTPS en `DJANGO_CSRF_TRUSTED_ORIGINS` y `DJANGO_HTTPS=true`. Iniciar sesión antes de operar. Evitar el servidor de desarrollo para un despliegue permanente.
6. Compilar/cargar el firmware corregido al ESP32 y configurar las credenciales/IP locales. Debe sincronizar su reloj mediante NTP para aceptar comandos. Verificar en hardware la polaridad del flotador y su resistencia pull-up externa; GPIO35 no tiene pull-up interno.

Se recargaron Telegraf y Grafana para activar sus configuraciones corregidas. Grafana respondió con base de datos `ok`. El broker y los volúmenes existentes se conservaron; no se abrió un túnel ni se enviaron órdenes a los actuadores. El firmware compilado debe cargarse al dispositivo para activar sus correcciones físicas.

## Límites físicos y científicos

La severidad basada en detección se identifica como cobertura de cajas de lesión sobre la imagen; no equivale a una segmentación ni a una medición agronómica calibrada. El panel de gemelo y sus explicaciones son demostrativos por proceso. La validación física de sensor desconectado, relés, calefactor, flotador y comunicación completa requiere un ensayo en banco antes de operar el invernadero.

Referencia: [código de SHT31 fijado para la compilación](https://github.com/RobTillaart/SHT31/tree/e5361f60e3f4ea31a7357055f92dee277f3b689f).
