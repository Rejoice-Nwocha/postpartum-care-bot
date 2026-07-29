import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    WHATSAPP_TOKEN: str = os.getenv('WHATSAPP_TOKEN', '')
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
    WHATSAPP_API_VERSION: str = os.getenv('WHATSAPP_API_VERSION', 'v20.0')
    VERIFY_TOKEN: str = os.getenv("VERIFY_TOKEN", "care-sister-secret-2026")

    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///./postpartum.db')
    NURSE_NOTIFY_WEBHOOK_URL: str = os.getenv('NURSE_NOTIFY_WEBHOOK_URL', '')

settings = Settings()
