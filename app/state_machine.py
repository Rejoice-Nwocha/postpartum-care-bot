from sqlalchemy.orm import Session
from app.db import Mother, DeliveryType
from app.safety_scanner import scan_message
from app.whatsapp_client import send_text, send_buttons
from app.content import WELCOME_MESSAGE, WELCOME_BUTTONS
from app.postpartum_brain import answer_postpartum_question
import logging

logger = logging.getLogger(__name__)


def get_or_create_mother(db: Session, wa_id: str, first_name: str = "Mama"):
    mother = db.query(Mother).filter(Mother.wa_id == wa_id).first()
    if not mother:
        mother = Mother(wa_id=wa_id, first_name=first_name)
        db.add(mother)
        db.commit()
        db.refresh(mother)
    elif first_name and mother.first_name == "Mama":
        mother.first_name = first_name
        db.commit()
    return mother


async def handle_message(db: Session, wa_id: str, text: str, first_name: str):
    mother = get_or_create_mother(db, wa_id, first_name)
    clean_text = (text or "").strip()

    if not clean_text:
        return

    # Safety always comes before education or reassurance.
    scan_result = scan_message(clean_text)
    if scan_result.triage_level != 'GREEN':
        mother.triage_level = scan_result.triage_level
        db.commit()
        await send_text(wa_id, scan_result.response_template)
        return

    # Complete the delivery-type prompt, but keep the conversation open if
    # the mother asks a genuine postpartum question instead of choosing 1 or 2.
    if mother.pending_prompt == 'awaiting_delivery_type':
        choice = clean_text.lower()
        if choice in {'1', 'vaginal', 'vaginal delivery'}:
            mother.delivery_type = DeliveryType.vaginal
            mother.pending_prompt = None
            db.commit()
            await send_text(
                wa_id,
                "Thank you, Mama. I've noted that you had a vaginal delivery. "
                "Your recovery is yours, and we can take it one step at a time. "
                "You can now ask me about your body, emotions, breastfeeding, "
                "your baby, sleep, nutrition or recovery."
            )
            return
        elif choice in {'2', 'c-section', 'c section', 'csection', 'c-section delivery', 'cesarean', 'caesarean'}:
            mother.delivery_type = DeliveryType.c_section
            mother.pending_prompt = None
            db.commit()
            await send_text(
                wa_id,
                "Thank you, Mama. I've noted that you had a C-section. "
                "You have been through birth and major surgery, so please be gentle with yourself. "
                "You can now ask me about recovery, emotions, breastfeeding, "
                "your baby, sleep, nutrition or your changing body."
            )
            return

        brain_response = answer_postpartum_question(clean_text)
        if brain_response:
            reply = brain_response.text
            if brain_response.follow_up:
                reply += "\n\n" + brain_response.follow_up
            await send_text(wa_id, reply)
            return

        await send_text(
            wa_id,
            "I'm here with you, Mama. You can reply 1 for Vaginal Delivery or 2 for C-Section, "
            "or simply ask me your postpartum question in your own words."
        )
        return

    # Once onboarded, answer the actual question instead of repeating a generic check-in.
    brain_response = answer_postpartum_question(clean_text)
    if brain_response:
        reply = brain_response.text
        if brain_response.follow_up:
            reply += "\n\n" + brain_response.follow_up
        await send_text(wa_id, reply)
        return

    # First-time fallback: invite onboarding while keeping the conversation open.
    if not mother.delivery_type or mother.delivery_type == DeliveryType.unknown:
        await send_buttons(
            wa_id,
            WELCOME_MESSAGE.format(name=first_name),
            WELCOME_BUTTONS,
        )
        mother.pending_prompt = 'awaiting_delivery_type'
        db.commit()
        return

    await send_text(
        wa_id,
        "I'm listening, Mama. You don't have to find the perfect words. "
        "Tell me what is happening in your body, how you are feeling emotionally, "
        "or what is worrying you about your baby, and we'll take it one step at a time."
    )
