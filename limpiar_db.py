"""Limpiar base de datos."""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "data" / "rifas.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Limpiar todas las boletas
cur.execute('UPDATE boletas SET estado = "disponible", cliente_id = NULL, monto_separacion = 0, monto_restante = 0, fecha_separacion = NULL')

# Eliminar clientes de prueba
cur.execute('DELETE FROM clientes')

# Eliminar transacciones
cur.execute('DELETE FROM transacciones')

conn.commit()
print('Base de datos limpiada - todas las boletas disponibles')
conn.close()
