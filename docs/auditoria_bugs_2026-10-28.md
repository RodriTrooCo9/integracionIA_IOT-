# Auditoría de bugs — 28 de octubre de 2026

## Resultado y alcance

Se identificaron **22 hallazgos**: 13 de prioridad P1 (corregir antes de operar con actuadores o exponer el sistema) y 9 de prioridad P2 (corregir para asegurar resultados, trazabilidad y portabilidad). No se asigna P0 porque no se observó un incidente activo ni se probó hardware real.

Se revisaron los servicios FastAPI, el supervisor, Django, el firmware PlatformIO, el simulador MQTT, la persistencia, Docker Compose, las configuraciones de adquisición y los tests. Esta auditoría no certifica el hardware, los modelos entrenados ni los resultados científicos de los notebooks.

No se modificó el código de funcionamiento ni la base de datos del proyecto. Las pruebas usaron SQLite y archivos en directorios temporales; Telegram estuvo deshabilitado y no se enviaron comandos a dispositivos.

## Verificación realizada

- Suite existente: **23 passed, 1 warning**, en 3,09 segundos, con el esquema SQL y los ocho ensayos inicializados en una base temporal. Una ejecución previa sin los ensayos produjo el fallo esperado de exportación CSV; no se contabiliza como bug independiente.
- `docker compose config --quiet`: correcto. Esto valida la configuración, no construye ni prueba los contenedores.
- `web/manage.py check`: sin incidencias.
- Flake8 sobre `server`, `web`, `scripts` y `tests`, seleccionando E9/F63/F7/F82: sin errores.
- TOML de Telegraf: sintácticamente válido; no se ejecutó el agente.
- Comprobaciones adicionales con modelos y clientes simulados: resultados consignados en los hallazgos.

El entorno local usa Python 3.14.4, FastAPI 0.157.0, Pydantic 2.14.1, Django 6.1.2, paho-mqtt 2.1.0 y OpenCV 5.0.0.93. **No coincide con las versiones fijadas en los requirements.** Por ello, el éxito de pytest no confirma que funcione una instalación limpia de las dependencias declaradas.

No se compiló el firmware: PlatformIO no está instalado. No se construyó la imagen Docker ni se probaron sensores, broker, InfluxDB o Telegram reales. Se distinguen abajo las pruebas ejecutadas de la evidencia estática.

## Hallazgos P1

### 1. El fallo del sensor no detiene ni limita el calefactor

**Evidencia estática:** `firmware/esp32_control/src/main.cpp:113`, `:125`, `:409`.

Si falla el SHT31, solo se pone `sensores_ok=false`; el bucle continúa ejecutando el PID con la última temperatura filtrada. Una lectura congelada por debajo del setpoint mantiene error positivo y puede llevar la calefacción a saturación. El watchdog se sigue refrescando y no detecta esta situación.

**Corrección:** gestionar antigüedad y validez de las lecturas, aplicar un estado seguro explícito y límites térmicos independientes del control normal. Probar desconexión del sensor durante calefacción.

### 2. El ESP32 no puede autenticarse en el broker configurado

**Evidencia estática:** `firmware/esp32_control/src/main.cpp:288`; `config/mosquitto/mosquitto.conf:14`.

Mosquitto exige autenticación y el firmware llama `mqttClient.connect(MQTT_CLIENT_ID)` sin usuario ni contraseña. El nodo queda sin telemetría ni comandos remotos con la configuración del repositorio.

**Corrección:** proporcionar credenciales por dispositivo y pasarlas al conectar. Mantener la autenticación del broker.

### 3. Setpoints y ganancias usan contratos MQTT incompatibles

**Evidencia estática:** `server/app/core/config.py:31`; `server/app/api/endpoints.py:182`; `firmware/esp32_control/include/config_invernadero.h:60`; `firmware/esp32_control/src/main.cpp:250`; `web/dashboard/views.py:179`.

El backend publica en `invernadero/control/setpoints`, pero el firmware escucha `invernadero/control/setpoint`. Además, el backend envía `sp_temperatura`/`sp_humedad` y el firmware lee `sp_temp`/`sp_hum`. Corregir únicamente el tópico deja los comandos sin efecto. Django publica ganancias en `control/pid_tuning`, mientras el ESP32 escucha `control/ganancias`.

**Corrección:** unificar tópicos y esquemas, validar rangos en el dispositivo y agregar una prueba del contrato servidor–firmware con confirmación del valor aplicado.

### 4. Humedad y modo SAFE no influyen en los actuadores

**Evidencia estática:** `firmware/esp32_control/src/main.cpp:53`, `:153`, `:258`, `:273`, `:355`.

El setpoint de humedad solo se almacena; no existe un lazo que lo use. El humidificador y la bomba se inicializan apagados y no vuelven a comandarse. De igual forma, el modo operativo se almacena y publica, pero el PID se ejecuta siempre, incluso si llega `SAFE` o `MANUAL`.

**Corrección:** implementar las transiciones de modo y el control de humedad con interbloqueos, o retirar de la interfaz las funciones todavía no implementadas. SAFE debe gobernar realmente las salidas.

### 5. Las APIs de control están accesibles sin autenticación

**Evidencia estática y tests:** `web/dashboard/views.py:102`, `:152`; `server/app/api/endpoints.py:159`; `web/invernadero_web/settings.py:23`; `Makefile:75`.

Las rutas de escritura no verifican identidad ni permisos. Django además usa `csrf_exempt` en setpoints y ganancias. Las pruebas actualizan ambos sin iniciar sesión. El flujo `make run` publica Django mediante Cloudflare; quien acceda al túnel puede cambiar parámetros. `DEBUG=True`, `ALLOWED_HOSTS=['*']` y la clave de Django incluida en el código agravan la exposición.

**Corrección:** autenticar y autorizar operadores, restaurar CSRF en rutas de navegador y separar configuración de desarrollo y despliegue. Resolverlo antes de habilitar un túnel con control físico operativo.

### 6. Docker requiere una base de datos que no existe en un clon limpio

**Evidencia estática:** `server/Dockerfile:31`; `.gitignore:49`; listado de archivos versionados de `data`.

El Dockerfile copia `data/invernadero_relacional.db`, pero los `.db` están ignorados y ese archivo no está versionado. El workflow de Docker no inicializa la base antes de construir. Un contexto obtenido directamente del repositorio carece del archivo obligatorio para `COPY`.

**Corrección:** copiar el esquema e inicializar la base montada al arrancar; no depender de copiar una base local dentro de la imagen. Probar construcción desde un checkout limpio.

### 7. La imagen del servidor no declara dependencias necesarias para arrancar

**Evidencia estática:** `server/requirements.txt`; `server/Dockerfile:25`; `server/app/services/vision_service.py:9`; `server/app/api/endpoints.py:65`.

El Dockerfile instala `server/requirements.txt`, que omite OpenCV y `python-multipart`. El módulo de visión importa `cv2` incondicionalmente y FastAPI registra una ruta con `File`/`Form`. Las dependencias presentes en el requirements raíz y en la venv local no se transfieren automáticamente al contenedor. Tampoco se declaran Ultralytics/SAHI para inferencia real.

**Corrección:** mantener un conjunto coherente de dependencias del servidor, declarar las de carga e inferencia y probar importación/arranque dentro de la imagen limpia.

### 8. Django publica sin iniciar el cliente MQTT

**Evidencia estática y ejecución:** `web/dashboard/views.py:24`, `:140`; `web/dashboard/services.py:17`; `web/dashboard/apps.py:3`.

El proceso Django importa el singleton MQTT, pero ninguna ruta de arranque llama a `iniciar()`. Esa llamada existe en el lifespan de FastAPI, que no se ejecuta al lanzar Django con `make server` o `make run`. En la comprobación, el hilo de red del cliente siguió siendo `None`.

**Corrección:** establecer un ciclo de vida MQTT para el proceso Django o enviar sus órdenes a FastAPI. Reflejar el fallo de comunicación en la respuesta al operador.

### 9. El fallback YOLO base puede convertir clases generales en enfermedades

**Evidencia estática:** `server/app/services/vision_service.py:34`, `:59`, `:112`.

Si faltan los pesos propios, se carga `yolo11n.pt` y se traducen sus identificadores con el diccionario de clases de papa. El código no verifica que `modelo.names` coincida con ese diccionario. Un modelo con otra taxonomía genera etiquetas fitosanitarias sin fundamento y puede alimentar alarmas y el supervisor.

**Corrección:** exigir pesos compatibles y validar los nombres de clases. El modo demostración debe ser explícito y no accionar el control físico.

### 10. La severidad cuenta hojas sanas como lesión y SAHI omite el área lesionada

**Evidencia estática y ejecución con detector simulado:** `server/app/services/vision_service.py:122`, `:146`, `:194`.

La rama YOLO suma el área de todas las cajas, incluidas `hoja_sana`, y cuenta todas como insectos. Con una sola detección sana cubriendo una imagen de 100×100, devolvió `hoja_sana`, **100% de severidad** y **1 insecto**. La rama SAHI no incrementa `area_lesiones`; una inferencia foliar con SAHI devuelve severidad cero aunque encuentre lesiones.

**Corrección:** separar clases de insectos, lesiones y hojas sanas; calcular una medida de severidad consistente entre inferencias y tratar el solapamiento de regiones. Probar explícitamente hojas sanas y lesiones con ambas rutas.

### 11. El supervisor usa segundos como ventana de horas y nunca recibe LWH del nodo

**Evidencia estática y ejecución:** `server/app/worker.py:34`, `:68`, `:91`, `:98`; `firmware/esp32_control/include/config_invernadero.h:31`; `firmware/esp32_control/src/main.cpp:304`.

La ventana guarda 48 mensajes, no 48 horas: con la telemetría de 1 Hz equivale aproximadamente a 48 segundos. Las últimas 12 muestras representan unos 12 segundos. Además, ni el firmware ni el simulador publican `lwh_continuo_horas`; el supervisor lo convierte en cero y pierde el aporte de 0,50 al riesgo climático.

Con 48 mensajes de 95% HR, VPD 0,1 y visión máxima, el score fue **0,575 / ALTO**. Con ese contrato y entradas físicas acotadas, el score no alcanza el umbral crítico de 0,75.

**Corrección:** calcular duración real de mojado/condiciones húmedas a partir de timestamps, agregar por intervalo y validar la cadencia de entrada. Probar eventos sostenidos de varias horas sin depender de contar mensajes.

### 12. El supervisor sigue decidiendo con información vencida o inválida

**Evidencia estática:** `server/app/worker.py:64`, `:84`.

Se guardan timestamps, pero el cálculo no consulta su antigüedad ni descarta una última detección antigua. Tampoco usa `sensores_ok` del nodo. Al perder cámaras o telemetría, el supervisor puede mantener recomendaciones basadas en un estado que ya no representa al invernadero.

**Corrección:** caducidad por fuente, validación de sensores y estado explícito de datos insuficientes. Diferenciar ausencia de detección de ausencia de información.

### 13. La recuperación del riesgo no restaura setpoints y un envío fallido no se reintenta

**Evidencia estática y ejecución simulada:** `server/app/worker.py:167`, `:177`, `:206`.

Solo se comandan setpoints al entrar en ALTO/CRÍTICO. En una secuencia ALTO → BAJO se publicó únicamente 19,5 °C / 65%; no se publicó la consigna normal. El mensaje queda retenido. Además, se ignora el resultado de `publish()` y se avanza `nivel_actual`: si falla ese envío, permanecer en el mismo nivel no provoca otro intento.

**Corrección:** definir una política de recuperación con histéresis, confirmar publicación/aplicación y conservar comandos pendientes hasta su entrega. Probar caída del broker durante la transición.

## Hallazgos P2

### 14. La plantilla `.env` rompe la pareja de credenciales de Telegraf

**Evidencia estática:** `.env.example:9`; `docker-compose.yml:73`.

La plantilla usa `MQTT_USER`, mientras Compose consulta `MQTT_USERNAME`. Al copiarla, Telegraf toma su usuario por defecto y la contraseña general de la plantilla, en lugar de su pareja de credenciales por defecto. Los clientes locales tampoco cargan esa plantilla de forma uniforme; el simulador solo consulta variables exportadas al proceso.

**Corrección:** definir variables específicas por cliente, uniformar sus nombres y comprobar autenticación después de aplicar el procedimiento documentado.

### 15. Telegraf no extrae el nombre del score publicado por el worker

**Evidencia estática:** `server/app/worker.py:158`; `config/telegraf/telegraf.conf:130`.

El worker publica `score_riesgo`; el parser busca `indice_riesgo`. No existe un mapeo para el campo emitido, por lo que ese score no se ingiere mediante la configuración actual. También conviene verificar los campos ausentes por tópico en el agente real; la sintaxis TOML válida no lo garantiza.

**Corrección:** alinear el esquema publicado y el parser, con fixtures reales de cada tópico y consulta posterior a InfluxDB.

### 16. El callback de desconexión falla con paho-mqtt 2

**Ejecución:** `server/app/services/mqtt_client.py:24`, `:47`.

El cliente selecciona Callback API VERSION2, pero `_on_disconnect` mantiene una firma anterior. Al invocarlo con los argumentos v2 se obtiene `TypeError: ... takes from 4 to 5 positional arguments but 6 were given`. Afecta al entorno local con paho 2.1.0; los requirements fijan 1.6.1.

**Corrección:** adaptar callbacks por versión o fijar una única API soportada. Probar desconexión y reconexión, además del arranque.

### 17. Las detecciones subidas por Django no llegan al supervisor

**Evidencia estática:** `web/dashboard/views.py:216`; `server/app/worker.py:60`.

La ruta Django procesa y guarda la imagen, pero termina sin publicar en `TOPIC_VISION_DETECCIONES`. El supervisor recibe visión exclusivamente por ese tópico. Una detección visible en el panel no modifica el riesgo del worker; la ruta FastAPI sí publica ese evento.

**Corrección:** compartir el flujo de inferencia/persistencia/publicación o delegarlo a FastAPI. Verificar que una carga desde el panel aparezca en la entrada del supervisor.

### 18. El modo heurístico devuelve etiquetas inconsistentes y declara SAHI sin usarlo

**Ejecución y evidencia estática:** `server/app/services/vision_service.py:168`, `:187`, `:197`, `:210`.

La heurística calcula `clase_principal`, pero nunca la agrega a `clases_detectadas`. Una imagen marrón sintética devolvió `hoja_sana` con **100% de severidad**, mientras `bbox_json` contenía `tizon_tardio`. En trampas, la clase final cae en `sin_captura` aunque estime pulgones. Al solicitar SAHI sin modelo disponible, `procesado_con_sahi` devuelve `True` pese a ejecutarse la heurística.

**Corrección:** retornar resultados coherentes y registrar el motor realmente ejecutado, su disponibilidad y el carácter simulado de la detección.

### 19. Repetir la carga de ensayos duplica E1–E8

**Ejecución:** `scripts/seed_experiments.py:53`; `server/app/models/schemas.sql:79`.

`INSERT OR REPLACE` no reemplaza registros porque no hay restricción única sobre su identidad lógica ni se suministra el id. Dos llamadas generaron dos filas por código, 16 ensayos en total. `make run` vuelve a ejecutar la carga.

**Corrección:** definir una clave única adecuada —considerando repeticiones y tratamientos reales— y realizar un upsert explícito de los datos demostrativos. No borrar ensayos reales para resolver la duplicación.

### 20. Las imágenes pueden sobrescribirse y la ruta Django depende de este equipo

**Evidencia estática:** `server/app/api/endpoints.py:78`; `web/dashboard/views.py:228`; `web/dashboard/templates/dashboard/vision.html:131`.

Ambas rutas nombran archivos con precisión de segundos y el nombre original. Dos cargas del mismo nombre durante un segundo usan la misma ruta y pueden sobrescribir originales/anotaciones vinculadas a registros anteriores. Django y su plantilla incluyen además `/home/rodrigo/Desktop/IOTtesis/...`, lo que rompe portabilidad y puede separar el guardado de `MEDIA_ROOT`.

**Corrección:** identificadores únicos por carga, rutas configurables y URLs de medios generadas mediante el almacenamiento de Django. Validar contenido, tamaño y nombres de archivo antes de procesarlos.

### 21. El gemelo avanza por visitas y no representa el PID configurado

**Evidencia estática:** `web/dashboard/services.py:57`, `:85`, `:96`; `web/dashboard/views.py:34`, `:91`.

Cada petición al panel o a telemetría ejecuta un paso con `dt=1`, independientemente del tiempo transcurrido. Más navegadores o refrescos aceleran la simulación compartida; varios procesos mantienen estados distintos. El control solo usa `kp` y un sesgo fijo de 10: cambiar `ki` o `kd` no altera la dinámica. La constante aplicada es 30 s aunque el comentario indica aproximadamente 240 s.

**Corrección:** ejecutar la simulación con reloj y estado definidos, aplicar el controlador/modelo declarado y consultar snapshots desde las vistas. Identificar claramente la fuente simulada en el panel de monitoreo.

### 22. Auditorías y tests pueden aparentar acciones que no ocurrieron

**Evidencia estática y tests:** `server/app/api/endpoints.py:139`, `:190`; `server/app/worker.py:193`; `tests/test_api_endpoints.py:17`; `tests/test_django_web.py:19`.

Se registra `notificado_telegram=True` antes de conocer el resultado del envío; incluso el modo mock o un error de Telegram deja la notificación registrada como realizada. La auditoría FastAPI fija el setpoint anterior en 18 °C y responde `success` aunque MQTT falle. Los tests existentes usan la base configurada del proyecto y escriben auditorías/detecciones; no tienen aislamiento automático ni verifican entrega al ESP32. La auditoría tuvo que proporcionar ese aislamiento externamente.

**Corrección:** distinguir solicitud, publicación, aplicación y notificación confirmada; almacenar el valor anterior real; usar fixtures temporales y verificar los estados fallidos. La falta de configuración de Telegram debe quedar diferenciada de un envío exitoso.

## Orden recomendado

1. Seguridad local: fallos de sensores, estado SAFE e interbloqueos.
2. Autenticación y contrato MQTT completo entre panel, servidor y nodo.
3. Construcción reproducible desde un clon limpio y dependencias coherentes.
4. Corregir clasificación/severidad y proteger el control de resultados simulados.
5. Ventanas temporales, caducidad de datos, recuperación y reintentos del supervisor.
6. Ingesta, ensayos idempotentes, almacenamiento y trazabilidad; ampliar pruebas a los escenarios anteriores.

La suite actual cubre carga de vistas y respuestas básicas, pero no demuestra el funcionamiento del lazo físico completo. Los hallazgos reproducidos con dobles de prueba confirman defectos de lógica; la validación final requiere integración con broker y hardware.
