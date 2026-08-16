"""Módulo de notificaciones por Telegram."""
import requests
from config import Config


class TelegramNotifier:
    """Envía notificaciones al admin por Telegram."""

    def __init__(self):
        self.enabled = Config.TELEGRAM_ENABLED
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID

    def _send(self, message: str, parse_mode: str = "Markdown", reply_markup: dict = None) -> bool:
        """Envía un mensaje al chat del admin."""
        print(f"[TELEGRAM] Intentando enviar mensaje...")
        print(f"[TELEGRAM] enabled={self.enabled}, bot_token={'OK' if self.bot_token else 'FALTA'}, chat_id={self.chat_id}")
        
        if not self.enabled or not self.bot_token or not self.chat_id:
            print("[TELEGRAM] Faltan configuraciones, no se envía")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode,
        }

        if reply_markup:
            data["reply_markup"] = reply_markup

        try:
            response = requests.post(url, json=data, timeout=10)
            print(f"[TELEGRAM] Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"[TELEGRAM] Error: {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"[TELEGRAM] Exception: {e}")
            return False

    def notificar_no_entiendo(self, telefono: str, mensaje: str) -> bool:
        """Notifica cuando el bot no entiende a un cliente."""
        if not Config.TELEGRAM_NOTIF_NO_ENTIENDO:
            return False

        msg = f"⚠️ *NO ENTIENDO*\n" \
              f"━━━━━━━━━━━━━━━━━━━━\n" \
              f"*De:* {telefono}\n" \
              f"*Mensaje:* {mensaje}\n" \
              f"━━━━━━━━━━━━━━━━━━━━\n" \
              f"Revisa y responde manualmente."

        return self._send(msg)

    def notificar_pago(self, datos: dict) -> bool:
        """Notifica cuando llega un comprobante de pago con botones."""
        if not Config.TELEGRAM_NOTIF_PAGO:
            return False

        boletas = datos.get("boletas", [])
        nombre = datos.get("nombre", "Sin nombre")
        telefono = datos.get("telefono", "")
        monto = datos.get("monto", 0)
        tipo = datos.get("tipo", "completo")

        numero = boletas[0] if boletas else "0000"
        titulo = "💳 RESERVA PENDIENTE" if tipo == "abono" else "💰 PAGO RECIBIDO"

        msg = f"{titulo}\n" \
              f"━━━━━━━━━━━━━━━━━━━━\n" \
              f"*Cliente:* {nombre}\n" \
              f"*Teléfono:* {telefono}\n" \
              f"*Boleta:* {numero}\n" \
              f"*Monto:* ${monto:,.0f}\n" \
              f"━━━━━━━━━━━━━━━━━━━━"

        # Botones inline
        teclado = {
            "inline_keyboard": [
                [
                    {"text": "✅ APROBAR", "callback_data": f"aprobar_{numero}"},
                    {"text": "❌ RECHAZAR", "callback_data": f"rechazar_{numero}"}
                ]
            ]
        }

        return self._send(msg, reply_markup=teclado)

    def notificar_reserva(self, datos: dict) -> bool:
        """Notifica cuando se hace una reserva."""
        boletas = datos.get("boletas", [])
        nombre = datos.get("nombre", "Sin nombre")
        telefono = datos.get("telefono", "")
        monto = datos.get("monto", 0)

        numero = boletas[0] if boletas else "0000"

        msg = f"🎫 *NUEVA RESERVA*\n" \
              f"━━━━━━━━━━━━━━━━━━━━\n" \
              f"*Cliente:* {nombre}\n" \
              f"*Teléfono:* {telefono}\n" \
              f"*Boleta:* {numero}\n" \
              f"*Monto:* ${monto:,.0f}\n" \
              f"━━━━━━━━━━━━━━━━━━━━"

        teclado = {
            "inline_keyboard": [
                [
                    {"text": "✅ APROBAR", "callback_data": f"aprobar_{numero}"},
                    {"text": "❌ RECHAZAR", "callback_data": f"rechazar_{numero}"}
                ]
            ]
        }

        return self._send(msg, reply_markup=teclado)

    def notificar_recordatorio(self, datos: dict) -> bool:
        """Notifica un recordatorio de pago pendiente."""
        nombre = datos.get("nombre", "")
        boletas = datos.get("boletas", [])
        monto = datos.get("monto_restante", 0)
        fecha_sorteo = datos.get("fecha_sorteo", "")

        msg = f"⏰ *RECORDATORIO*\n" \
              f"━━━━━━━━━━━━━━━━━━━━\n" \
              f"*Cliente:* {nombre}\n" \
              f"*Boletas:* {', '.join(boletas)}\n" \
              f"*Monto:* ${monto:,.0f}\n" \
              f"*Sorteo:* {fecha_sorteo}\n" \
              f"━━━━━━━━━━━━━━━━━━━━"

        return self._send(msg)


# Instancia global
telegram = TelegramNotifier()
