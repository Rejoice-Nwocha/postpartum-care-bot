from datetime import date
from sqlalchemy.orm import Session
from app.db import Mother, DeliveryType
from app.safety_scanner import scan_message
from app.whatsapp_client import send_text, send_buttons
from app.content import WELCOME_MESSAGE, WELCOME_BUTTONS
from app.postpartum_brain import answer_postpartum_question, detect_intent
import logging

logger = logging.getLogger(__name__)

MAIN_MENU = (
    "What would you like help with today?\n\n"
    "1. My recovery\n"
    "2. My emotions\n"
    "3. My body\n"
    "4. Breastfeeding\n"
    "5. My baby\n"
    "6. Food & hydration\n"
    "7. Sleep & rest\n"
    "8. Cultural care\n"
    "9. I just want to talk\n\n"
    "You can reply with a number, or simply tell me what's happening."
)

RECOVERY_MENU = (
    "Let's make recovery feel manageable.\n\n"
    "1. Physical recovery\n"
    "2. Food & hydration\n"
    "3. Rest & sleep\n"
    "4. Breastfeeding & breasts\n"
    "5. Emotional wellbeing\n"
    "6. Baby care\n"
    "7. C-section recovery\n"
    "8. Vaginal birth recovery\n"
    "9. Traditional & cultural care\n"
    "0. Back to main menu\n\n"
    "You can also ask me a question in your own words."
)

MENU_COMMANDS = {"menu", "main menu", "home", "start", "0"}
TALK_COMMANDS = {"9", "talk", "i just want to talk", "just want to talk"}


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


def personalize(text: str, first_name: str) -> str:
    name = (first_name or "Mama").strip() or "Mama"
    return text.replace("Mama", name)


def remember_topic(mother: Mother, text: str):
    intent = detect_intent(text)
    if intent:
        mother.current_topic = intent


def postpartum_day(mother: Mother):
    if not mother.delivery_date:
        return None
    return max(0, (date.today() - mother.delivery_date).days)


def menu_reply(mother: Mother, text: str):
    value = text.lower().strip()
    state = mother.pending_prompt or ""

    if value in MENU_COMMANDS:
        mother.pending_prompt = "main_menu"
        return MAIN_MENU

    if value in TALK_COMMANDS:
        mother.pending_prompt = "talking"
        return (
            "I'm here, and you don't need to turn this into a medical question.\n\n"
            "Tell me what's on your mind, exactly as it comes. You can be frustrated, tired, confused, happy, scared or simply unsure.\n\n"
            "I'm listening."
        )

    if state == "main_menu":
        choices = {
            "1": ("recovery_menu", RECOVERY_MENU),
            "2": ("emotions", "Tell me what has been going on emotionally. You don't have to find perfect words."),
            "3": ("body", "Tell me what has changed in your body or what you're noticing."),
            "4": ("breastfeeding", "Tell me what is happening with breastfeeding, latch, milk supply or breast comfort."),
            "5": ("baby", "Tell me what is worrying you about your baby."),
            "6": ("nutrition", "Tell me what you need help with around food, appetite or hydration."),
            "7": ("sleep", "Let's talk about your rest. What's making sleep difficult right now?"),
            "8": ("cultural", "Tell me the cultural or traditional postpartum practice you'd like to understand. I'll help you think about its value and safety."),
            "9": ("talking", "I'm here. Tell me what's on your mind, exactly as it comes."),
        }
        if value in choices:
            new_state, reply = choices[value]
            mother.pending_prompt = new_state
            return reply

    if state == "recovery_menu":
        choices = {
            "0": ("main_menu", MAIN_MENU),
            "1": ("physical_recovery", "Let's talk about your physical recovery. Tell me what you're noticing."),
            "2": ("nutrition", "Tell me what you need help with around food, appetite or hydration."),
            "3": ("sleep", "Tell me about your rest and sleep."),
            "4": ("breastfeeding", "Tell me what is happening with breastfeeding or your breasts."),
            "5": ("emotions", "Tell me how you've been feeling emotionally."),
            "6": ("baby", "Tell me what you'd like help with about your baby."),
            "7": ("csection", "Tell me how your C-section recovery is going."),
            "8": ("perineum", "Tell me how your vaginal-birth recovery is feeling, including any soreness, tear or stitches."),
            "9": ("cultural", "Tell me the cultural or traditional postpartum practice you'd like to understand."),
        }
        if value in choices:
            new_state, reply = choices[value]
            mother.pending_prompt = new_state
            return reply

    return None


async def handle_message(db: Session, wa_id: str, text: str, first_name: str):
    mother = get_or_create_mother(db, wa_id, first_name)
    clean_text = (text or "").strip()
    if not clean_text:
        return

    scan_result = scan_message(clean_text)
    if scan_result.triage_level != 'GREEN':
        mother.triage_level = scan_result.triage_level
        db.commit()
        await send_text(wa_id, personalize(scan_result.response_template, mother.first_name))
        return

    # Natural-language questions always remain available, even inside menus.
    brain_response = answer_postpartum_question(clean_text)
    if brain_response and clean_text.lower() not in MENU_COMMANDS:
        remember_topic(mother, clean_text)
        mother.pending_prompt = mother.pending_prompt if mother.pending_prompt not in {"awaiting_delivery_type", "main_menu"} else None
        reply = personalize(brain_response.text, mother.first_name)
        if brain_response.follow_up:
            reply += "\n\n" + personalize(brain_response.follow_up, mother.first_name)
        db.commit()
        await send_text(wa_id, reply)
        return

    if mother.pending_prompt == 'awaiting_delivery_type':
        choice = clean_text.lower()
        if choice in {'1', 'vaginal', 'vaginal delivery'}:
            mother.delivery_type = DeliveryType.vaginal
            mother.pending_prompt = 'main_menu'
            db.commit()
            await send_text(wa_id, personalize("Thank you, Mama. I've noted that you had a vaginal delivery.\n\n" + MAIN_MENU, mother.first_name))
            return
        if choice in {'2', 'c-section', 'c section', 'csection', 'c-section delivery', 'cesarean', 'caesarean'}:
            mother.delivery_type = DeliveryType.c_section
            mother.pending_prompt = 'main_menu'
            db.commit()
            await send_text(wa_id, personalize("Thank you, Mama. I've noted that you had a C-section.\n\n" + MAIN_MENU, mother.first_name))
            return

        await send_text(wa_id, personalize("I'm here with you, Mama. Reply 1 for Vaginal Delivery or 2 for C-Section, or ask your postpartum question in your own words.", mother.first_name))
        return

    menu = menu_reply(mother, clean_text)
    if menu:
        db.commit()
        await send_text(wa_id, personalize(menu, mother.first_name))
        return

    if not mother.delivery_type or mother.delivery_type == DeliveryType.unknown:
        await send_buttons(wa_id, WELCOME_MESSAGE.format(name=mother.first_name), WELCOME_BUTTONS)
        mother.pending_prompt = 'awaiting_delivery_type'
        db.commit()
        return

    # Continue the last topic naturally when the message is conversational.
    if mother.current_topic:
        prompt = (
            f"I'm listening, {mother.first_name}. We're talking about your {mother.current_topic.replace('_', ' ')}. "
            "Tell me a little more about what you're experiencing, and we'll take it one step at a time."
        )
    else:
        prompt = personalize(
            "I'm listening, Mama. You don't have to find the perfect words. Tell me what is happening in your body, how you are feeling emotionally, or what is worrying you about your baby.",
            mother.first_name,
        )
    db.commit()
    await send_text(wa_id, prompt)
