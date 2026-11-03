# Especificación Técnica de Integración Frontend y Plantillas Django
## Prototipo de Sistema Integrado IoT–PID–IA para Cultivo de Papa bajo Invernadero (La Paz, 3600 msnm)

Este documento contiene la especificación completa de variables de contexto, modelos ORM, endpoints de API asíncronos y componentes requeridos en pantalla para la construcción de plantillas HTML externas en Django.

---

## 1. Mapa de Rutas y Enrutamiento de Vistas (`dashboard/urls.py`)

| URL | Nombre de Ruta (`name`) | Vista (`views.py`) | Función |
| :--- | :--- | :--- | :--- |
| `/` | `dashboard:index` | `views.index` | Monitor y telemetría en vivo, semáforo y SHAP |
| `/control-pid/` | `dashboard:control_pid` | `views.control_pid_view` | Setpoints, sintonización PID y autotuning |
| `/vision/` | `dashboard:vision` | `views.vision_view` | Inferencia YOLO/SAHI y galería histórica |
| `/gemelo-digital/` | `dashboard:gemelo_digital` | `views.gemelo_digital_view` | Esquema 2D e inyector de perturbaciones |
| `/experimentos/` | `dashboard:experimentos` | `views.experimentos_view` | Tablero de protocolos científicos E1 a E8 |
| `/experimentos/exportar-csv/` | `dashboard:exportar_csv` | `views.exportar_experimentos_csv` | Descarga de reporte en archivo `.csv` |

---

## 2. Diccionario Maestro `estado` (Compartido en Múltiples Vistas)

Inyectado directamente como `{{ estado }}` en el contexto de Django y devuelto en JSON por el endpoint `/api/telemetria/`:

| Clave / Variable | Tipo | Unidad / Rango | Descripción Agronómica / Técnica |
| :--- | :---: | :---: | :--- |
| `estado.temp_interior` | `float` | `°C` (ej. `18.2`) | Temperatura del aire dentro del invernadero (SHT31) |
| `estado.temp_exterior` | `float` | `°C` (ej. `9.5`) | Temperatura ambiental exterior (estación meteorológica) |
| `estado.hum_interior` | `float` | `%` (ej. `72.0`) | Humedad relativa interior |
| `estado.hum_exterior` | `float` | `%` (ej. `65.0`) | Humedad relativa exterior |
| `estado.temp_suelo` | `float` | `°C` (ej. `16.0`) | Temperatura en zona radicular del cultivo de papa |
| `estado.hum_suelo` | `float` | `%` (ej. `30.5`) | Humedad volumétrica de sustrato/suelo (sensores VWC) |
| `estado.rad_solar` | `float` | `W/m²` (ej. `420.0`) | Radiación solar incidente en el altiplano |
| `estado.sp_temperatura` | `float` | `°C` (ej. `18.0`) | Setpoint actual de temperatura |
| `estado.sp_humedad` | `float` | `%` (ej. `75.0`) | Setpoint actual de humedad relativa |
| `estado.vpd_kpa` | `float` | `kPa` (ej. `0.65`) | Déficit de Presión de Vapor (Banda óptima: 0.5 - 1.2 kPa) |
| `estado.punto_rocio` | `float` | `°C` (ej. `13.1`) | Temperatura de condensación psicrométrica |
| `estado.score_riesgo` | `float` | `[0.0 - 1.0]` | Probabilidad calculada de brote fitopatológico |
| `estado.nivel_riesgo` | `str` | `BAJO` \| `MEDIO` \| `ALTO` \| `CRÍTICO` | Categoría del semáforo agronómico |
| `estado.calefactor_pct` / `estado.actuador_calefactor_ssr` | `float` | `% [0 - 100]` | Modulación de potencia del calefactor cerámico SSR |
| `estado.extractor_pct` / `estado.actuador_extractor` | `float` | `% [0 - 100]` | Velocidad PWM del ventilador extractor |
| `estado.bomba_riego` | `bool` | `True` / `False` | Estado de activación de la electroválvula de riego |
| `estado.actuador_bomba_humedad` | `float` | `% [0 ó 100]` | Porcentaje de accionamiento del riego/nebulizador |
| `estado.kp` | `float` | Adimensional | Ganancia Proporcional activa del lazo térmico |
| `estado.ki` | `float` | `s⁻¹` | Ganancia Integral activa |
| `estado.kd` | `float` | `s` | Ganancia Derivativa activa |
| `estado.modo_perturbacion` | `str` | `NORMAL`, `HELADA`, `TEMPORAL_NIEBLA`, `OLA_CALOR`, `PLAGA_PULGON` | Escenario climático inyectado en el gemelo |

---

## 3. Detalle por Vista: Variables de Contexto y Componentes en Pantalla

### Vista 1: En Vivo / Monitor Principal (`/`)

#### Variables de Contexto Django
```python
context = {
    "estado": estado,                      # Diccionario maestro descrito arriba
    "explicacion": explicacion,            # Diccionario SHAP de explicabilidad agronómica
    "alarmas": ultimas_alarmas,            # QuerySet: EventoAlarma (últimos 5)
    "detecciones": ultimas_detecciones,    # QuerySet: DeteccionVision (últimos 6)
    "titulo": "Panel de Control y Monitoreo en Vivo"
}
```

#### Campos de `explicacion`:
- `explicacion.score_riesgo`: `float` (ej. `0.22`).
- `explicacion.nivel`: `str` (`"BAJO"`, `"MEDIO"`, `"ALTO"`, `"CRÍTICO"`).
- `explicacion.recomendacion_accion`: `str` (Recomendación agronómica textual para el operador).
- `explicacion.factores_shap`: Lista de objetos/diccionarios con:
  - `f.variable`: `str` (ej. `"Humedad Relativa Prolongada (>90%)"`).
  - `f.impacto`: `str` (ej. `"+0.45"` o `"-0.35"`).
  - `f.direccion`: `str` (`"AUMENTA RIESGO"`, `"ALERTA PREVENTIVA"`, `"PROTECTOR"`).
  - `f.explicacion`: `str` (Mecanismo biofísico de la espora/plaga).

#### Lo que debe salir en pantalla:
1. **Header superior / Navbar:** Reloj en vivo (`HH:MM:SS`), badge de conexión ("Papa • La Paz 3600m"), enlaces de navegación.
2. **4 Tarjetas de KPIs Principales:**
   - **Temp. Interior:** Valor actual `{{ estado.temp_interior }} °C`, exterior `{{ estado.temp_exterior }} °C` y setpoint `{{ estado.sp_temperatura }} °C`.
   - **Humedad Interior:** Valor actual `{{ estado.hum_interior }} %`, punto de rocío `{{ estado.punto_rocio }} °C` y setpoint `{{ estado.sp_humedad }} %`.
   - **Déficit de Presión de Vapor (VPD):** Valor actual `{{ estado.vpd_kpa }} kPa` y leyenda de banda óptima (`0.5 - 1.2 kPa`).
   - **Semáforo Fitosanitario:** Nivel `{{ estado.nivel_riesgo }}`, Score `{{ estado.score_riesgo }}`, luz indicadora con color según severidad y recomendación de acción.
3. **2 Gráficos de Telemetría en Tiempo Real (Chart.js):**
   - **Gráfico Térmico:** Curvas de `Temp Interior`, `Temp Exterior` y línea de `Setpoint`.
   - **Gráfico Higrométrico:** Curvas de `Humedad Interior`, `Punto de Rocío` y línea de `Setpoint`.
4. **Estado de Actuadores Split-Range:**
   - Barra de progreso y porcentaje de `Calefactor SSR` (`{{ estado.calefactor_pct }}%`).
   - Barra de progreso y porcentaje de `Extractor PWM` (`{{ estado.extractor_pct }}%`).
   - Indicador de modo: `"AUTÓNOMO (PID Borde)"`.
5. **Panel de Explicabilidad Agronómica (SHAP):**
   - Lista iterativa de `{% for f in explicacion.factores_shap %}` mostrando el factor, badge de dirección (verde si protege, rojo si aumenta riesgo), impacto numérico y explicación biológica.

---

### Vista 2: Control PID y Setpoints (`/control-pid/`)

#### Variables de Contexto Django
```python
context = {
    "estado": estado,          # Diccionario maestro
    "auditorias": auditorias,  # QuerySet: AuditoriaControlPID (últimos 8)
    "titulo": "Control PID, Setpoints y Autotuning"
}
```

#### Campos de cada elemento `a` en `auditorias` (`AuditoriaControlPID`):
- `a.timestamp`: `datetime` (Fecha y hora del cambio, formato `Y-m-d H:i:s`).
- `a.usuario_origen`: `str` (ej. `"OPERADOR_DJANGO_WEB"` o `"SISTEMA_IA"`).
- `a.variable_control`: `str` (`"TEMPERATURA_Y_HUMEDAD"` o `"GANANCIAS_PID"`).
- `a.sp_anterior`: `float` (Valor antes del cambio).
- `a.sp_nuevo`: `float` (Nuevo valor aplicado).
- `a.kp`, `a.ki`, `a.kd`: `float` (Ganancias registradas si aplicó al controlador).
- `a.justificacion`: `str` (Motivo del cambio para trazabilidad agronómica).

#### Lo que debe salir en pantalla:
1. **Control de Setpoints Agronómicos:**
   - Slider de $SP_{temp}$ (Rango: `8.0 °C` a `28.0 °C`, paso `0.5`, valor: `{{ estado.sp_temperatura }}`).
   - Slider de $SP_{hum}$ (Rango: `40 %` a `95 %`, paso `1`, valor: `{{ estado.sp_humedad }}`).
   - Campo de texto para justificación de cambio (para auditoría).
   - Botón `"Guardar Setpoints"` (Dispara `POST /api/setpoints/`).
2. **Ajuste Manual de Ganancias PID:**
   - Inputs numéricos para $K_p$ (Proporcional), $K_i$ (Integral) y $K_d$ (Derivativo).
   - Ecuación del firmware visible: $u(t) = K_p e(t) + K_i \int e(\tau)d\tau + K_d \frac{de}{dt}$.
   - Botón `"Actualizar Ganancias"` (Dispara `POST /api/pid/`).
3. **Módulo de Autotuning FOPDT:**
   - Botón `"Optuna Bayesian (ITAE)"` (Llama a `GET /api/autotune/?metodo=OPTUNA`).
   - Botón `"Cohen-Coon Clásico"` (Llama a `GET /api/autotune/?metodo=COHEN_COON`).
   - Tarjetas de resultados de sintonía: Método, $K_p$, $K_i$, $K_d$ calculados.
   - Botón `"Aplicar"` para transferir los valores a los inputs del controlador.
4. **Tabla de Trazabilidad y Auditoría:**
   - Columnas: Fecha/Hora, Origen, Variable, Anterior, Nuevo, Kp/Ki/Kd, Justificación.
   - Filas vacías controladas con `{% empty %}`.

---

### Vista 3: Visión Artificial y Patologías (`/vision/`)

#### Variables de Contexto Django
```python
context = {
    "detecciones": detecciones,   # QuerySet: DeteccionVision (últimos 24)
    "titulo": "Visor de Patologías y Plagas (YOLO26 / YOLO11 + SAHI)"
}
```

#### Campos de cada elemento `d` en `detecciones` (`DeteccionVision`):
- `d.id`: `int` (ID primario).
- `d.timestamp`: `datetime` (Fecha y hora).
- `d.nodo_camara_id`: `str` (ej. `"cam_fija_01"` o `"cam_web_upload"`).
- `d.tipo_origen`: `str` (`"HOJA_FOLLAJE"` o `"TRAMPA_AMARILLA"`).
- `d.ruta_imagen_original`: `str` (Ruta en disco del archivo original).
- `d.ruta_imagen_anotada`: `str` (Ruta de la imagen con cajas delimitadoras).
- `d.clase_detectada`: `str` (ej. `"tizon_tardio"`, `"pulgon_alado"`, `"hoja_sana"`).
- `d.confianza`: `float` (`0.0` a `1.0`, ej. `0.94`).
- `d.bbox_json`: `str` (Coordenadas en JSON `[x1, y1, x2, y2]`).
- `d.conteo_insectos`: `int` (Número de individuos detectados en trampas).
- `d.severidad_porcentaje`: `float` (`%` de área foliar necrosada).
- `d.tiempo_inferencia_ms`: `float` (Latencia del modelo en ms).
- `d.procesado_con_sahi`: `bool` (`True` si utilizó slicing por ventanas).

#### Lo que debe salir en pantalla:
1. **Formulario de Inferencia en Tiempo Real:**
   - Selector: `"Hoja / Follaje"` o `"Trampa Cromática Amarilla"`.
   - Switch / Checkbox: `"Slicing SAHI (Micro-objetos)"`.
   - Selector de archivo fotográfico (`accept="image/*"`).
   - Botón `"Ejecutar Inferencia YOLO"` (Dispara `POST /api/subir-imagen/`).
2. **Panel de Resultados Inmediatos:**
   - Estado vacío inicial con mensaje de ayuda.
   - Diagnóstico Predicho (Clase detectada).
   - Nivel de Confianza (`%`).
   - Métricas: Conteo de insectos (o "No aplica"), Severidad foliar (`%`), Tiempo de inferencia (`ms`).
   - Visor de la imagen anotada con las cajas delimitadoras dibujadas.
3. **Galería Histórica de Detecciones:**
   - Cuadrícula responsive de tarjetas.
   - Miniatura de la imagen (`/media/<nombre_archivo>`).
   - Badge de confianza y badge si fue procesado con `SAHI`.
   - Clase detectada, origen de la cámara, conteo/severidad y fecha (`d/m H:i`).

---

### Vista 4: Gemelo Digital del Invernadero (`/gemelo-digital/`)

#### Variables de Contexto Django
```python
context = {
    "estado": estado,   # Diccionario maestro
    "titulo": "Gemelo Digital del Invernadero y Simulación de Perturbaciones"
}
```

#### Lo que debe salir en pantalla:
1. **Selector de Escenarios y Estrés Agroclimático:**
   - 5 Botones de modos:
     - `NORMAL`: Día templado altiplánico ($18^\circ\text{C}$ / $75\%\text{ HR}$).
     - `HELADA`: Exterior a $-2.5^\circ\text{C}$. Calefactor al máximo.
     - `TEMPORAL_NIEBLA`: Humedad saturada $>95\%$. Riesgo crítico de tizón.
     - `OLA_CALOR`: Interior a $28^\circ\text{C}$. Extractor al $100\%$.
     - `PLAGA_PULGON`: Trampa amarilla $>15$ individuos. Alerta fitosanitaria.
   - Badge que indica el modo activo actual (`{{ estado.modo_perturbacion }}`).
2. **Corte Transversal Esquemático 2D del Invernadero:**
   - **Intemperie / Exterior:** Indicador de temperatura y humedad exterior.
   - **Calefactor Eléctrico SSR:** Porcentaje de potencia activa con ícono animado.
   - **Dosel de Cultivo de Papa:** Tarjeta central con $T_{int}$, $HR_{int}$ y VPD.
   - **Ventilador Extractor:** Porcentaje PWM con ícono animado cuando supera el 20%.
   - **Línea de Suelo y Riego:** Porcentaje de bomba y estado de cámara ESP32-CAM.
3. **Panel Lateral de Fundamento Biofísico:**
   - Ecuación diferencial FOPDT: $\tau \frac{dT(t)}{dt} + T(t) = K \cdot u(t - \theta) + T_{ext}(t)$.
   - Parámetros del modelo: $K = 0.1639\text{ }^\circ\text{C/\%}$, $\tau = 242.96\text{ s}$, $\theta = 33.33\text{ s}$.
   - Tarjeta psicrométrica: Punto de rocío ($T_{dew}$), margen de condensación ($T_{int} - T_{dew}$) y presión atmosférica de La Paz ($67.5\text{ kPa}$).

---

### Vista 5: Ensayos Experimentales (`/experimentos/`)

#### Variables de Contexto Django
```python
context = {
    "ensayos": ensayos,   # QuerySet: ExperimentoEnsayo (E1 a E8)
    "titulo": "Tablero de Ensayos Experimentales (E1 a E8)"
}
```

#### Campos de cada elemento `e` en `ensayos` (`ExperimentoEnsayo`):
- `e.codigo_experimento`: `str` (ej. `"E1"`, `"E2"`, ..., `"E8"`).
- `e.nombre_ensayo`: `str` (Título descriptivo del ensayo).
- `e.tratamiento`: `str` (Configuración o algoritmo probado, ej. `"YOLO11n + SAHI"`).
- `e.fecha_inicio`: `datetime` o `str` (Inicio del ensayo).
- `e.fecha_fin`: `datetime` o `str` (Conclusión del ensayo).
- `e.duracion_horas`: `float` (Horas acumuladas del experimento).
- `e.metricas_resumen_json`: `str` (Resultados cuantitativos en JSON: mAP, IAE, tiempo de subida, etc.).
- `e.observaciones`: `str` (Notas agronómicas e interpretación).

#### Lo que debe salir en pantalla:
1. **Header:** Botón de acción `"Exportar Ensayos (CSV)"` que descarga el archivo generado por `dashboard:exportar_csv`.
2. **4 Tarjetas de Resumen Global:**
   - Total Ensayos: `8 Protocolos`.
   - Horas Acumuladas: `472.0 h`.
   - Disponibilidad del Sistema: `99.8 %`.
   - Mitigación de Heladas: `100 % Éxito`.
3. **Tabla de la Matriz Experimental:**
   - Columnas: Código (badge), Nombre del Ensayo y observaciones, Tratamiento, Duración (`h`), Fechas (rango), Métricas Clave (`metricas_resumen_json` formateado).

---

## 4. Endpoints de API Interactivos (JavaScript / Fetch)

Si tu plantilla externa utiliza JavaScript para actualizar valores dinámicamente sin recargar la página, estos son los contratos de datos:

---

### 1. `GET /api/telemetria/`
- **Uso:** Sondeo periódico en vivo (cada 2 a 3 segundos).
- **Respuesta JSON:**
```json
{
  "timestamp": "14:25:30",
  "estado": {
    "temp_interior": 18.25,
    "temp_exterior": 9.40,
    "hum_interior": 72.1,
    "hum_exterior": 65.0,
    "temp_suelo": 16.0,
    "hum_suelo": 30.5,
    "rad_solar": 420.0,
    "sp_temperatura": 18.0,
    "sp_humedad": 75.0,
    "kp": 15.934,
    "ki": 0.1359,
    "kd": 1.571,
    "calefactor_pct": 24.5,
    "extractor_pct": 0.0,
    "actuador_calefactor_ssr": 24.5,
    "actuador_extractor": 0.0,
    "actuador_bomba_humedad": 0.0,
    "bomba_riego": false,
    "modo_perturbacion": "NORMAL",
    "score_riesgo": 0.22,
    "nivel_riesgo": "BAJO",
    "vpd_kpa": 0.582,
    "punto_rocio": 13.04
  },
  "explicacion": {
    "score_riesgo": 0.22,
    "nivel": "BAJO",
    "recomendacion_accion": "Mantener setpoints estándar (Temp: 18.0°C, Hum: 75%). Monitoreo de rutina.",
    "factores_shap": [
      {
        "variable": "Microclima en Rango Óptimo",
        "impacto": "-0.35",
        "direccion": "PROTECTOR",
        "explicacion": "VPD entre 0.5 y 1.2 kPa; transpiración vegetal equilibrada sin mojado foliar."
      }
    ]
  }
}
```

---

### 2. `POST /api/setpoints/`
- **Uso:** Enviar nuevos setpoints agronómicos desde sliders o formularios.
- **Headers:** `Content-Type: application/json`
- **Cuerpo enviado (JSON):**
```json
{
  "sp_temperatura": 19.0,
  "sp_humedad": 70.0,
  "justificacion": "Ajuste preventivo ante descenso térmico"
}
```
- **Respuesta JSON:**
```json
{
  "status": "success",
  "sp_temperatura": 19.0,
  "sp_humedad": 70.0,
  "publicado_mqtt": true,
  "mensaje": "Setpoints actualizados a 19.0°C y 70.0%"
}
```

---

### 3. `POST /api/pid/`
- **Uso:** Ajustar ganancias del lazo de control.
- **Headers:** `Content-Type: application/json`
- **Cuerpo enviado (JSON):**
```json
{
  "kp": 15.934,
  "ki": 0.1359,
  "kd": 1.571
}
```
- **Respuesta JSON:**
```json
{
  "status": "success",
  "kp": 15.934,
  "ki": 0.1359,
  "kd": 1.571,
  "mensaje": "Ganancias actualizadas: Kp=15.934, Ki=0.1359, Kd=1.571"
}
```

---

### 4. `GET /api/autotune/?metodo=OPTUNA` (o `COHEN_COON` / `IMC`)
- **Uso:** Calcular ganancias óptimas recomendadas por el algoritmo.
- **Respuesta JSON:**
```json
{
  "metodo": "Optuna Bayesiano TPE (Óptimo Seleccionado)",
  "kp": 15.934,
  "ki": 0.1359,
  "kd": 1.571,
  "iae_estimado": 1800.4,
  "sobrepaso_estimado_pct": 1.6,
  "tiempo_asentamiento_s": 346.0,
  "fopdt": {
    "ganancia_K": 0.1639,
    "constante_tau_s": 242.96,
    "retardo_theta_s": 33.33
  }
}
```

---

### 5. `POST /api/modo-gemelo/`
- **Uso:** Cambiar el escenario de estrés climático.
- **Headers:** `Content-Type: application/json`
- **Cuerpo enviado (JSON):**
```json
{
  "modo": "HELADA"
}
```
- **Respuesta JSON:**
```json
{
  "status": "success",
  "modo": "HELADA"
}
```

---

### 6. `POST /api/subir-imagen/`
- **Uso:** Envío de fotografía para inferencia YOLO con o sin SAHI.
- **Formato:** `multipart/form-data`
- **Campos enviados:**
  - `imagen`: Archivo binario (JPG, PNG).
  - `tipo_origen`: `"HOJA_FOLLAJE"` o `"TRAMPA_AMARILLA"`.
  - `usar_sahi`: `"true"` o `"false"`.
- **Respuesta JSON:**
```json
{
  "status": "success",
  "id": 142,
  "clase_detectada": "tizon_tardio",
  "confianza": 0.945,
  "conteo_insectos": 0,
  "severidad_porcentaje": 18.5,
  "tiempo_ms": 78.4,
  "ruta_anotada": "/home/rodrigo/Desktop/IOTtesis/data/raw/uploads/anotada_uuid.jpg",
  "severidad_disponible": true,
  "conteo_disponible": false,
  "tarea_modelo": "segmentacion_o_clasificacion",
  "simulado": false
}
```

---

## 5. Reglas de Estilos y Umbrales Fitosanitarios

Para aplicar estilos condicionales en tus plantillas HTML externas:

1. **Semáforo Fitosanitario (`estado.nivel_riesgo`):**
   - `"BAJO"`: Color verde (`#10B981` / `emerald-500`).
   - `"MEDIO"`: Color amarillo (`#F59E0B` / `amber-500`).
   - `"ALTO"`: Color naranja (`#F97316` / `orange-500`).
   - `"CRÍTICO"`: Color rojo con pulso o parpadeo (`#EF4444` / `rose-500 animate-pulse`).

2. **Déficit de Presión de Vapor (VPD):**
   - Normal / Óptimo: $0.5 \le \text{VPD} \le 1.2\text{ kPa}$.
   - Riesgo de Rocío / Hongo: $\text{VPD} < 0.35\text{ kPa}$.
   - Estrés Hídrico / Plaga: $\text{VPD} > 1.4\text{ kPa}$.

3. **Límites de Seguridad en Setpoints:**
   - Temperatura: Mínimo $8.0^\circ\text{C}$, Máximo $28.0^\circ\text{C}$ (Óptimo papa: $18.0^\circ\text{C}$).
   - Humedad: Mínimo $40\%$, Máximo $95\%$ (Óptimo tuberización: $75\%$).
