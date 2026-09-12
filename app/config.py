import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Settings:
    # Legacy Meta settings - kept for later production integration.
    WHATSAPP_TOKEN: str = os.getenv('WHATSAPP_TOKEN', '')
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
    WHATSAPP_API_VERSION: str = os.getenv('WHATSAPP_API_VERSION', 'v20.0')
    VERIFY_TOKEN: str = os.getenv("VERIFY_TOKEN", "care-sister-secret-2026")

    # Evolution API test settings.
    EVOLUTION_API_URL: str = os.getenv('EVOLUTION_API_URL', '').rstrip('/')
    EVOLUTION_API_KEY: str = os.getenv('EVOLUTION_API_KEY', '')
    EVOLUTION_INSTANCE: str = os.getenv('EVOLUTION_INSTANCE', '')

    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///./postpartum.db')
    NURSE_NOTIFY_WEBHOOK_URL: str = os.getenv('NURSE_NOTIFY_WEBHOOK_URL', '')


settings = Settings()

# Safe diagnostic: report presence only, never log the actual secret/key.
logger.info(
    "Evolution configuration loaded: url=%s api_key=%s instance=%s",
    bool(settings.EVOLUTION_API_URL),
    bool(settings.EVOLUTION_API_KEY),
    bool(settings.EVOLUTION_INSTANCE),
)
