"""Cliente para comunicarse con la API de WhatsApp Business."""
import requests
import logging
from config import Config

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """Cliente para enviar mensajes por WhatsApp Business API."""

    def __init__(self):
        self.token = Config.WHATSAPP_TOKEN
        self.phone_id = Config.PHONE_NUMBER_ID
        self.business_id = Config.WHATSAPP_BUSINESS_ID
        self.api_version = Config.META_API_VERSION
        self.base_url = Config.META_API_BASE

    def _headers(self) -> dict:
        """Headers para las requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def enviar_mensaje(self, telefono: str, texto: str) -> bool:
        """Envía un mensaje de texto."""
        url = f"{self.base_url}/{self.phone_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "to": telefono,
            "type": "text",
            "text": {"body": texto}
        }

        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=30)
            if response.status_code in [200, 201]:
                logger.info(f"Mensaje enviado a {telefono}")
                return True
            else:
                logger.error(f"Error enviando mensaje: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Excepción enviando mensaje: {e}")
            return False

    def enviar_imagen(self, telefono: str, url_imagen: str, caption: str = None) -> bool:
        """Envía una imagen."""
        url = f"{self.base_url}/{self.phone_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "to": telefono,
            "type": "image",
            "image": {
                "link": url_imagen,
                "caption": caption or ""
            }
        }

        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=30)
            if response.status_code in [200, 201]:
                logger.info(f"Imagen enviada a {telefono}")
                return True
            else:
                logger.error(f"Error enviando imagen: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Excepción enviando imagen: {e}")
            return False

    def obtener_media_url(self, media_id: str) -> str:
        """Obtiene la URL de descarga de un media."""
        url = f"{self.base_url}/{media_id}"

        try:
            response = requests.get(url, headers=self._headers(), timeout=30)
            if response.status_code == 200:
                data = response.json()
                return data.get("url", "")
            else:
                logger.error(f"Error obteniendo media: {response.status_code}")
                return ""
        except Exception as e:
            logger.error(f"Excepción obteniendo media: {e}")
            return ""

    def descargar_media(self, media_url: str) -> bytes:
        """Descarga el contenido de un media."""
        try:
            response = requests.get(media_url, headers=self._headers(), timeout=60)
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Error descargando media: {response.status_code}")
                return b""
        except Exception as e:
            logger.error(f"Excepción descargando media: {e}")
            return b""

    def marcar_leido(self, message_id: str) -> bool:
        """Marca un mensaje como leído."""
        url = f"{self.base_url}/{self.phone_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        try:
            response = requests.post(url, json=payload, headers=self._headers(), timeout=30)
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Excepción marcando como leído: {e}")
            return False
