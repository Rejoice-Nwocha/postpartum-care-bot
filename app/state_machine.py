from sqlalchemy.orm import Session
from app.db import Mother, DeliveryType
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
    clean_text = (text or "").strip()

    scan_result = scan_message(clean_text)
    if scan_result.triage_level != 'GREEN':
        await send_text(wa_id, scan_result.response_template)
        return

    # Complete the initial delivery-type prompt before normal conversation.
    if mother.pending_prompt == 'awaiting_delivery_type':
        choice = clean_text.lower()
        if choice in {'1', 'vaginal', 'vaginal delivery'}:
            mother.delivery_type = DeliveryType.vaginal
        elif choice in {'2', 'c-section', 'c section', 'csection', 'c-section delivery'}:
            mother.delivery_type = DeliveryType.c_section
        else:
            await send_text(
                wa_id,
                "Please reply with 1 for Vaginal Delivery or 2 for C-Section Delivery."
            )
            return

        mother.pending_prompt = None
        db.commit()
        await send_text(
            wa_id,
            "Thank you, Mama. I've noted your delivery type. How are you feeling today?"
        )
        return

    # Region is not stored on the current Mother model, so use the general
    # cultural guidance until a region field is added to the data model.
    cultural = get_cultural_advice('general')

    # Onboarding or default
    if not mother.delivery_type or mother.delivery_type == DeliveryType.unknown:
        await send_buttons(wa_id, WELCOME_MESSAGE.format(name=first_name), WELCOME_BUTTONS)
        mother.pending_prompt = 'awaiting_delivery_type'
        db.commit()
    else:
        reply = f"Thank you, Mama. {cultural} How are you feeling today?"
        await send_text(wa_id, reply)
