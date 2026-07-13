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


def get_empathetic_response(result):
    if result.triage_level == TriageLevel.CRITICAL:
        return (
            "Mama, my heart is with you right now. This sounds serious and your body is asking for help. "
            "Please don't wait — go to the nearest hospital or call for help immediately. "
            "You are not alone. A care sister has been alerted."
        )
    elif result.triage_level == TriageLevel.MEDIUM:
        return (
            "Thank you for sharing this with me, Mama. I hear you, and it's okay to feel this way. "
            "Please keep an eye on it and reach out to your clinic if it gets worse. "
            "I'm here for you."
        )
    return "Thank you for telling me, dear. How else can I support you today?"


# Patterns
CRITICAL_PATTERNS = [
    r"\b(heavy|soak|soaking)\b.*\b(bleed|blood|pad)\b",
    r"\b(fever|hot body|homa)\b",
    r"\b(fits?|seizure|convuls)\b",
    r"\b(blur|blurry|can't see)\b",
    r"\b(hurt myself|kill myself|die)\b",
]

MEDIUM_PATTERNS = [
    r"\b(headache|pain|overwhelmed|crying|anxious)\b",
]


def scan_message(text: str):
    text = text.lower()
    for pattern in CRITICAL_PATTERNS:
        if re.search(pattern, text):
            return ScanResult(TriageLevel.CRITICAL, [pattern], "emergency", get_empathetic_response(ScanResult(TriageLevel.CRITICAL, [], "")))
    
    for pattern in MEDIUM_PATTERNS:
        if re.search(pattern, text):
            return ScanResult(TriageLevel.MEDIUM, [pattern], "concern", get_empathetic_response(ScanResult(TriageLevel.MEDIUM, [], "")))
    
    return ScanResult(TriageLevel.GREEN, [], None, "Thank you for sharing, Mama.")
