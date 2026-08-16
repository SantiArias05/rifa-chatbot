"""Carga configuración desde .env con defaults sensatos."""
import os
from pathlib import Path
from dotenv import load_dotenv
from database import query_one

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    # WhatsApp
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
    PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")
    WHATSAPP_BUSINESS_ID = os.getenv("WHATSAPP_BUSINESS_ID", "")
    WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "")

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
    TELEGRAM_NOTIF_NO_ENTIENDO = os.getenv("TELEGRAM_NOTIF_NO_ENTIENDO", "true").lower() == "true"
    TELEGRAM_NOTIF_PAGO = os.getenv("TELEGRAM_NOTIF_PAGO", "true").lower() == "true"

    # App
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = BASE_DIR / os.getenv("LOG_FILE", "logs/app.log")

    # Meta API
    META_API_VERSION = "v20.0"
    META_API_BASE = f"https://graph.facebook.com/{META_API_VERSION}"

    @classmethod
    def get_db_config(cls, clave: str, default=None):
        """Obtiene un valor de la tabla config de la DB."""
        try:
            from database import query_one
            row = query_one("SELECT valor FROM config WHERE clave = ?", (clave,))
            return row["valor"] if row else default
        except Exception:
            return default
