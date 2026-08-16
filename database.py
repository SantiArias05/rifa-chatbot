"""Manejo de la base de datos SQLite del chatbot de rifas."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "rifas.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


@contextmanager
def get_conn():
    """Context manager que abre/cierra la conexión con FK activadas."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Crea las tablas si no existen."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"No encuentro el schema en {SCHEMA_PATH}")
    with get_conn() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    print(f"[OK] DB inicializada en {DB_PATH}")


def query(sql: str, params: tuple = ()):
    """Ejecuta un SELECT y devuelve lista de dicts."""
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def query_one(sql: str, params: tuple = ()):
    """Ejecuta un SELECT y devuelve un solo dict (o None)."""
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None


def execute(sql: str, params: tuple = ()):
    """Ejecuta INSERT/UPDATE/DELETE y devuelve el lastrowid."""
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid


# ---------- helpers de dominio ----------

def get_or_create_cliente(telefono: str, nombre: str = None) -> int:
    """Devuelve el id del cliente, creándolo si no existe."""
    row = query_one("SELECT id FROM clientes WHERE telefono = ?", (telefono,))
    if row:
        if nombre and nombre != "Sin nombre":
            execute(
                "UPDATE clientes SET nombre = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (nombre, row["id"]),
            )
        return row["id"]
    return execute(
        "INSERT INTO clientes (telefono, nombre) VALUES (?, ?)",
        (telefono, nombre or "Sin nombre"),
    )


def get_active_rifa() -> dict | None:
    """Devuelve la rifa marcada como activa."""
    cfg = query_one("SELECT valor FROM config WHERE clave = 'rifa_activa_id'")
    if cfg and cfg["valor"]:
        rifa = query_one("SELECT * FROM rifas WHERE id = ?", (int(cfg["valor"]),))
        if rifa:
            return rifa
    return query_one(
        "SELECT * FROM rifas WHERE estado = 'activa' ORDER BY id DESC LIMIT 1"
    )


def reservar_boleta(rifa_id: int, numero: str, cliente_id: int, minutos: int = 120) -> bool:
    """Reserva atómica: devuelve True solo si la boleta estaba disponible."""
    with get_conn() as conn:
        cur = conn.execute(
            """UPDATE boletas
                  SET estado = 'reservada',
                      cliente_id = ?,
                      fecha_reserva = CURRENT_TIMESTAMP,
                      fecha_expiracion_reserva = datetime('now', '+' || ? || ' minutes'),
                      updated_at = CURRENT_TIMESTAMP
                WHERE rifa_id = ? AND numero = ? AND estado = 'disponible'""",
            (cliente_id, minutos, rifa_id, numero),
        )
        if cur.rowcount == 0:
            return False
        boleta_id = conn.execute(
            "SELECT id FROM boletas WHERE rifa_id = ? AND numero = ?",
            (rifa_id, numero),
        ).fetchone()[0]
        conn.execute(
            """INSERT INTO transacciones (boleta_id, rifa_id, tipo, detalle, usuario_tel)
                   VALUES (?, ?, 'reserva', 'Reserva creada',
                           (SELECT telefono FROM clientes WHERE id = ?))""",
            (boleta_id, rifa_id, cliente_id),
        )
        return True


def confirmar_pago(boleta_id: int, admin_tel: str) -> bool:
    """Confirma el pago de una boleta reservada."""
    with get_conn() as conn:
        cur = conn.execute(
            """UPDATE boletas
                  SET estado = 'vendida',
                      fecha_pago = CURRENT_TIMESTAMP,
                      updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND estado = 'reservada'""",
            (boleta_id,),
        )
        if cur.rowcount == 0:
            return False
        conn.execute(
            """INSERT INTO transacciones (boleta_id, tipo, detalle, usuario_tel)
                   VALUES (?, 'pago_confirmado', 'Pago confirmado por admin', ?)""",
            (boleta_id, admin_tel),
        )
        return True


def liberar_expiradas() -> int:
    """Job: pone en 'expirada' las reservas vencidas. Devuelve cuántas."""
    with get_conn() as conn:
        cur = conn.execute(
            """UPDATE boletas
                  SET estado = 'expirada', updated_at = CURRENT_TIMESTAMP
                WHERE estado = 'reservada'
                  AND fecha_expiracion_reserva IS NOT NULL
                  AND fecha_expiracion_reserva < CURRENT_TIMESTAMP""",
        )
        return cur.rowcount


def is_admin(telefono: str) -> bool:
    """Chequea si un número está en la whitelist de admins."""
    row = query_one(
        "SELECT id FROM admins WHERE telefono = ? AND activo = 1", (telefono,)
    )
    return row is not None


if __name__ == "__main__":
    init_db()
    print("[OK] Estructura lista.")
