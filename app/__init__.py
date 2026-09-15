"""Care Sister application package.

The category router below makes broad menu/category phrases first-class
conversation intents. This prevents a mother's new request from inheriting an
unrelated previous topic such as sleep.
"""

from . import postpartum_brain as _brain


_CATEGORY_PHRASES = {
    "cultural": (
        "cultural practices",
        "cultural practice",
        "cultural care",
        "traditional care",
        "traditional practices",
        "traditional postpartum care",
        "postpartum traditions",
        "postpartum tradition",
        "cultural traditions",
    ),
    "recovery": ("my recovery", "physical recovery", "recovery"),
    "mood": ("my emotions", "emotions", "emotional wellbeing", "emotional well-being"),
    "body": ("my body",),
    "breastfeeding": ("breastfeeding", "breastfeeding & breasts"),
    "baby": ("my baby", "baby care", "care for my baby"),
    "nutrition": ("food & hydration", "food and hydration"),
    "sleep": ("sleep & rest", "rest & sleep"),
}


def _category_intent(text: str) -> str | None:
    value = " ".join((text or "").lower().strip().split())
    if not value:
        return None
    for intent, phrases in _CATEGORY_PHRASES.items():
        if value in phrases:
            return intent
    return None


_original_detect_intent = _brain.detect_intent
_original_answer = _brain.answer_postpartum_question


def detect_intent(text: str) -> str | None:
    """Recognise broad menu requests before keyword-based clinical intents."""
    return _category_intent(text) or _original_detect_intent(text)


def answer_postpartum_question(text: str):
    """Give useful entry responses for broad menu categories."""
    category = _category_intent(text)
    if category == "cultural":
        return _brain.BrainResponse(
            "Absolutely, Mama. Postpartum care can look different across families and cultures. We can talk about traditional practices while keeping your recovery and safety at the centre.\n\n"
            "Some areas we can explore include postpartum rest and family support, Omugwo, traditional foods, warm bathing, massage, belly binding, herbs, spiritual or naming rituals, and advice from elders.",
            "Which cultural or traditional practice are you or your family considering?"
        )
    if category == "recovery":
        return _brain.BrainResponse(
            "Absolutely, Mama. We can take your recovery one part at a time — physical healing, bleeding, pain, rest, breastfeeding, nourishment, emotional wellbeing, or care after your type of birth.",
            "What part of your recovery would you like to talk about first?"
        )
    if category == "baby":
        return _brain.BrainResponse(
            "Of course, Mama. We can talk about your baby's feeding, sleep, crying, cord, jaundice, or another change you've noticed.",
            "What are you noticing or worrying about with your baby right now?"
        )
    if category in {"mood", "body", "breastfeeding", "nutrition", "sleep"}:
        mapped = {
            "mood": "mood",
            "body": "body",
            "breastfeeding": "breastfeeding",
            "nutrition": "nutrition",
            "sleep": "sleep",
        }
        return _brain.RESPONSES[mapped[category]]
    return _original_answer(text)


# state_machine imports these names from app.postpartum_brain after the package
# initialiser runs, so broad menu phrases become consistent with normal intents.
_brain.detect_intent = detect_intent
_brain.answer_postpartum_question = answer_postpartum_question
