"""Validaciones comunes."""
import re

TELEFONO_RE = re.compile(r"^\+?[0-9]{7,15}$")
NUMERO_BOLETA_EXACTO = re.compile(r"^[0-9]{4}$")
NUMERO_BOLETA_RE = re.compile(r"\b\d{1,4}\b")


def telefono_valido(telefono: str) -> bool:
    return bool(TELEFONO_RE.match(telefono or ""))


def numero_boleta_valido(numero: str) -> bool:
    return bool(NUMERO_BOLETA_EXACTO.match(numero or ""))


def parsear_boletas(texto: str) -> list[str]:
    """Extrae números de 1-4 dígitos de un texto libre y los normaliza a 4 dígitos.
    Acepta: '0001 y 0002', '0001,0002', '0001 0002', '1, 2'.
    Ignora cualquier número que no sea 1-4 dígitos.
    """
    encontrados = NUMERO_BOLETA_RE.findall(texto or "")
    # dedup preservando orden
    seen = set()
    out = []
    for n in encontrados:
        n4 = n.zfill(4)
        if n4 not in seen:
            seen.add(n4)
            out.append(n4)
    return out


def parsear_cantidad(texto: str) -> int | None:
    """Intenta leer una cantidad del texto. Devuelve int o None."""
    if not texto:
        return None
    # palabras comunes
    palabras = {
        "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
        "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    }
    t = texto.strip().lower()
    if t in palabras:
        return palabras[t]
    m = re.search(r"\d+", t)
    if m:
        n = int(m.group(0))
        return n if 0 < n <= 100 else None
    return None
