from datetime import date, datetime
import re
from sqlalchemy.orm import Session
from app.db import Mother, DeliveryType
from app.safety_scanner import scan_message, TriageLevel
from app.whatsapp_client import send_text, send_buttons
from app.content import WELCOME_MESSAGE, WELCOME_BUTTONS
from app.postpartum_brain import answer_postpartum_question, contextual_response, detect_intent
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
AFFIRMATIVE = {"yes", "yeah", "yep", "i am", "i do", "safe", "i feel safe", "1"}
NEGATIVE = {"no", "nope", "not really", "unsafe", "i don't", "i am not", "2"}


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
    if intent and intent != "greeting":
        mother.current_topic = intent


def postpartum_day(mother: Mother):
    if not mother.delivery_date:
        return None
    return max(0, (date.today() - mother.delivery_date).days)


def recovery_stage(mother: Mother) -> str:
    day = postpartum_day(mother)
    if day is None:
        return "unknown"
    if day <= 14:
        return "early_recovery"
    if day <= 42:
        return "healing_recovery"
    return "ongoing_recovery"


def parse_delivery_date(text: str):
    value = (text or "").strip()
    formats = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y")
    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt).date()
            if parsed <= date.today():
                return parsed
        except ValueError:
            pass

    for fmt in ("%d %B %Y", "%d %b %Y"):
        try:
            parsed = datetime.strptime(value, fmt).date()
            if parsed <= date.today():
                return parsed
        except ValueError:
            pass
    return None


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
    if scan_result.triage_level != TriageLevel.GREEN:
        mother.triage_level = scan_result.triage_level
        db.commit()
        await send_text(wa_id, personalize(scan_result.response_template, mother.first_name))
        return

    value = clean_text.lower().strip()

    # First-time users are guided through the minimum recovery profile before
    # generic conversation begins. Emergency/safety messages have already been
    # handled above, so a genuine urgent concern is never blocked by onboarding.
    if (
        not mother.delivery_type
        or mother.delivery_type == DeliveryType.unknown
    ) and mother.pending_prompt is None:
        mother.pending_prompt = "awaiting_delivery_type"
        db.commit()
        await send_buttons(
            wa_id,
            WELCOME_MESSAGE.format(name=mother.first_name),
            WELCOME_BUTTONS,
        )
        return

    # Onboarding takes priority over generic brain intents.
    if mother.pending_prompt == "awaiting_delivery_type":
        if value in {"1", "vaginal", "vaginal delivery", "normal delivery"}:
            mother.delivery_type = DeliveryType.vaginal
            mother.pending_prompt = "awaiting_delivery_date"
            db.commit()
            await send_text(
                wa_id,
                personalize(
                    "Thank you, Mama. I've noted that you had a vaginal delivery.\n\n"
                    "What date did you give birth? You can reply like **7/09/2026** or **2026-09-07**.",
                    mother.first_name,
                ),
            )
            return
        if value in {"2", "c-section", "c section", "csection", "c-section delivery", "cesarean", "caesarean"}:
            mother.delivery_type = DeliveryType.c_section
            mother.pending_prompt = "awaiting_delivery_date"
            db.commit()
            await send_text(
                wa_id,
                personalize(
                    "Thank you, Mama. I've noted that you had a C-section.\n\n"
                    "What date did you give birth? You can reply like **7/09/2026** or **2026-09-07**.",
                    mother.first_name,
                ),
            )
            return
        await send_text(
            wa_id,
            personalize(
                "I'm here with you, Mama. Reply **1** for Vaginal Delivery or **2** for C-Section. You can also tell me the delivery type in your own words.",
                mother.first_name,
            ),
        )
        return

    if mother.pending_prompt == "awaiting_delivery_date":
        parsed = parse_delivery_date(clean_text)
        if parsed:
            mother.delivery_date = parsed
            mother.pending_prompt = "main_menu"
            day = postpartum_day(mother)
            db.commit()
            await send_text(
                wa_id,
                personalize(
                    f"Got it, Mama. I've saved your delivery date as {parsed.strftime('%d %B %Y')}.\n\n"
                    f"You're about **day {day} postpartum**, so I'll use that context when we talk about your recovery.\n\n"
                    + MAIN_MENU,
                    mother.first_name,
                ),
            )
            return
        await send_text(
            wa_id,
            personalize(
                "I couldn't recognise that date. Please send your delivery date as **DD/MM/YYYY** or **YYYY-MM-DD** (for example, 07/09/2026).",
                mother.first_name,
            ),
        )
        return

    # Handle the emotional-support safety check.
    if mother.pending_prompt == "mood_safety_check":
        if value in AFFIRMATIVE:
            mother.pending_prompt = "emotions"
            db.commit()
            await send_text(
                wa_id,
                personalize(
                    "Thank you for telling me. I'm glad you're safe right now. You don't have to carry everything at once.\n\n"
                    "What has been weighing on you most today?",
                    mother.first_name,
                ),
            )
            return
        if value in NEGATIVE:
            mother.pending_prompt = "human_support"
            mother.bot_status = "human_review"
            mother.human_review_since = datetime.utcnow()
            db.commit()
            await send_text(
                wa_id,
                personalize(
                    "Thank you for telling me. Please don't stay alone with this. Tell a trusted person who can be with you right now and seek urgent help from a qualified healthcare professional or emergency service. If you are in immediate danger, contact your local emergency service now.\n\n"
                    "You deserve immediate, human support.",
                    mother.first_name,
                ),
            )
            return

    # Interpret a follow-up using the existing topic before generic intent
    # detection. This prevents the old repeated-listening loop.
    if mother.current_topic:
        contextual = contextual_response(
            clean_text,
            current_topic=mother.current_topic,
            postpartum_days=postpartum_day(mother),
        )
        if contextual:
            remember_topic(mother, clean_text)
            if mother.current_topic == "mood" and "safe right now" in contextual.text.lower():
                mother.pending_prompt = "mood_safety_check"
            else:
                mother.pending_prompt = mother.current_topic
            reply = personalize(contextual.text, mother.first_name)
            if contextual.follow_up:
                reply += "\n\n" + personalize(contextual.follow_up, mother.first_name)
            db.commit()
            await send_text(wa_id, reply)
            return

    menu = menu_reply(mother, clean_text)
    if menu:
        db.commit()
        await send_text(wa_id, personalize(menu, mother.first_name))
        return

    brain_response = answer_postpartum_question(clean_text)
    if brain_response:
        remember_topic(mother, clean_text)
        if detect_intent(clean_text) == "greeting":
            mother.pending_prompt = "main_menu"
        elif brain_response.follow_up:
            mother.pending_prompt = mother.current_topic or mother.pending_prompt
        reply = personalize(brain_response.text, mother.first_name)
        if brain_response.follow_up:
            reply += "\n\n" + personalize(brain_response.follow_up, mother.first_name)
        db.commit()
        await send_text(wa_id, reply)
        return

    if mother.current_topic:
        prompt = (
            f"I'm with you, {mother.first_name}. We're talking about your {mother.current_topic.replace('_', ' ')}.\n\n"
            "Tell me a little more about what you're experiencing, and we'll take it one step at a time."
        )
    else:
        prompt = personalize(
            "I'm listening, Mama. You don't have to find the perfect words. Tell me what is happening in your body, how you are feeling emotionally, or what is worrying you about your baby.",
            mother.first_name,
        )
    db.commit()
    await send_text(wa_id, prompt)
