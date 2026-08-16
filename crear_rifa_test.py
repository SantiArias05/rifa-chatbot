"""Script para crear rifa de prueba."""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "data" / "rifas.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Crear rifa de prueba
cur.execute('''
    INSERT INTO rifas (nombre, descripcion, precio_boleta, precio_separacion_min, total_boletas, fecha_sorteo, dias_aviso)
    VALUES (?, ?, ?, ?, ?, ?, ?)
''', ('Rifa Sorteo 2024', 'Rifa mensual', 20000, 5000, 100, '2024-12-31', 2))

rifa_id = cur.lastrowid

# Crear 100 boletas (0000-0099)
for i in range(100):
    num = str(i).zfill(4)
    cur.execute('INSERT INTO boletas (rifa_id, numero, precio, estado) VALUES (?, ?, ?, ?)',
                (rifa_id, num, 20000, 'disponible'))

conn.commit()
print(f'Rifa creada con ID: {rifa_id}')
print(f'Boletas creadas: {cur.execute("SELECT COUNT(*) FROM boletas").fetchone()[0]}')

# Configurar como rifa activa
cur.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('rifa_activa_id', ?)", (str(rifa_id),))
conn.commit()
print('Rifa configurada como activa')

# Agregar admin de prueba
cur.execute("INSERT OR IGNORE INTO admins (nombre, telefono, rol) VALUES (?, ?, ?)", ('Admin', '+573001234567', 'admin'))
conn.commit()
print('Admin agregado')

conn.close()
print('\n✅ Listo para probar!')
