from dataclasses import dataclass
import re


@dataclass(frozen=True)
class TopicRoute:
    topic: str
    aliases: tuple[str, ...]
    response: str
    follow_up: str


TOPIC_ROUTES = (
    TopicRoute(
        "recovery",
        ("my recovery", "recovery", "postpartum recovery"),
        "Absolutely, Mama. We can take your postpartum recovery one part at a time — bleeding, soreness, wound healing, feeding, rest, nourishment, body changes or how you're feeling emotionally.",
        "What part of your recovery would you like help with right now?",
    ),
    TopicRoute(
        "emotions",
        ("my emotions", "my emotional wellbeing", "emotional wellbeing", "emotional well-being"),
        "We can talk about how you're feeling without forcing every emotion into a medical label. I'm listening, and you can tell me what has been hardest lately.",
        "What's been weighing on you most right now?",
    ),
    TopicRoute(
        "body",
        ("my body", "body changes", "changes in my body"),
        "We can talk through the changes you're noticing in your body after birth and what feels unfamiliar or concerning.",
        "Which change in your body would you like to talk about first?",
    ),
    TopicRoute(
        "breastfeeding",
        ("breastfeeding", "breastfeeding support", "breastfeeding & breasts", "breastfeeding and breasts"),
        "We can talk about breastfeeding, latch, milk supply, feeding comfort or changes in your breasts. You don't have to figure it out alone.",
        "Is your main concern latch, pain, milk supply, or your baby's feeding pattern?",
    ),
    TopicRoute(
        "baby",
        ("my baby", "baby care", "my baby's care"),
        "Absolutely, Mama. We can talk about your baby's feeding, sleep, crying, jaundice, cord care or another change you're noticing.",
        "What is worrying you about your baby right now?",
    ),
    TopicRoute(
        "nutrition",
        ("food & hydration", "food and hydration", "nutrition", "food", "hydration"),
        "We can talk about food, appetite, fluids and practical nourishment during recovery in a way that fits your culture, budget and health needs.",
        "Are you struggling more with appetite, getting enough fluids, or knowing what foods support recovery?",
    ),
    TopicRoute(
        "sleep",
        ("sleep & rest", "sleep and rest", "rest & sleep", "rest and sleep", "sleep", "rest"),
        "Let's talk about rest without judging you for being exhausted. Your body is recovering while you're caring for a newborn.",
        "Are you getting any opportunity to rest, and what is making sleep or rest difficult?",
    ),
    TopicRoute(
        "cultural",
        ("cultural care", "cultural practices", "cultural practice", "traditional & cultural care", "traditional and cultural care", "traditional care", "cultural"),
        "Absolutely, Mama. We can talk about postpartum cultural and traditional care without judging your traditions. This can include family support, foods, bathing, massage, belly binding, herbs, spiritual or naming rituals, and support from elders.",
        "Which cultural or traditional practice would you like to talk about?",
    ),
    TopicRoute(
        "talking",
        ("i just want to talk", "just want to talk", "talk", "i want to talk"),
        "I'm here, and you don't need to turn this into a medical question. Tell me what's on your mind, exactly as it comes.",
        "What's on your mind right now?",
    ),
    TopicRoute(
        "physical_recovery",
        ("physical recovery",),
        "Let's focus on your physical recovery, Mama. Your body is healing from pregnancy and birth, and what recovery feels like can depend on how you gave birth and how many days postpartum you are.",
        "What physical change or symptom are you noticing right now?",
    ),
    TopicRoute(
        "csection",
        ("c-section recovery", "c section recovery", "cesarean recovery", "caesarean recovery"),
        "Let's focus on your C-section recovery, including wound care, pain, movement and the changes you are noticing while you heal.",
        "What are you noticing around your C-section recovery right now?",
    ),
    TopicRoute(
        "physical_recovery",
        ("vaginal birth recovery", "vaginal delivery recovery"),
        "Let's focus on recovery after a vaginal birth, including bleeding, soreness, stitches or tears, pelvic changes and general healing.",
        "What are you noticing in your recovery after the vaginal birth?",
    ),
)


def _normalise(text: str) -> str:
    value = (text or "").lower().strip()
    value = re.sub(r"[’']", "'", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" .,!?:;-")


def match_topic_route(text: str) -> TopicRoute | None:
    value = _normalise(text)
    if not value:
        return None
    for route in TOPIC_ROUTES:
        if value in {_normalise(alias) for alias in route.aliases}:
            return route
    return None
