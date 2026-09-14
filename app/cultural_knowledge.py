"""Global cultural-awareness layer for ACHOT Care Sister.

This module describes cultural postpartum traditions without presenting them as
medical treatment. Care Sister should respect cultural meaning while keeping
professional healthcare assessment as the safety boundary.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CulturalPractice:
    name: str
    regions: tuple[str, ...]
    category: str
    description: str
    safety_level: str
    guidance: str


CULTURAL_PRACTICES = [
    CulturalPractice(
        "Postpartum rest and family support",
        ("Africa", "Asia", "Middle East", "Europe", "Latin America", "Caribbean", "Indigenous communities"),
        "rest_and_community",
        "Protected rest, practical help, shared meals and family or community support are found in many postpartum traditions.",
        "generally compatible",
        "Respect the tradition and encourage the mother to accept safe practical support while continuing routine and urgent healthcare.",
    ),
    CulturalPractice(
        "Omugwo and elder-led support",
        ("Nigeria", "Igbo communities", "West Africa"),
        "family_support",
        "In some Nigerian communities, an older female relative supports the new mother with food, baby care and household responsibilities.",
        "generally compatible",
        "Treat this as family and cultural support rather than a replacement for clinical care.",
    ),
    CulturalPractice(
        "Warm nourishing postpartum foods",
        ("Africa", "South Asia", "East Asia", "Southeast Asia", "Middle East", "Latin America", "Caribbean"),
        "food_and_nourishment",
        "Many cultures emphasize warm meals, soups, broths and nourishing foods during postpartum recovery.",
        "generally compatible",
        "Support culturally familiar foods that fit the mother's health needs, allergies and dietary restrictions.",
    ),
    CulturalPractice(
        "Forty-day or defined postpartum recovery periods",
        ("North Africa", "Middle East", "South Asia", "East Asia", "Southeast Asia", "Latin America", "Caribbean"),
        "rest_and_transition",
        "A defined period of rest, family care or ritual transition after birth is present in many communities.",
        "generally compatible",
        "The cultural meaning varies by community. A mother should still be able to obtain medical care during the recovery period.",
    ),
    CulturalPractice(
        "Gentle postpartum massage",
        ("Africa", "South Asia", "East Asia", "Southeast Asia", "Middle East", "Latin America", "Caribbean"),
        "bodywork",
        "Massage is used in some communities for comfort, relaxation and postpartum support.",
        "use caution",
        "Care Sister should not treat massage as medical treatment. Painful areas, healing wounds or other symptoms may require professional assessment.",
    ),
    CulturalPractice(
        "Abdominal or belly binding",
        ("Africa", "South Asia", "East Asia", "Southeast Asia", "Latin America", "Caribbean"),
        "body_support",
        "Wrapping or binding the abdomen is practiced in several communities as a cultural practice and for a feeling of support.",
        "use caution",
        "Care Sister should ask about comfort, breathing and wound recovery and should not present binding as necessary for healing or body shape.",
    ),
    CulturalPractice(
        "Traditional herbs and herbal preparations",
        ("Africa", "South Asia", "East Asia", "Southeast Asia", "Middle East", "Latin America", "Caribbean", "Indigenous communities"),
        "traditional_medicine",
        "Traditional and herbal medicine systems are used in many cultures for postpartum wellbeing.",
        "professional review",
        "Natural does not automatically mean safe. Ingredients, quality, interactions and breastfeeding considerations can matter, so medicinal use should be discussed with a qualified healthcare professional.",
    ),
    CulturalPractice(
        "Warm bathing and bathing traditions",
        ("Africa", "South Asia", "East Asia", "Southeast Asia", "Latin America", "Caribbean"),
        "bathing_and_comfort",
        "Warm bathing and culturally specific bathing rituals are used in many communities for comfort, cleanliness and transition.",
        "use caution",
        "Keep the practice compatible with wound-care instructions and avoid anything that causes pain or injury.",
    ),
    CulturalPractice(
        "Spiritual, blessing and naming rituals",
        ("Africa", "Middle East", "South Asia", "East Asia", "Southeast Asia", "Latin America", "Caribbean", "Indigenous communities", "Europe"),
        "spiritual_and_ritual",
        "Prayer, blessings, naming ceremonies, songs and other rituals may help families mark the transition into parenthood.",
        "generally compatible",
        "Respect the mother's beliefs and choices while making clear that rituals do not replace medical treatment when illness is suspected.",
    ),
    CulturalPractice(
        "Community meal support",
        ("Africa", "Asia", "Middle East", "Europe", "Latin America", "Caribbean", "Indigenous communities"),
        "community_support",
        "Relatives, neighbours and community groups may provide meals and practical help so the mother can focus on recovery and the baby.",
        "generally compatible",
        "Encourage safe support that reduces the mother's workload and isolation.",
    ),
    CulturalPractice(
        "Traditional warming or cooling beliefs",
        ("Africa", "South Asia", "East Asia", "Southeast Asia", "Middle East", "Latin America", "Caribbean"),
        "food_and_beliefs",
        "Some cultural systems classify foods, environments or activities as warming or cooling during postpartum recovery.",
        "use caution",
        "Care Sister can explain the cultural meaning without presenting these classifications as medical diagnoses or universal medical rules.",
    ),
    CulturalPractice(
        "Traditional birth-attendant or elder support",
        ("Africa", "South Asia", "Southeast Asia", "Latin America", "Indigenous communities"),
        "community_care",
        "Trusted elders and community caregivers can remain important sources of practical and emotional support after birth.",
        "use caution",
        "Respect the relationship while encouraging skilled healthcare assessment for symptoms, complications and routine postnatal care.",
    ),
    CulturalPractice(
        "Postpartum storytelling, music and oral traditions",
        ("Africa", "Asia", "Latin America", "Caribbean", "Indigenous communities", "Europe"),
        "emotional_support",
        "Songs, stories, advice from elders and shared family narratives can help mark the transition into parenthood.",
        "generally compatible",
        "Encourage supportive, non-shaming messages that help the mother feel connected and understood.",
    ),
]


ALIASES = {
    "omugwo": ("omugwo", "grandmother support", "mother-in-law support"),
    "binding": ("belly binding", "abdominal binding", "bind my belly", "wrap my belly"),
    "herbs": ("herb", "herbal", "traditional medicine", "herbal tea"),
    "massage": ("massage", "body massage"),
    "forty_day": ("40 day", "forty day", "40-day", "confinement"),
    "rest": ("rest", "stay indoors", "family support"),
    "food": ("pepper soup", "soup", "broth", "postpartum food", "warming food", "cold food"),
    "ritual": ("ritual", "blessing", "prayer", "naming", "ceremony", "spiritual"),
    "elder": ("elder", "traditional birth attendant", "grandmother", "auntie"),
}


def find_cultural_practice(text: str) -> CulturalPractice | None:
    value = (text or "").lower().strip()
    for key, terms in ALIASES.items():
        if any(term in value for term in terms):
            for practice in CULTURAL_PRACTICES:
                if key == "omugwo" and practice.name.startswith("Omugwo"):
                    return practice
                if key == "binding" and "binding" in practice.name.lower():
                    return practice
                if key == "herbs" and "herb" in practice.name.lower():
                    return practice
                if key == "massage" and "massage" in practice.name.lower():
                    return practice
                if key == "forty_day" and "forty-day" in practice.name.lower():
                    return practice
                if key == "food" and "food" in practice.name.lower():
                    return practice
                if key == "ritual" and "ritual" in practice.name.lower():
                    return practice
                if key == "elder" and "elder" in practice.name.lower():
                    return practice
                if key == "rest" and "rest" in practice.name.lower():
                    return practice
    return None


def cultural_response(text: str) -> str | None:
    practice = find_cultural_practice(text)
    if not practice:
        return None
    return (
        f"Mama, {practice.name.lower()} is a postpartum tradition found in some communities. "
        f"{practice.description}\n\n"
        f"Cultural context: {practice.guidance}\n\n"
        f"Safety level: {practice.safety_level}.\n\n"
        "I can help you understand the cultural practice, but I cannot diagnose a medical condition. "
        "If you have concerning symptoms or are unsure whether a practice is appropriate for you, "
        "please visit a hospital or speak with a qualified healthcare professional for an examination and proper diagnosis."
    )
