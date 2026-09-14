"""Deterministic clinical safety rules for Care Sister.

This layer is deliberately separate from the conversational brain. It identifies
high-signal postpartum warning-sign combinations and returns supportive routing
language; it does not diagnose. Clinical content should be reviewed by ACHOT's
qualified clinical advisor before production use.
"""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ClinicalResult:
    level: str
    response: str
    follow_up: str = ""


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower().strip())


def _has(value: str, *terms: str) -> bool:
    return any(term in value for term in terms)


def clinical_response(text: str, postpartum_days: int | None = None) -> ClinicalResult | None:
    """Return the safest deterministic response for recognised warning signs."""
    value = _normalise(text)

    # Immediate maternal emergencies.
    if _has(value, "can't breathe", "cannot breathe", "difficulty breathing", "shortness of breath", "chest pain", "chest tightness"):
        return ClinicalResult(
            "CRITICAL",
            "Mama, chest pain or difficulty breathing after birth needs urgent medical assessment. Please seek emergency medical care now or have someone take you to the nearest emergency department. Do not wait for the symptoms to pass.",
        )

    if _has(value, "passed out", "fainted", "fainting", "unconscious", "seizure", "convulsion"):
        return ClinicalResult(
            "CRITICAL",
            "Mama, fainting, loss of consciousness or a seizure after birth needs urgent medical assessment. Please seek emergency medical care now and have someone stay with you.",
        )

    if _has(value, "severe headache", "worst headache", "terrible headache") and _has(value, "blurred vision", "vision changes", "seeing spots", "can't see", "cannot see"):
        return ClinicalResult(
            "CRITICAL",
            "Mama, a severe headache together with vision changes after birth needs urgent medical assessment. Please seek emergency medical care now.",
        )

    # A broad "my leg is swollen" message is not enough by itself for the
    # emergency rule. Escalate when the wording points to one-sided/new calf or
    # leg symptoms, especially with pain, warmth or redness.
    one_sided_leg = _has(
        value,
        "one leg",
        "one calf",
        "only one leg",
        "only one calf",
        "left leg",
        "right leg",
        "left calf",
        "right calf",
    )
    leg_symptom = _has(value, "swollen", "swelling", "pain", "hurts", "red", "warm", "hot", "tender")
    if one_sided_leg and leg_symptom:
        return ClinicalResult(
            "CRITICAL",
            "Mama, new pain, warmth, redness or swelling affecting one leg after birth needs urgent medical assessment. Please seek medical care promptly and do not massage the painful area.",
        )

    if _has(value, "calf pain", "calf hurts") and leg_symptom:
        return ClinicalResult(
            "CRITICAL",
            "Mama, new calf pain or swelling after birth needs urgent medical assessment. Please seek medical care promptly and do not massage the painful area.",
        )

    # Postpartum bleeding/infection combinations.
    bleeding = _has(value, "bleeding", "blood", "lochia", "discharge", "soaking pad", "soaked pad")
    foul = _has(value, "foul smell", "foul-smelling", "bad smell", "bad odor", "bad odour", "smelly")
    fever = _has(value, "fever", "temperature", "chills", "shivering")
    pelvic_pain = _has(value, "pelvic pain", "tummy pain", "abdominal pain", "stomach pain", "worsening pain", "severe pain")
    heavy = _has(value, "very heavy", "heavy bleeding", "getting heavier", "more bleeding", "soaking through", "soaking a pad")
    dizzy = _has(value, "dizzy", "dizziness", "faint", "fainting", "heart pounding", "racing heart")

    if bleeding and heavy and dizzy:
        return ClinicalResult(
            "CRITICAL",
            "Mama, very heavy postpartum bleeding together with dizziness or faintness needs emergency medical care. Please seek emergency care now and have someone stay with you.",
        )

    if bleeding and foul and (fever or pelvic_pain):
        return ClinicalResult(
            "MEDIUM",
            "Mama, an unusual or foul smell from postpartum bleeding or discharge together with fever, chills or worsening tummy/pelvic pain needs prompt medical assessment. Please contact your maternity team, clinic or a qualified healthcare professional today.",
            "Are you also bleeding more heavily than before, feeling dizzy, or feeling unusually unwell?",
        )

    if heavy and postpartum_days is not None and postpartum_days >= 7:
        return ClinicalResult(
            "MEDIUM",
            "Mama, bleeding that is becoming heavier again during postpartum recovery deserves medical advice, particularly after the first week. Please contact your maternity team or a qualified healthcare professional for assessment.",
            "Did the increase happen suddenly, and are you feeling dizzy or unusually unwell?",
        )

    if foul and (fever or pelvic_pain):
        return ClinicalResult(
            "MEDIUM",
            "Mama, an unusual or foul smell from postpartum discharge together with fever or worsening pain should be assessed by a healthcare professional. Please contact your maternity team or clinic today.",
            "Are you feeling feverish, shivery, dizzy or unusually unwell?",
        )

    # Wound/perineal complications.
    wound = _has(value, "wound", "incision", "c-section wound", "c section wound", "stitches", "tear")
    wound_change = _has(value, "pus", "discharge", "opening", "red", "swollen", "worse", "worsening", "foul")
    if wound and wound_change and (fever or _has(value, "pus", "foul", "opening", "worsening pain")):
        return ClinicalResult(
            "MEDIUM",
            "Mama, a changing wound or stitches with signs such as worsening pain, redness, swelling, discharge or fever should be assessed by a healthcare professional. Please contact your maternity team promptly.",
            "Is the area becoming more painful, red, swollen, or producing discharge?",
        )

    # Breast infection pattern.
    breast = _has(value, "breast", "nipple")
    if breast and fever and _has(value, "red", "hot", "warm", "pain", "swollen"):
        return ClinicalResult(
            "MEDIUM",
            "Mama, breast pain or a hot/red/swollen area together with fever or feeling unwell needs medical assessment. Please contact a healthcare professional promptly.",
            "Is the painful area becoming more red or swollen, and do you feel feverish or unwell?",
        )

    # Urinary warning pattern.
    if _has(value, "burning when i pee", "burning when i urinate", "pain when i pee", "pain when i urinate") and fever:
        return ClinicalResult(
            "MEDIUM",
            "Mama, urinary burning together with fever after birth should be assessed by a healthcare professional because an infection may need treatment. Please contact your maternity team or clinic promptly.",
        )

    # Postpartum mental-health emergency: route to immediate human support without
    # describing or discussing methods of self-harm.
    if _has(value, "hearing voices", "seeing things", "not sure what is real", "very confused", "confused and not myself"):
        return ClinicalResult(
            "CRITICAL",
            "Mama, sudden severe confusion or experiences that make it difficult to tell what is real after birth need urgent medical assessment. Please stay with a trusted person and seek emergency medical care now.",
        )

    return None
