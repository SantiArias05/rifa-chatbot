-- ============================================================
-- CHATBOT DE RIFAS - ESQUEMA DE BASE DE DATOS (v2 corregido)
-- ============================================================
-- Para inicializar: python database.py
-- ============================================================

-- Tabla: rifas (la rifa en sí, antes era el nombre equivocado de "boletas")
CREATE TABLE IF NOT EXISTS rifas (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre               TEXT    NOT NULL,
    descripcion          TEXT,
    precio_boleta        REAL    NOT NULL CHECK (precio_boleta > 0),
    precio_separacion_min REAL   NOT NULL DEFAULT 5000 CHECK (precio_separacion_min > 0),
    total_boletas        INTEGER NOT NULL DEFAULT 10000 CHECK (total_boletas > 0 AND total_boletas <= 10000),
    fecha_sorteo         DATETIME,
    dias_aviso           INTEGER NOT NULL DEFAULT 2 CHECK (dias_aviso > 0),
    estado               TEXT    NOT NULL DEFAULT 'activa'
                        CHECK (estado IN ('activa','pausada','finalizada','cancelada')),
    fecha_inicio         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin            DATETIME,
    created_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: clientes (separada para no repetir datos en cada boleta)
CREATE TABLE IF NOT EXISTS clientes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT    NOT NULL,
    telefono    TEXT    NOT NULL UNIQUE,
    email       TEXT,
    notas       TEXT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: boletas (los tickets 0000-9999 de cada rifa)
CREATE TABLE IF NOT EXISTS boletas (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    rifa_id                  INTEGER NOT NULL,
    numero                   TEXT    NOT NULL
                             CHECK (length(numero) = 4 AND numero GLOB '[0-9][0-9][0-9][0-9]'),
    estado                   TEXT    NOT NULL DEFAULT 'disponible'
                             CHECK (estado IN ('disponible','separada','reservada','vendida','cancelada','expirada')),
    cliente_id               INTEGER,
    comprobante_path         TEXT,
    precio                   REAL    NOT NULL CHECK (precio > 0),
    monto_separacion         REAL    DEFAULT 0,
    monto_restante           REAL    DEFAULT 0,
    fecha_separacion         DATETIME,
    fecha_expiracion_separacion DATETIME,
    fecha_reserva            DATETIME,
    fecha_expiracion_reserva DATETIME,
    fecha_pago               DATETIME,
    notas                    TEXT,
    created_at               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (rifa_id, numero),
    FOREIGN KEY (rifa_id)    REFERENCES rifas(id)    ON DELETE CASCADE,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL
);

-- Tabla: transacciones (log de eventos, append-only)
CREATE TABLE IF NOT EXISTS transacciones (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    boleta_id     INTEGER,
    rifa_id       INTEGER,
    tipo          TEXT    NOT NULL
                  CHECK (tipo IN ('separacion','reserva','pago_parcial','pago_completo','pago_confirmado','cancelacion','expiracion','devolucion','creacion_boleta')),
    detalle       TEXT,
    monto         REAL,
    usuario_tel   TEXT,
    metadata_json TEXT,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (boleta_id) REFERENCES boletas(id) ON DELETE SET NULL,
    FOREIGN KEY (rifa_id)   REFERENCES rifas(id)   ON DELETE SET NULL
);

-- Tabla: admins (whitelist de números autorizados)
CREATE TABLE IF NOT EXISTS admins (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT    NOT NULL,
    telefono    TEXT    NOT NULL UNIQUE,
    rol         TEXT    NOT NULL DEFAULT 'admin'
                CHECK (rol IN ('admin','superadmin')),
    activo      INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0,1)),
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: sesiones_cliente (manejo de flujo conversacional paso a paso)
CREATE TABLE IF NOT EXISTS sesiones_cliente (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    telefono       TEXT    NOT NULL UNIQUE,
    estado         TEXT    NOT NULL DEFAULT 'inicio'
                   CHECK (estado IN ('inicio','pidiendo_numero','pidiendo_separacion',
                                     'pidiendo_datos','pidiendo_comprobante','separacion_pendiente',
                                     'procesando','completado','timeout')),
    rifa_id        INTEGER,
    contexto_json  TEXT,
    last_activity  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rifa_id) REFERENCES rifas(id) ON DELETE SET NULL
);

-- Tabla: conversaciones (historial de mensajes para memoria)
CREATE TABLE IF NOT EXISTS conversaciones (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    telefono      TEXT    NOT NULL,
    mensaje       TEXT    NOT NULL,
    tipo          TEXT    NOT NULL DEFAULT 'entrada'
                    CHECK (tipo IN ('entrada','salida','sistema')),
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: historial_cliente (memoria persistente del cliente)
CREATE TABLE IF NOT EXISTS historial_cliente (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    telefono         TEXT    NOT NULL UNIQUE,
    nombre           TEXT,
    rifas_compradas  TEXT,
    boletas_compradas TEXT,
    deuda_pendiente  REAL    DEFAULT 0,
    ultimo_mensaje   DATETIME,
    notas            TEXT,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: config (settings que se cambian sin redeploy)
CREATE TABLE IF NOT EXISTS config (
    clave       TEXT PRIMARY KEY,
    valor       TEXT NOT NULL,
    descripcion TEXT,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- ÍNDICES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_boletas_numero       ON boletas(numero);
CREATE INDEX IF NOT EXISTS idx_boletas_estado       ON boletas(estado);
CREATE INDEX IF NOT EXISTS idx_boletas_rifa_id      ON boletas(rifa_id);
CREATE INDEX IF NOT EXISTS idx_boletas_cliente_id   ON boletas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_boletas_expiracion   ON boletas(fecha_expiracion_reserva)
    WHERE estado = 'reservada';
CREATE INDEX IF NOT EXISTS idx_boletas_exp_sep     ON boletas(fecha_expiracion_separacion)
    WHERE estado = 'separada';
CREATE INDEX IF NOT EXISTS idx_clientes_telefono    ON clientes(telefono);
CREATE INDEX IF NOT EXISTS idx_transacciones_boleta ON transacciones(boleta_id);
CREATE INDEX IF NOT EXISTS idx_transacciones_fecha  ON transacciones(created_at);
CREATE INDEX IF NOT EXISTS idx_sesiones_telefono    ON sesiones_cliente(telefono);
CREATE INDEX IF NOT EXISTS idx_conversaciones_telefono ON conversaciones(telefono, created_at);
CREATE INDEX IF NOT EXISTS idx_historial_telefono    ON historial_cliente(telefono);

-- ============================================================
-- DATOS INICIALES
-- ============================================================
INSERT OR IGNORE INTO config (clave, valor, descripcion) VALUES
    ('reserva_minutos',    '120',     'Minutos que dura una reserva antes de expirar'),
    ('precio_default',     '1000',    'Precio por defecto si no se crea la rifa'),
    ('admin_notif_enabled','1',       'Activar notificaciones a admins'),
    ('rifa_activa_id',     '',        'ID de la rifa actualmente activa'),
    ('telegram_enabled',    '0',       'Activar notificaciones por Telegram'),
    ('telegram_chat_id',    '',        'Chat ID del admin para notificaciones'),
    ('telegram_notif_no_entiendo', '1', 'Notificar cuando no entienda'),
    ('telegram_notif_pago', '1',      'Notificar cuando llegue comprobante');
