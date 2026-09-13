import re
from dataclasses import dataclass
from enum import Enum


class TriageLevel(str, Enum):
    GREEN = "GREEN"
    MEDIUM = "MEDIUM"
    CRITICAL = "CRITICAL"


@dataclass
class ScanResult:
    triage_level: TriageLevel
    matched_terms: list
    category: str
    response_template: str = ""


CRITICAL_PATTERNS = [
    ("heavy_bleeding", r"\b(heavy|soak(?:ing)?|soaked|flooding)\b.{0,80}\b(bleed(?:ing)?|blood|pad)\b"),
    ("severe_bleeding", r"\b(bleed(?:ing)?|blood)\b.{0,80}\b(won't stop|doesn't stop|not stopping)\b"),
    ("seizure", r"\b(seizure|convulsion|convulsions|fits?)\b"),
    ("breathing", r"\b(can't breathe|cannot breathe|difficulty breathing|trouble breathing|shortness of breath|breathless)\b"),
    ("chest", r"\b(chest pain|chest pressure|tightness in (my|the) chest)\b"),
    ("fainting", r"\b(fainted|fainting|passed out|unconscious|lost consciousness)\b"),
    ("severe_headache_vision", r"\b(severe|worst|terrible)\b.{0,60}\b(headache|head pain)\b.{0,60}\b(blurred vision|blurry vision|can't see|vision changes)\b"),
    ("vision", r"\b(blurred vision|blurry vision|vision changes|seeing spots|can't see properly)\b"),
    ("self_harm", r"\b(hurt myself|harm myself|kill myself|end my life|suicidal)\b"),
    ("high_fever", r"\b(fever|temperature)\b.{0,50}\b(38|39|40)\s*(?:°|degrees?)?\s*(?:c|celsius)?\b"),
    ("very_unwell", r"\b(very unwell|extremely unwell|seriously ill|feel like i(?:'m| am) dying)\b"),
]

MEDIUM_PATTERNS = [
    ("fever", r"\b(fever|temperature|hot body|homa)\b"),
    ("headache", r"\b(headache|head pain)\b"),
    ("pain", r"\b(pain|painful|sore|soreness|cramp|cramps)\b"),
    ("emotional_distress", r"\b(overwhelmed|crying|anxious|panic|worried|scared|hopeless)\b"),
]


def get_empathetic_response(result: ScanResult):
    if result.triage_level == TriageLevel.CRITICAL:
        return (
            "Mama, I'm glad you told me. What you're describing needs urgent professional assessment. "
            "Please go to the nearest hospital or emergency service now, and ask a trusted person to stay with you if possible. "
            "I can support you with information, but I cannot diagnose or safely manage an emergency over chat."
        )
    if result.triage_level == TriageLevel.MEDIUM:
        return (
            "Thank you for telling me, Mama. I hear you. This deserves attention rather than being brushed aside. "
            "Please contact your maternity team, clinic or a qualified healthcare professional for advice, especially if it is worsening or not settling. "
            "I'm here to help you understand what you're experiencing."
        )
    return "Thank you for sharing, Mama. I'm here with you."


def scan_message(text: str) -> ScanResult:
    value = re.sub(r"\s+", " ", (text or "").lower().strip())
    if not value:
        return ScanResult(TriageLevel.GREEN, [], "none", get_empathetic_response(ScanResult(TriageLevel.GREEN, [], "none")))

    for category, pattern in CRITICAL_PATTERNS:
        if re.search(pattern, value):
            return ScanResult(TriageLevel.CRITICAL, [category], category, get_empathetic_response(ScanResult(TriageLevel.CRITICAL, [category], category)))

    for category, pattern in MEDIUM_PATTERNS:
        if re.search(pattern, value):
            return ScanResult(TriageLevel.MEDIUM, [category], category, get_empathetic_response(ScanResult(TriageLevel.MEDIUM, [category], category)))

    return ScanResult(TriageLevel.GREEN, [], "none", get_empathetic_response(ScanResult(TriageLevel.GREEN, [], "none")))
