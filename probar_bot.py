"""Script para probar el bot directamente."""
import sys
sys.path.insert(0, '.')

from bot import bot

# Simular conversación
telefono = "+573001234567"

print("=== Probando el Bot ===\n")

# 1. Saludo inicial
print("1. Cliente: hola")
respuesta = bot.procesar(telefono, "hola")
print("   Bot:", respuesta.replace("\U0001f44b", "[SALUDO]"), "\n")

# 2. Pide número
print("2. Cliente: quiero el 0042")
respuesta = bot.procesar(telefono, "0042")
print("   Bot:", respuesta.replace("\U0001f44b", "[SALUDO]"), "\n")

# 3. Indica cuánto separar
print("3. Cliente: 5000")
respuesta = bot.procesar(telefono, "5000")
print("   Bot:", respuesta.replace("\U0001f44b", "[SALUDO]"), "\n")

# 4. Pide datos de pago
print("4. Cliente: si, enviamelos")
respuesta = bot.procesar(telefono, "si")
print("   Bot:", respuesta.replace("\U0001f44b", "[SALUDO]"), "\n")

print("=== Fin de prueba ===")
