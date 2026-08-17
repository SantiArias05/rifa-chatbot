"""Plantillas de mensajes WhatsApp - Tono amigable y conversacional."""


def bienvenida(nombre_rifa: str = None, precio: int = 0) -> str:
    """Saludo inicial cuando el cliente inicia conversación."""
    nombre = nombre_rifa or "su rifa"
    return (
        f"¡Hola! 👋 Bienvenido a la rifa {nombre}\n\n"
        f"🎟️ El número cuesta ${precio:,}\n\n"
        f"¿Qué número te gustaría reservar?\n"
        f"Escribilo y te lo apartamos 😀"
    )


def oferta_numeros_cercanos(numero: str, cercanos: list[str]) -> str:
    """Cuando el número solicitado ya está ocupado."""
    opts = ", ".join(cercanos[:4])
    return (
        f"Uy, el {numero} ya está reservado 😢\n\n"
        f"Te puedo ofrecer estos otros:\n{opts}\n\n"
        f"¿Cuál te gusta más?"
    )


def numeros_disponibles_aleatorios(numeros: list[str]) -> str:
    """Muestra un random de boletas disponibles."""
    if not numeros:
        return (
            f"¡Qué lástima! 😢 En este momento no hay boletas disponibles.\n\n"
            f"Pero no te preocupes, muy pronto我们会(tendremos) una nueva rifa!\n\n"
            f"¿Te sumo a la lista de espera para avisarte cuando haya nuevas rifas? 😊"
        )

    return (
        f"¡Mira estas que están libres! 🎉\n\n"
        f"{', '.join(numeros)}\n\n"
        f"¿Cuál te llevo reservado?"
    )


def pedir_datos_pago(numero: str, precio: int, datos_pago: dict) -> str:
    """Pide los datos al cliente."""
    banco = datos_pago.get("banco", "Banco")
    cuenta = datos_pago.get("cuenta", "XXXXXX")
    tipo = datos_pago.get("tipo", "ahorros")

    return (
        f"¡El {numero} es tuyo! 🎉\n\n"
        f"Valor: ${precio:,}\n\n"
        f"Datos para pagar:\n"
        f"🏦 Banco: {banco}\n"
        f"💳 Tipo: {tipo}\n"
        f"📱 Número: {cuenta}\n\n"
        f"Cuando pagues, mandame la foto del comprobante 😀"
    )


def comprobante_recibido() -> str:
    """Confirmación cuando el cliente envía el comprobante."""
    return (
        f"¡Perfecto, me llegó! 📸\n\n"
        f"Ya lo estoy revisando 👀\n"
        f"Te aviso en breve cuando esté confirmado ✅\n\n"
        f"¿Tenés alguna otra duda?"
    )


def pago_confirmado(numero: str) -> str:
    """Cuando el pago es confirmado."""
    return (
        f"¡FELICIDADES! 🎊🎊\n\n"
        f"Boleta {numero} confirmada\n"
        f"¡Ya es tuya! 🏆\n\n"
        f"¡Mucha suerte en el sorteo! 🍀🍀"
    )


def pago_rechazado(numero: str, motivo: str = None) -> str:
    """Cuando el pago es rechazado."""
    base = f"El pago de la boleta {numero} no fue aceptado 😟"
    if motivo:
        base += f"\n\nMotivo: {motivo}"
    base += "\n\nContactame para solucionarlo"
    return base


def no_entiendo() -> str:
    """Cuando no entiende el mensaje."""
    return (
        f"No te entendí 😅\n\n"
        f"¿Podés escribir de otra forma?\n"
        f"O si querés, decime qué número te gusta"
    )


def estado_cliente(boletas: list[dict]) -> str:
    """Muestra el estado de las boletas del cliente."""
    if not boletas:
        return "No tenés boletas registradas aún."

    msg = "Tus boletas:\n\n"
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
        f"¡Hola! 👋\n\n"
        f"Gracias por escribirnos.\n\n"
        f"Actualmente no hay rifa activa, pero muy pronto tendremos una nueva! 🎉\n\n"
        f"¿Te sumo a la lista de espera para avisarte apenas tengamos todo listo? 😊"
    )


def ayuda() -> str:
    """Mensaje de ayuda."""
    return (
        f"Comandos disponibles:\n\n"
        f"• disponibles - Ver boletas disponibles\n"
        f"• mis boletas - Ver tus compras\n"
        f"• ayuda - Mostrar este mensaje\n\n"
        f"¿En qué te puedo ayudar?"
    )
