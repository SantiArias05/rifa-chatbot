"""Manejo de base de datos - Soporta PostgreSQL (produccion) y SQLite (desarrollo)."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "rifas.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"

# Determinar tipo de DB
DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_POSTGRES = bool(DATABASE_URL)

# Conexión global
_conn = None


def get_conn():
    """Context manager que abre/cierra la conexión."""
    global _conn
    
    if USE_POSTGRES:
        # Usar PostgreSQL
        import psycopg2
        if _conn is None or _conn.closed:
            _conn = psycopg2.connect(DATABASE_URL)
        return _conn
    else:
        # Usar SQLite
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def get_conn_with_commit():
    """Context manager con commit automático."""
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


@contextmanager
def conn_context():
    """Context manager que maneja commit/rollback."""
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def _convert_params(params, sql):
    """Convierte parámetros para PostgreSQL si es necesario."""
    if USE_POSTGRES:
        # PostgreSQL necesita %s en lugar de ?
        return tuple(params)
    return params


def query(sql: str, params: tuple = ()):
    """Ejecuta SELECT y retorna lista de diccionarios."""
    if USE_POSTGRES:
        # Convertir ? a %s para PostgreSQL
        sql = sql.replace('?', '%s')
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
    else:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def query_one(sql: str, params: tuple = ()):
    """Ejecuta SELECT y retorna un diccionario o None."""
    results = query(sql, params)
    return results[0] if results else None


def execute(sql: str, params: tuple = ()):
    """Ejecuta INSERT/UPDATE/DELETE y retorna el ID."""
    if USE_POSTGRES:
        # Convertir ? a %s para PostgreSQL
        sql = sql.replace('?', '%s')
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                conn.commit()
                # Retornar ID si es INSERT
                if cur.rowcount > 0 and "INSERT" in sql.upper():
                    # PostgreSQL usa RETURNING o lastval()
                    try:
                        cur.execute("SELECT LASTVAL()")
                        return cur.fetchone()[0]
                    except:
                        return cur.rowcount
                return cur.rowcount
    else:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            return cur.lastrowid


def init_db():
    """Crea las tablas si no existen."""
    if USE_POSTGRES:
        # PostgreSQL - crear tablas
        with get_conn() as conn:
            with conn.cursor() as cur:
                # Tabla rifas
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS rifas (
                        id SERIAL PRIMARY KEY,
                        nombre TEXT NOT NULL,
                        descripcion TEXT,
                        precio_boleta REAL NOT NULL,
                        precio_separacion_min REAL,
                        total_boletas INTEGER NOT NULL,
                        fecha_sorteo TEXT,
                        dias_aviso INTEGER DEFAULT 2,
                        estado TEXT DEFAULT 'activa',
                        fecha_inicio TEXT,
                        fecha_fin TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabla clientes
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS clientes (
                        id SERIAL PRIMARY KEY,
                        nombre TEXT NOT NULL,
                        telefono TEXT UNIQUE NOT NULL,
                        email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabla boletas
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS boletas (
                        id SERIAL PRIMARY KEY,
                        rifa_id INTEGER REFERENCES rifas(id),
                        numero TEXT NOT NULL,
                        estado TEXT DEFAULT 'disponible',
                        cliente_id INTEGER REFERENCES clientes(id),
                        comprobante_path TEXT,
                        precio REAL NOT NULL,
                        monto_separacion REAL DEFAULT 0,
                        monto_restante REAL DEFAULT 0,
                        fecha_separacion TIMESTAMP,
                        fecha_expiracion_separacion TIMESTAMP,
                        fecha_reserva TIMESTAMP,
                        fecha_expiracion_reserva TIMESTAMP,
                        fecha_pago TIMESTAMP,
                        notas TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(rifa_id, numero)
                    )
                """)
                
                # Tabla transacciones
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS transacciones (
                        id SERIAL PRIMARY KEY,
                        boleta_id INTEGER REFERENCES boletas(id),
                        rifa_id INTEGER REFERENCES rifas(id),
                        tipo TEXT NOT NULL,
                        detalle TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabla sesiones_cliente
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sesiones_cliente (
                        id SERIAL PRIMARY KEY,
                        telefono TEXT UNIQUE NOT NULL,
                        estado TEXT NOT NULL,
                        contexto TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabla config
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS config (
                        clave TEXT PRIMARY KEY,
                        valor TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabla conversaciones (historial)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversaciones (
                        id SERIAL PRIMARY KEY,
                        telefono TEXT NOT NULL,
                        mensaje TEXT NOT NULL,
                        tipo TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
    else:
        # SQLite - usar schema.sql
        if not SCHEMA_PATH.exists():
            return
        
        with get_conn() as conn:
            with open(SCHEMA_PATH, encoding='utf-8') as f:
                conn.executescript(f.read())


def get_active_rifa():
    """Retorna la rifa activa."""
    rifa = query_one(
        "SELECT * FROM rifas WHERE estado = 'activa' ORDER BY id DESC LIMIT 1"
    )
    if not rifa:
        # Buscar cualquier rifa si no hay activa
        rifa = query_one("SELECT * FROM rifas ORDER BY id DESC LIMIT 1")
    return rifa


def is_admin(telefono: str) -> bool:
    """Determina si el teléfono es admin."""
    from config import Config
    admin_telefonos = os.getenv("ADMIN_TELEFONOS", "").split(",")
    return telefono in admin_telefonos or telefono == os.getenv("ADMIN_TELEFONO", "")


def get_or_create_cliente(telefono: str, nombre: str = None):
    """Obtiene o crea un cliente."""
    cliente = query_one("SELECT * FROM clientes WHERE telefono = ?", (telefono,))
    if cliente:
        if nombre and cliente.get("nombre") != nombre:
            execute("UPDATE clientes SET nombre = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                   (nombre, cliente["id"]))
        return query_one("SELECT * FROM clientes WHERE telefono = ?", (telefono,))
    
    cliente_id = execute(
        "INSERT INTO clientes (nombre, telefono) VALUES (?, ?)",
        (nombre or "Cliente", telefono)
    )
    return query_one("SELECT * FROM clientes WHERE id = ?", (cliente_id,))


def liberar_expiradas():
    """Libera boletas expiradas."""
    count = 0
    # Implementar lógica de expiración
    return count
