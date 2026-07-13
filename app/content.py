WELCOME_MESSAGE = "Hello Mama {name}! Congratulations on the safe arrival of your bundle of joy! 👶🎉 We are so grateful to God for your safe delivery. The first 24 hours can feel completely overwhelming. Please remember to rest as much as you can while your baby sleeps. To help us send you the exact recovery tips you need for your body, please tell us how you delivered your baby:"

WELCOME_BUTTONS = ["Vaginal Delivery", "C-Section Delivery"]
# Cultural Validation Module - Respectful blending of tradition and modern care

CULTURAL_NOTES = {
    "west_africa": "In many West African traditions, the postpartum period is a time of rest and community support. Foods like pepper soup, yam, and leafy greens are often used to help with healing and milk production. Rest is highly valued.",
    "east_africa": "In East Africa, practices like drinking warm herbal teas and gentle massage are common. The support of family (Omugwo in some communities) is important. Focus on hydration and nutrient-rich foods.",
    "southern_africa": "Southern African traditions often emphasize rest, warmth, and traditional herbs. Belly binding is practiced in some communities for support — done gently.",
    "north_africa": "In North African traditions, the 40-day rest period is common. Nourishing foods, hydration, and family support play a big role in recovery.",
}

def get_cultural_advice(region: str = "general"):
    if region.lower() in CULTURAL_NOTES:
        return CULTURAL_NOTES[region.lower()]
    return "Across African traditions, rest, family support, and nourishing foods are highly valued during the postpartum period. Combine this with modern medical advice for best results."
CULTURAL_NOTES = {
    "west": "In West Africa, postpartum care often includes special soups (like pepper soup), rest, and support from family. Many mothers are encouraged to eat nutrient-rich foods like yam, plantain, and leafy greens to aid healing and milk supply.",
    "east": "In East Africa, the 'Omugwo' tradition (grandmother support) is common. Warm herbal teas, gentle massage, and community help are valued. Rest and hydration are emphasized.",
    "south": "In Southern Africa, traditions often include belly binding (done gently), warm foods, and rest. Family and community play a big role in supporting the new mother.",
    "north": "In North Africa, the 40-day rest period is important. Nourishing foods, hydration, and family care are central to recovery.",
}

def get_cultural_advice(region: str = "general"):
    key = region.lower()[:4]  # west, east, south, north
    if key in CULTURAL_NOTES:
        return CULTURAL_NOTES[key]
    return "Across many African cultures, the postpartum period is honored with rest, family support, and nourishing foods. Listen to your body and combine tradition with medical advice."
