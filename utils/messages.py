"""Plantillas de mensajes WhatsApp - Tono formal colombiano."""


def bienvenida(nombre_rifa: str = None, precio: int = 0) -> str:
    """Saludo inicial cuando el cliente inicia conversación."""
    nombre = nombre_rifa or "su rifa"
    return (
        f"¡Buenas! Le atiende.\n\n"
        f"Tenemos disponible en {nombre}.\n"
        f"Valor de la boleta: ${precio:,}.\n\n"
        f"¿Qué número le interesa?"
    )


def oferta_numeros_cercanos(numero: str, cercanos: list[str]) -> str:
    """Cuando el número solicitado ya está ocupado."""
    opts = ", ".join(cercanos[:4])
    return (
        f"El número {numero} ya está ocupado.\n\n"
        f"Le puedo ofrecer: {opts}\n"
        f"¿Cuál prefiere?"
    )


def numeros_disponibles_aleatorios(numeros: list[str]) -> str:
    """Muestra un random de boletas disponibles."""
    if not numeros:
        return "En este momento no hay boletas disponibles."

    return (
        f"Estas son algunas disponibles:\n\n"
        f"{', '.join(numeros)}\n\n"
        f"¿Cuál le interesa?"
    )


def pedir_datos_pago(numero: str, precio: int, datos_pago: dict) -> str:
    """Pide los datos al cliente."""
    banco = datos_pago.get("banco", "Banco")
    cuenta = datos_pago.get("cuenta", "XXXXXX")
    tipo = datos_pago.get("tipo", "ahorros")

    return (
        f"La boleta {numero} está disponible.\n"
        f"Valor: ${precio:,}\n\n"
        f"Datos para el pago:\n"
        f"- Banco: {banco}\n"
        f"- Cuenta: {tipo}\n"
        f"- Número: {cuenta}\n\n"
        f"Envíe el comprobante (foto) cuando realice el pago."
    )


def comprobante_recibido() -> str:
    """Confirmación cuando el cliente envía el comprobante."""
    return (
        f"Gracias, he recibido su comprobante. 📸\n\n"
        f"En breve le confirmamos el pago.\n"
        f"¿Necesita algo más?"
    )


def pago_confirmado(numero: str) -> str:
    """Cuando el pago es confirmado."""
    return (
        f"¡Pago confirmado!\n\n"
        f"Boleta: {numero}\n"
        f"Ya está a su nombre.\n\n"
        f"¡Mucha suerte! 🍀"
    )


def pago_rechazado(numero: str, motivo: str = None) -> str:
    """Cuando el pago es rechazado."""
    base = f"Lamentablemente, el pago para la boleta {numero} fue rechazado."
    if motivo:
        base += f"\n\nMotivo: {motivo}"
    base += "\n\nComuníquese con nosotros para resolver."
    return base


def no_entiendo() -> str:
    """Cuando no entiende el mensaje."""
    return (
        f"Disculpe, no entendí su mensaje.\n\n"
        f"¿Podría escribir de otra forma?\n"
        f"Si lo prefiere, puede llamar directamente."
    )


def estado_cliente(boletas: list[dict]) -> str:
    """Muestra el estado de las boletas del cliente."""
    if not boletas:
        return "No tiene boletas registradas."

    msg = "Sus boletas:\n\n"
    for b in boletas:
        estado = b.get("estado", "")
        numero = b.get("numero", "")
        if estado == "reservada":
            msg += f"• {numero} - Reservada\n"
        elif estado == "vendida":
            msg += f"• {numero} - Confirmada ✓\n"

    return msg


def rifa_no_activa() -> str:
    """Cuando no hay rifa activa."""
    return (
        f"En este momento no hay rifa activa.\n\n"
        f"Próximamente tendremos nuevas rifas."
    )


def ayuda() -> str:
    """Mensaje de ayuda."""
    return (
        f"Comandos disponibles:\n\n"
        f"• disponibles - Ver boletas\n"
        f"• mis boletas - Ver sus compras\n"
        f"• ayuda - Mostrar este mensaje\n\n"
        f"¿En qué le puedo ayudar?"
    )
