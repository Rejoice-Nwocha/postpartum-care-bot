WELCOME_MESSAGE = (
    "Hello Mama {name}.\n\n"
    "I'm Care Sister by ACHOT — a compassionate postpartum companion here to help you understand your recovery, "
    "your emotions, your body, breastfeeding, your baby, rest, nourishment and culturally rooted care.\n\n"
    "I can give general health information and help you notice when something needs professional attention. "
    "I cannot diagnose a medical condition.\n\n"
    "To personalize your recovery guidance, how did you give birth?"
)

WELCOME_BUTTONS = ["Vaginal Delivery", "C-Section Delivery"]


# Cultural content is intentionally framed as information, not endorsement.
# Practices should be evaluated for hygiene, heat/burn risk, ingestion risk,
# interactions with medicines, wound healing and other postpartum concerns.
CULTURAL_NOTES = {
    "west": (
        "In many West African communities, postpartum care may include a period of rest, "
        "family support and culturally familiar foods. Practices vary widely between families and countries."
    ),
    "east": (
        "Across East Africa, postpartum support may involve extended family care, warm foods or drinks, "
        "massage and community support. Practices differ between communities."
    ),
    "south": (
        "Across Southern Africa, postpartum traditions may emphasize rest, warmth, family support and, "
        "in some communities, forms of gentle body support. Practices differ between communities."
    ),
    "north": (
        "In parts of North Africa, postpartum traditions may include a period of rest, family care, "
        "nourishing foods and culturally meaningful routines. Practices differ between communities."
    ),
}


def get_cultural_advice(region: str = "general"):
    key = (region or "").lower().strip()[:4]
    if key in CULTURAL_NOTES:
        return CULTURAL_NOTES[key]
    return (
        "Postpartum traditions can provide comfort, identity and community support. "
        "Tell me the specific practice you are considering and I can help you think through its cultural meaning "
        "and safety considerations without judging your tradition."
    )
