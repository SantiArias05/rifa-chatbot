"""Smoke test rápido de los utils."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils.validators import (
    parsear_boletas, parsear_cantidad, numero_boleta_valido, telefono_valido
)

casos = [
    ("parsear_boletas", lambda: parsear_boletas("0001, 0002, 5")),
    ("parsear_boletas (texto libre)", lambda: parsear_boletas("quiero la 1234 y la 5678")),
    ("parsear_boletas (repetidos)", lambda: parsear_boletas("0001 0001 0002")),
    ("parsear_cantidad (texto)", lambda: parsear_cantidad("tres")),
    ("parsear_cantidad (numero)", lambda: parsear_cantidad("2 boletas")),
    ("parsear_cantidad (invalid)", lambda: parsear_cantidad("muchas")),
    ("numero_boleta_valido 0001", lambda: numero_boleta_valido("0001")),
    ("numero_boleta_valido abc", lambda: numero_boleta_valido("abc")),
    ("numero_boleta_valido 12", lambda: numero_boleta_valido("12")),
    ("telefono_valido +57...", lambda: telefono_valido("+573001234567")),
    ("telefono_valido vacio", lambda: telefono_valido("")),
]

for nombre, fn in casos:
    try:
        print(f"  {nombre:35s} -> {fn()}")
    except Exception as e:
        print(f"  {nombre:35s} -> ERROR: {e}")
