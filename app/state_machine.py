from sqlalchemy.orm import Session
from app.db import Mother
from app.safety_scanner import scan_message
from app.whatsapp_client import send_text, send_buttons
from app.content import WELCOME_MESSAGE, WELCOME_BUTTONS, get_cultural_advice
import logging

logger = logging.getLogger(__name__)


def get_or_create_mother(db: Session, wa_id: str, first_name: str = "Mama"):
    mother = db.query(Mother).filter(Mother.wa_id == wa_id).first()
    if not mother:
        mother = Mother(wa_id=wa_id, first_name=first_name)
        db.add(mother)
        db.commit()
        db.refresh(mother)
    return mother


async def handle_message(db: Session, wa_id: str, text: str, first_name: str):
    mother = get_or_create_mother(db, wa_id, first_name)
    
    scan_result = scan_message(text)
    if scan_result.triage_level != 'GREEN':
        await send_text(wa_id, scan_result.response_template)
        return

    # Cultural advice
    cultural = get_cultural_advice(mother.region or 'general')
    
    # Onboarding or default
    if not mother.delivery_type:
        await send_buttons(wa_id, WELCOME_MESSAGE.format(name=first_name), WELCOME_BUTTONS)
        mother.pending_prompt = 'awaiting_delivery_type'
        db.commit()
    else:
        reply = f"Thank you, Mama. {cultural} How are you feeling today?"
        await send_text(wa_id, reply)
