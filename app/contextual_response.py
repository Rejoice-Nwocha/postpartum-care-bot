from dataclasses import dataclass

from app.postpartum_brain import BrainResponse, RESPONSES, detect_intent


@dataclass(frozen=True)
class Context:
    current_topic: str | None = None
    postpartum_days: int | None = None


def contextual_response(text: str, current_topic: str | None = None, postpartum_days: int | None = None) -> BrainResponse | None:
    """Interpret a follow-up using the mother's existing conversation context."""
    value = " ".join((text or "").lower().strip().split())
    topic = current_topic or detect_intent(value)

    if topic == "lochia":
        has_unusual_smell = any(term in value for term in (
            "smell", "smells", "smelly", "foul", "offensive", "bad odour", "bad odor"
        ))
        dark_red = any(term in value for term in (
            "dark red", "dark-red", "deep red", "reddish brown", "red brown"
        ))

        if has_unusual_smell:
            return BrainResponse(
                "Thank you for telling me, Mama. Dark-red or reddish-brown lochia can occur during postpartum recovery, but an unusual or foul smell is something I don't want you to ignore. It can be a sign that you need to be checked for an infection.\n\nPlease contact your midwife, maternity clinic, doctor or other qualified healthcare professional today for advice and assessment, especially if you also have fever, chills, worsening tummy or pelvic pain, heavier bleeding or feel unwell. I can't diagnose the cause over chat.",
                "Do you also have a fever or chills, worsening tummy or pelvic pain, heavier bleeding, or feel unusually unwell?",
            )

        if dark_red and postpartum_days is not None and postpartum_days >= 7:
            return BrainResponse(
                "Thank you for clarifying, Mama. Lochia can vary in colour, but around the end of the first week it should generally be becoming lighter and less heavy. If it is staying very red or becoming heavier again, it is worth checking with your maternity team, especially if you have pain, fever, dizziness or feel unwell.",
                "Is the bleeding getting lighter overall, or is it becoming heavier again?",
            )

    if topic == "mood" and any(term in value for term in (
        "depressed", "very low", "hopeless", "not myself", "can't cope", "cannot cope"
    )):
        return RESPONSES["mood"]

    return None
