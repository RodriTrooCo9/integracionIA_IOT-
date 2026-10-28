-- =============================================================================
-- Esquema Relacional SQLite: Eventos, Detección de Visión y Experimentos E1-E8
-- Proyecto: Tesis IoT-PID-IA Papa bajo Invernadero (La Paz)
-- =============================================================================

PRAGMA foreign_keys = ON;

-- 1. Tabla de Dispositivos / Nodos
CREATE TABLE IF NOT EXISTS nodos_sensores (
    nodo_id VARCHAR(32) PRIMARY KEY,
    nombre VARCHAR(64) NOT NULL,
    descripcion TEXT,
    ip_asignada VARCHAR(45),
    mac_address VARCHAR(17),
    firmware_version VARCHAR(16),
    estado VARCHAR(16) DEFAULT 'ACTIVO', -- ACTIVO, INACTIVO, MANTENIMIENTO
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Detecciones de Visión Artificial (YOLO + SAHI)
CREATE TABLE IF NOT EXISTS detecciones_vision (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    nodo_camara VARCHAR(32) NOT NULL,
    tipo_origen VARCHAR(16) NOT NULL, -- 'TRAMPA_AMARILLA', 'HOJA_FOLLAJE'
    ruta_imagen_original TEXT NOT NULL,
    ruta_imagen_anotada TEXT,
    clase_detectada VARCHAR(64) NOT NULL, -- 'polilla_guatemalteca', 'mosca_minadora', 'pulgones', 'tizon_tardio', etc.
    confianza REAL NOT NULL,
    bbox_json TEXT NOT NULL, -- '[{"x1": 12, "y1": 34, "x2": 56, "y2": 78, "clase": "pulgon"}]'
    conteo_insectos INTEGER DEFAULT 1,
    severidad_porcentaje REAL DEFAULT 0.0, -- Para lesiones foliares (0.0 a 100.0)
    tiempo_inferencia_ms REAL,
    procesado_con_sahi BOOLEAN DEFAULT 0,
    simulado BOOLEAN NOT NULL DEFAULT 1,
    motor TEXT NOT NULL DEFAULT 'desconocido',
    FOREIGN KEY (nodo_camara) REFERENCES nodos_sensores(nodo_id)
);

-- 3. Tabla de Registro de Eventos y Alarmas del Sistema
CREATE TABLE IF NOT EXISTS eventos_alarmas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_evento VARCHAR(32) NOT NULL, -- 'TEMP_CRITICA_ALTA', 'TEMP_CRITICA_BAJA', 'DESCONEXION_WIFI', 'FALLA_SENSOR', 'RIESGO_TIZON_ALTO'
    nivel_severidad VARCHAR(16) NOT NULL, -- 'INFO', 'WARNING', 'CRITICAL'
    mensaje TEXT NOT NULL,
    valor_disparador REAL,
    accion_ejecutada TEXT, -- 'NOTIFICACION_TELEGRAM', 'ACTIVACION_FORZADA_CALEFACTOR', etc.
    notificado_telegram BOOLEAN DEFAULT 0
);

-- 4. Tabla de Auditoría de Cambios de Setpoints y Parámetros PID
CREATE TABLE IF NOT EXISTS auditoria_control_pid (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_origen VARCHAR(32) DEFAULT 'SISTEMA_IA', -- 'SISTEMA_IA', 'OPERADOR_WEB', 'VALOR_DEFECTO'
    variable_control VARCHAR(32) NOT NULL, -- 'TEMPERATURA', 'HUMEDAD'
    sp_anterior REAL,
    sp_nuevo REAL NOT NULL,
    kp REAL,
    ki REAL,
    kd REAL,
    justificacion TEXT
);

-- 5. Tabla de Registro de Ensayos Experimentales (E1 a E8)
CREATE TABLE IF NOT EXISTS experimentos_ensayos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_experimento VARCHAR(8) NOT NULL, -- 'E1', 'E2', ..., 'E8'
    nombre_ensayo VARCHAR(128) NOT NULL,
    tratamiento VARCHAR(32) NOT NULL, -- 'CON_SISTEMA_PID_IA', 'SIN_SISTEMA_TESTIGO'
    fecha_inicio TIMESTAMP NOT NULL,
    fecha_fin TIMESTAMP,
    duracion_horas REAL,
    metricas_resumen_json TEXT, -- '{"iae": 14.2, "sobrepaso_max": 8.5, "tiempo_riesgo_h": 1.2}'
    observaciones TEXT
);

-- Índices para optimizar consultas en FastAPI y análisis estadístico
CREATE INDEX IF NOT EXISTS idx_detecciones_fecha ON detecciones_vision(timestamp);
CREATE INDEX IF NOT EXISTS idx_detecciones_clase ON detecciones_vision(clase_detectada);
CREATE INDEX IF NOT EXISTS idx_eventos_nivel ON eventos_alarmas(nivel_severidad, timestamp);
CREATE INDEX IF NOT EXISTS idx_experimentos_codigo ON experimentos_ensayos(codigo_experimento);

-- One record per logical demonstration fixture. Existing real trials are untouched.
CREATE TABLE IF NOT EXISTS seed_fixtures (
    fixture_key TEXT PRIMARY KEY,
    experimento_id INTEGER NOT NULL REFERENCES experimentos_ensayos(id)
);
CREATE TABLE IF NOT EXISTS control_publicado (
    variable TEXT PRIMARY KEY,
    valor REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
