"""Small, deterministic helpers for Care Sister follow-up conversations."""

import re
from datetime import date


NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14,
}


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower().strip())


def extract_days(text: str) -> int | None:
    value = normalise(text)
    match = re.search(r"\b(\d{1,3})\s*(?:day|days|d)\b", value)
    if match:
        return int(match.group(1))
    for word, number in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\s+(?:day|days)\b", value):
            return number
    return None


def is_affirmative(text: str) -> bool:
    return normalise(text) in {"yes", "yeah", "yep", "y", "true", "i do", "i am"}


def is_negative(text: str) -> bool:
    return normalise(text) in {"no", "nope", "n", "false", "not really", "i don't", "i am not"}


def postpartum_day(delivery_date: date | None) -> int | None:
    if delivery_date is None:
        return None
    return max(0, (date.today() - delivery_date).days)


def recovery_stage(day: int | None) -> str:
    if day is None:
        return "unknown"
    if day <= 14:
        return "early recovery"
    if day <= 42:
        return "healing recovery"
    return "ongoing recovery"
