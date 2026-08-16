"""Ver contenido de la base de datos."""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "data" / "rifas.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Ver tablas
print('=== TABLAS ===')
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
for t in cur.fetchall():
    print(f'  - {t[0]}')

print()

# Ver rifas
print('=== RIFAS ===')
cur.execute('SELECT * FROM rifas')
for r in cur.fetchall():
    print(r)

print()

# Ver clientes
print('=== CLIENTES ===')
cur.execute('SELECT * FROM clientes')
for c in cur.fetchall():
    print(c)

print()

# Ver boletas (resumen)
print('=== BOLETAS (resumen) ===')
cur.execute('''
    SELECT estado, COUNT(*) as total 
    FROM boletas 
    GROUP BY estado
''')
for e in cur.fetchall():
    print(f'  {e[0]}: {e[1]}')

print()

# Ver admins
print('=== ADMINES ===')
cur.execute('SELECT * FROM admins')
for a in cur.fetchall():
    print(a)

print()

# Ver config
print('=== CONFIG ===')
cur.execute('SELECT * FROM config')
for c in cur.fetchall():
    print(f'  {c[0]}: {c[1]}')

conn.close()
