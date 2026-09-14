import re
from dataclasses import dataclass

from app.postpartum_brain import BrainResponse, RESPONSES, detect_intent


@dataclass(frozen=True)
class Context:
    current_topic: str | None = None
    postpartum_days: int | None = None


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower().strip())


def extract_days(text: str) -> int | None:
    value = normalise(text)
    patterns = (
        r"\bday\s+(\d{1,3})\b",
        r"\b(\d{1,3})\s+days?\s+(?:postpartum|after birth|after delivery)\b",
        r"\b(\d{1,3})\s*(?:dpp)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            days = int(match.group(1))
            if 0 <= days <= 365:
                return days
    return None


def contextual_response(text: str, current_topic: str | None = None, postpartum_days: int | None = None) -> BrainResponse | None:
    """Interpret short follow-ups using the mother's existing conversation context."""
    value = normalise(text)
    topic = current_topic or detect_intent(value)
    mentioned_days = extract_days(value)
    days = mentioned_days if mentioned_days is not None else postpartum_days

    if topic == "lochia":
        has_unusual_smell = any(term in value for term in (
            "smell", "smells", "smelly", "foul", "offensive", "bad odour", "bad odor"
        ))
        dark_red = any(term in value for term in (
            "dark red", "dark-red", "deep red", "reddish brown", "red brown"
        ))
        heavier = any(term in value for term in (
            "heavier", "getting heavier", "more blood", "more bleeding", "soaking", "soaked"
        ))
        fever = any(term in value for term in ("fever", "temperature", "chills", "shivering"))
        worsening_pain = any(term in value for term in (
            "worsening pain", "getting worse", "severe pain", "bad pain", "pelvic pain", "tummy pain"
        ))

        if mentioned_days is not None:
            return BrainResponse(
                f"Thank you for telling me, Mama. I've noted that you're about day {mentioned_days} postpartum. Lochia can change as recovery progresses, so the next thing I want to understand is how the bleeding is changing and whether you have any other symptoms.",
                "Is the bleeding getting lighter overall, and what colour and amount are you seeing?"
            )

        if has_unusual_smell and (fever or worsening_pain):
            return BrainResponse(
                "Thank you for clarifying, Mama. An unusual or foul smell from postpartum bleeding or discharge together with fever or worsening tummy/pelvic pain needs prompt medical assessment. Please contact your maternity team, clinic or a qualified healthcare professional today.",
                "Is the bleeding getting heavier, and do you feel unusually unwell or dizzy?",
            )

        if has_unusual_smell:
            return BrainResponse(
                "Thank you for telling me, Mama. Lochia can vary in colour and amount, but an unusual or foul smell is something I don't want you to ignore. Please contact your maternity team, clinic or a qualified healthcare professional for advice and assessment, especially if you also develop fever, chills, worsening pain, heavier bleeding or feel unwell.",
                "Is the bleeding getting lighter overall, or is it becoming heavier?",
            )

        if dark_red and days is not None and days >= 7:
            return BrainResponse(
                "Thank you for clarifying, Mama. Lochia can vary in colour, but around the end of the first week it should generally be trending lighter and less heavy. If it is staying very red or becoming heavier again, it is worth checking with your maternity team, especially if you have pain, fever, dizziness or feel unwell.",
                "Is the bleeding getting lighter overall, or is it becoming heavier again?",
            )

        if heavier:
            return BrainResponse(
                "Thank you for telling me, Mama. A change toward heavier postpartum bleeding deserves attention. Please contact your maternity team or a qualified healthcare professional for advice, and seek urgent care if the bleeding becomes suddenly very heavy or you feel faint or very unwell.",
                "Has the amount increased suddenly, or has it been gradually getting heavier?",
            )

    if topic in {"mood", "hope", "anxiety"}:
        if any(term in value for term in (
            "depressed", "very low", "hopeless", "not myself", "can't cope", "cannot cope", "overwhelmed"
        )):
            return RESPONSES["mood"]

        if any(term in value for term in ("anxious", "anxiety", "panic", "worried", "scared")):
            return RESPONSES["anxiety"]

    if topic == "pain" and any(term in value for term in ("where", "stomach", "back", "pelvis", "head", "breast")):
        return RESPONSES["pain"]

    return None
