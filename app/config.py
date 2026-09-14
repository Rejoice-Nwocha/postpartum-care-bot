import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Settings:
    # Evolution API / Baileys is the active WhatsApp transport for testing.
    EVOLUTION_API_URL: str = os.getenv("EVOLUTION_API_URL", "").rstrip("/")
    EVOLUTION_API_KEY: str = os.getenv("EVOLUTION_API_KEY", "")
    EVOLUTION_INSTANCE: str = os.getenv("EVOLUTION_INSTANCE", "")

    # Database and future human-support integration.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./postpartum.db")
    NURSE_NOTIFY_WEBHOOK_URL: str = os.getenv("NURSE_NOTIFY_WEBHOOK_URL", "")

    # Kept for a future Meta integration; not used by the Evolution transport.
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_API_VERSION: str = os.getenv("WHATSAPP_API_VERSION", "v20.0")
    VERIFY_TOKEN: str = os.getenv("VERIFY_TOKEN", "")


settings = Settings()

logger.info(
    "Evolution configuration loaded: url=%s api_key=%s instance=%s",
    bool(settings.EVOLUTION_API_URL),
    bool(settings.EVOLUTION_API_KEY),
    bool(settings.EVOLUTION_INSTANCE),
)
