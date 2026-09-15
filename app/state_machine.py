from datetime import date, datetime
from sqlalchemy.orm import Session
from app.db import Mother, DeliveryType
from app.safety_scanner import scan_message, TriageLevel
from app.whatsapp_client import send_text, send_buttons
from app.content import WELCOME_MESSAGE, WELCOME_BUTTONS
from app.postpartum_brain import answer_postpartum_question, detect_intent
from app.contextual_response import contextual_response
from app.topic_router import match_topic_route
import logging

logger = logging.getLogger(__name__)

MAIN_MENU = (
    "What would you like help with today?\n\n"
    "1. My recovery\n2. My emotions\n3. My body\n4. Breastfeeding\n"
    "5. My baby\n6. Food & hydration\n7. Sleep & rest\n8. Cultural care\n"
    "9. I just want to talk\n\nYou can reply with a number, or simply tell me what's happening."
)

RECOVERY_MENU = (
    "Let's make recovery feel manageable.\n\n1. Physical recovery\n2. Food & hydration\n"
    "3. Rest & sleep\n4. Breastfeeding & breasts\n5. Emotional wellbeing\n6. Baby care\n"
    "7. C-section recovery\n8. Vaginal birth recovery\n9. Traditional & cultural care\n0. Back to main menu\n\n"
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
        db.add(mother); db.commit(); db.refresh(mother)
    elif first_name and mother.first_name == "Mama":
        mother.first_name = first_name; db.commit()
    return mother


def personalize(text: str, first_name: str) -> str:
    return text.replace("Mama", (first_name or "Mama").strip() or "Mama")


def remember_topic(mother: Mother, text: str):
    route = match_topic_route(text)
    if route:
        mother.current_topic = route.topic
        return route.topic
    intent = detect_intent(text)
    if intent and intent != "greeting":
        mother.current_topic = intent
    return intent


def remember_response_context(mother: Mother, follow_up: str = ""):
    mother.pending_question = follow_up or None
    mother.expected_answer_type = "free_text" if follow_up else None


def set_topic_prompt(mother: Mother, topic: str, prompt: str):
    mother.current_topic = topic
    mother.pending_prompt = topic
    mother.pending_question = prompt
    mother.expected_answer_type = "free_text"
    return prompt


def postpartum_day(mother: Mother):
    if not mother.delivery_date:
        return None
    return max(0, (date.today() - mother.delivery_date).days)


def parse_delivery_date(text: str):
    value = (text or "").strip()
    formats = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y")
    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt).date()
            if parsed <= date.today(): return parsed
        except ValueError: pass
    for fmt in ("%d %B %Y", "%d %b %Y"):
        try:
            parsed = datetime.strptime(value, fmt).date()
            if parsed <= date.today(): return parsed
        except ValueError: pass
    return None


def menu_reply(mother: Mother, text: str):
    value = text.lower().strip(); state = mother.pending_prompt or ""
    if value in MENU_COMMANDS:
        mother.pending_prompt = "main_menu"
        mother.pending_question = None
        mother.expected_answer_type = None
        return MAIN_MENU
    if value in TALK_COMMANDS:
        mother.current_topic = "talking"
        mother.pending_prompt = "talking"
        return set_topic_prompt(mother, "talking", "What's on your mind right now?")
    if state == "main_menu":
        choices = {
            "1": ("recovery", "What part of your recovery would you like help with right now?"),
            "2": ("emotions", "What's been weighing on you most right now?"),
            "3": ("body", "Which change in your body would you like to talk about first?"),
            "4": ("breastfeeding", "Is your main concern latch, pain, milk supply, or your baby's feeding pattern?"),
            "5": ("baby", "What is worrying you about your baby right now?"),
            "6": ("nutrition", "Are you struggling more with appetite, getting enough fluids, or knowing what foods support recovery?"),
            "7": ("sleep", "Are you getting any opportunity to rest, and what is making sleep or rest difficult?"),
            "8": ("cultural", "Which cultural or traditional practice would you like to talk about?"),
            "9": ("talking", "What's on your mind right now?"),
        }
        if value in choices:
            topic, prompt = choices[value]
            return set_topic_prompt(mother, topic, prompt)
    if state == "recovery_menu":
        choices = {
            "0": ("main_menu", None),
            "1": ("physical_recovery", "What physical change or symptom are you noticing right now?"),
            "2": ("nutrition", "Are you struggling more with appetite, getting enough fluids, or knowing what foods support recovery?"),
            "3": ("sleep", "Are you getting any opportunity to rest, and what is making sleep or rest difficult?"),
            "4": ("breastfeeding", "Is your main concern latch, pain, milk supply, or your baby's feeding pattern?"),
            "5": ("emotions", "What's been weighing on you most right now?"),
            "6": ("baby", "What is worrying you about your baby right now?"),
            "7": ("csection", "What are you noticing around your C-section recovery right now?"),
            "8": ("perineum", "What are you noticing in your recovery after the vaginal birth?"),
            "9": ("cultural", "Which cultural or traditional practice would you like to talk about?"),
        }
        if value in choices:
            topic, prompt = choices[value]
            if topic == "main_menu":
                mother.pending_prompt = "main_menu"
                mother.pending_question = None
                mother.expected_answer_type = None
                return MAIN_MENU
            return set_topic_prompt(mother, topic, prompt)
    return None


async def handle_message(db: Session, wa_id: str, text: str, first_name: str):
    mother = get_or_create_mother(db, wa_id, first_name)
    clean_text = (text or "").strip()
    if not clean_text: return

    current_day = postpartum_day(mother)
    scan_result = scan_message(clean_text, postpartum_days=current_day)

    if scan_result.triage_level == TriageLevel.CRITICAL:
        mother.triage_level = TriageLevel.CRITICAL
        mother.pending_question = None
        mother.expected_answer_type = None
        db.commit()
        await send_text(wa_id, personalize(scan_result.response_template, mother.first_name))
        return

    value = clean_text.lower().strip()
    if (not mother.delivery_type or mother.delivery_type == DeliveryType.unknown) and mother.pending_prompt is None:
        mother.pending_prompt = "awaiting_delivery_type"; db.commit()
        await send_buttons(wa_id, WELCOME_MESSAGE.format(name=mother.first_name), WELCOME_BUTTONS); return

    if mother.pending_prompt == "awaiting_delivery_type":
        if value in {"1", "vaginal", "vaginal delivery", "normal delivery"}:
            mother.delivery_type = DeliveryType.vaginal; mother.pending_prompt = "awaiting_delivery_date"; db.commit()
            await send_text(wa_id, personalize("Thank you, Mama. I've noted that you had a vaginal delivery.\n\nWhat date did you give birth? Reply like 07/09/2026 or 2026-09-07.", mother.first_name)); return
        if value in {"2", "c-section", "c section", "csection", "c-section delivery", "cesarean", "caesarean"}:
            mother.delivery_type = DeliveryType.c_section; mother.pending_prompt = "awaiting_delivery_date"; db.commit()
            await send_text(wa_id, personalize("Thank you, Mama. I've noted that you had a C-section.\n\nWhat date did you give birth? Reply like 07/09/2026 or 2026-09-07.", mother.first_name)); return
        await send_text(wa_id, personalize("Reply 1 for Vaginal Delivery or 2 for C-Section. You can also tell me the delivery type in your own words.", mother.first_name)); return

    if mother.pending_prompt == "awaiting_delivery_date":
        parsed = parse_delivery_date(clean_text)
        if parsed:
            mother.delivery_date = parsed; mother.pending_prompt = "main_menu"; day = postpartum_day(mother); db.commit()
            await send_text(wa_id, personalize(f"Got it, Mama. I've saved your delivery date as {parsed.strftime('%d %B %Y')}.\n\nYou're about day {day} postpartum.\n\n" + MAIN_MENU, mother.first_name)); return
        await send_text(wa_id, personalize("I couldn't recognise that date. Please send DD/MM/YYYY or YYYY-MM-DD.", mother.first_name)); return

    if mother.pending_prompt == "mood_safety_check":
        if value in AFFIRMATIVE:
            mother.pending_prompt = "emotions"; db.commit()
            await send_text(wa_id, personalize("Thank you for telling me. I'm glad you're safe right now. What has been weighing on you most today?", mother.first_name)); return
        if value in NEGATIVE:
            mother.pending_prompt = "human_support"; mother.bot_status = "human_review"; mother.human_review_since = datetime.utcnow(); db.commit()
            await send_text(wa_id, personalize("Thank you for telling me. Please don't stay alone with this. Tell a trusted person who can be with you and seek urgent help from a qualified healthcare professional or emergency service now. You deserve immediate support.", mother.first_name)); return

    # Explicit menu commands and broad topic labels must be processed before
    # stale conversational context. A mother's new topic should never inherit
    # the previous topic merely because the new message is short.
    menu = menu_reply(mother, clean_text)
    if menu:
        db.commit()
        route = match_topic_route(clean_text)
        if route:
            reply = route.response + "\n\n" + route.follow_up
        elif mother.current_topic == "main_menu":
            reply = menu
        else:
            reply = menu
        await send_text(wa_id, personalize(reply, mother.first_name)); return

    route = match_topic_route(clean_text)
    if route:
        mother.current_topic = route.topic
        mother.pending_prompt = route.topic
        mother.pending_question = route.follow_up
        mother.expected_answer_type = "free_text"
        db.commit()
        reply = route.response + "\n\n" + route.follow_up
        await send_text(wa_id, personalize(reply, mother.first_name)); return

    contextual = contextual_response(
        clean_text,
        current_topic=mother.current_topic,
        postpartum_days=current_day,
        pending_question=mother.pending_question,
        expected_answer_type=mother.expected_answer_type,
    )

    if scan_result.triage_level == TriageLevel.MEDIUM:
        clinical_text = scan_result.response_template
        brain_response = contextual or answer_postpartum_question(clean_text)
        if brain_response:
            remember_topic(mother, clean_text)
            reply = personalize(brain_response.text, mother.first_name)
            if brain_response.follow_up:
                reply += "\n\n" + personalize(brain_response.follow_up, mother.first_name)
            if clinical_text and clinical_text not in reply:
                reply += "\n\n" + personalize(clinical_text, mother.first_name)
            mother.pending_prompt = mother.current_topic or "follow_up"
            mother.triage_level = TriageLevel.MEDIUM
            remember_response_context(mother, brain_response.follow_up)
            db.commit(); await send_text(wa_id, reply); return
        mother.triage_level = TriageLevel.MEDIUM
        db.commit(); await send_text(wa_id, personalize(clinical_text, mother.first_name)); return

    if contextual:
        remember_topic(mother, clean_text)
        mother.pending_prompt = mother.current_topic
        reply = personalize(contextual.text, mother.first_name)
        if contextual.follow_up:
            reply += "\n\n" + personalize(contextual.follow_up, mother.first_name)
        remember_response_context(mother, contextual.follow_up)
        db.commit(); await send_text(wa_id, reply); return

    brain_response = answer_postpartum_question(clean_text)
    if brain_response:
        intent = remember_topic(mother, clean_text)
        mother.pending_prompt = "main_menu" if intent == "greeting" else (mother.current_topic or mother.pending_prompt)
        reply = personalize(brain_response.text, mother.first_name)
        if brain_response.follow_up: reply += "\n\n" + personalize(brain_response.follow_up, mother.first_name)
        remember_response_context(mother, brain_response.follow_up)
        db.commit(); await send_text(wa_id, reply); return

    if mother.current_topic:
        prompt = f"I'm with you, {mother.first_name}. We're talking about your {mother.current_topic.replace('_', ' ')}. Tell me a little more about what you're experiencing, and we'll take it one step at a time."
    else:
        prompt = personalize("I'm listening, Mama. You don't have to find the perfect words. Tell me what is happening in your body, how you are feeling emotionally, or what is worrying you about your baby.", mother.first_name)
    remember_response_context(mother, "Tell me a little more about what you're experiencing.")
    db.commit(); await send_text(wa_id, prompt)
