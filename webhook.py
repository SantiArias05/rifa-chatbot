"""Webhook para recibir mensajes de WhatsApp Business."""
import logging
from flask import Blueprint, request, jsonify
from config import Config
from database import is_admin
from bot import bot
from whatsapp import WhatsAppClient

webhook_bp = Blueprint("webhook", __name__)
logger = logging.getLogger(__name__)
wa_client = WhatsAppClient()


@webhook_bp.route("/webhook", methods=["GET"])
def verify_webhook():
    """Verificación del webhook cuando se registra en Meta."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == Config.WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verificado correctamente")
        return challenge, 200
    else:
        logger.warning(f"Verificación fallida: mode={mode}, token={token}")
        return "Verificación fallida", 403


@webhook_bp.route("/webhook", methods=["POST"])
def receive_webhook():
    """Recibe mensajes entrantes de WhatsApp."""
    try:
        data = request.json
        logger.info(f"Webhook recibido: {data}")

        # Verificar que es un mensaje
        if "entry" not in data:
            return jsonify({"status": "ok"})

        # Procesar cada mensaje
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                messages = change.get("value", {}).get("messages", [])
                for msg in messages:
                    _procesar_mensaje(msg)

        return jsonify({"status": "ok"})

    except Exception as e:
        logger.error(f"Error procesando webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


def _procesar_mensaje(msg: dict):
    """Procesa un mensaje individual de WhatsApp."""
    try:
        # Extraer datos
        telefono = msg.get("from", "")
        msg_id = msg.get("id", "")
        timestamp = msg.get("timestamp", "")

        # Determinar tipo de mensaje
        tipo = msg.get("type", "text")

        if tipo == "text":
            texto = msg.get("text", {}).get("body", "")
            _responder(telefono, texto, msg_id)

        elif tipo == "image":
            # Guardar imagen
            media_id = msg.get("image", {}).get("id", "")
            _procesar_imagen(telefono, media_id, msg_id)

        elif tipo == "document":
            # Documento recibido
            logger.info(f"Documento recibido de {telefono}: {msg.get('document', {})}")

        else:
            logger.info(f"Tipo de mensaje no manejado: {tipo}")

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")


def _responder(telefono: str, texto: str, msg_id: str = None):
    """Genera y envía la respuesta al cliente."""
    # Verificar si es admin
    es_admin = is_admin(telefono)

    # Procesar con el bot
    respuesta = bot.procesar(telefono, texto, es_admin)

    # Enviar respuesta por WhatsApp
    wa_client.enviar_mensaje(telefono, respuesta)

    logger.info(f"Respondido a {telefono}: {respuesta[:50]}...")


def _procesar_imagen(telefono: str, media_id: str, msg_id: str):
    """Procesa una imagen recibida (comprobante de pago)."""
    try:
        # Descargar imagen
        media_url = wa_client.obtener_media_url(media_id)

        if media_url:
            # Guardar en disco
            from pathlib import Path
            import requests

            comprobantes_dir = Path(__file__).parent / "data" / "comprobantes"
            comprobantes_dir.mkdir(parents=True, exist_ok=True)

            # Descargar
            img_data = requests.get(media_url).content
            filename = f"{telefono}_{msg_id}.jpg"
            filepath = comprobantes_dir / filename
            filepath.write_bytes(img_data)

            logger.info(f"Comprobante guardado: {filepath}")

            # Notificar al admin por Telegram
            from telegram import telegram
            telegram.notificar_pago({
                "boletas": ["pendiente"],
                "nombre": "Cliente",
                "telefono": telefono,
                "monto": 0,
                "tipo": "comprobante"
            })

    except Exception as e:
        logger.error(f"Error procesando imagen: {e}")
