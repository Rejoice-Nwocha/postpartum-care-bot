"""ACHOT Care Sister knowledge and conversation layer.

This module is intentionally conservative: it provides education and supportive
self-care guidance, while routing possible danger signs to the existing triage
layer instead of attempting diagnosis or treatment.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class BrainResponse:
    text: str
    follow_up: str = ""


INTENTS = {
    "lochia": ["lochia", "postpartum bleeding", "bleeding after birth", "discharge after birth", "vaginal discharge"],
    "bleeding": ["bleeding", "blood", "clots", "pad", "soaking pad"],
    "pain": ["pain", "sore", "soreness", "cramp", "cramps", "after pains", "stomach pain", "back pain"],
    "perineum": ["tear", "stitches", "episiotomy", "perineum", "bottom hurts", "vagina hurts"],
    "csection": ["c section", "c-section", "cesarean", "caesarean", "c section wound", "incision", "scar"],
    "breastfeeding": ["breastfeeding", "breast feed", "latch", "latching", "milk supply", "breast milk", "baby won't latch"],
    "breast": ["breast pain", "engorged", "engorgement", "nipple", "blocked duct", "mastitis"],
    "sleep": ["sleep", "sleeping", "tired", "exhausted", "fatigue", "no sleep"],
    "nutrition": ["food", "eat", "eating", "nutrition", "hungry", "appetite", "water", "hydration"],
    "constipation": ["constipation", "constipated", "hard stool", "poop", "bowel"],
    "urination": ["pee", "urine", "urinating", "pissing", "bladder", "burning when i pee"],
    "mood": ["sad", "crying", "cry", "overwhelmed", "emotional", "mood", "baby blues", "postpartum depression", "depressed"],
    "anxiety": ["anxious", "anxiety", "panic", "worried", "scared", "fear", "racing thoughts"],
    "trauma": ["trauma", "traumatic birth", "bad birth", "birth experience", "flashback", "nightmare"],
    "body": ["body", "belly", "stomach still big", "weight", "stretch marks", "changes"],
    "sex": ["sex", "intercourse", "dry", "dryness", "pain during sex", "intimacy"],
    "contraception": ["contraception", "birth control", "family planning", "prevent pregnancy"],
    "baby_feeding": ["baby feeding", "baby feeds", "formula", "how often baby eats", "wet diaper", "dirty diaper"],
    "baby_sleep": ["baby sleeping", "newborn sleep", "baby won't sleep", "baby cries", "crying baby"],
    "baby_jaundice": ["jaundice", "yellow baby", "yellow eyes"],
    "cord": ["umbilical", "cord", "belly button"],
    "hope": ["i can't do this", "i feel like a bad mother", "bad mother", "failing", "i am failing", "not coping", "overwhelmed"],
    "greeting": ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"],
}

RESPONSES = {
    "lochia": BrainResponse(
        "Mama, lochia is the vaginal discharge that happens after birth while your uterus heals. It is a normal part of postpartum recovery, and it can change in colour and amount as the days pass. Your body has been through something enormous, so seeing changes can feel unfamiliar, but you don't have to face them without understanding them.\n\nWhat matters is how much you are bleeding, whether it is changing over time, and whether you have other symptoms such as severe pain, fever, dizziness or feeling very unwell.",
        "How many days has it been since you gave birth, and what does the bleeding or discharge look like right now?"
    ),
    "pain": BrainResponse(
        "Some cramping, soreness and body aches can happen while the body recovers from birth. You deserve comfort while you heal, and pain that is severe, worsening, or accompanied by other concerning symptoms should not simply be pushed through.\n\nTry to give your body permission to rest, keep hydrated, and follow the pain-care plan given by your healthcare team. You do not have to prove that you are strong by suffering in silence.",
        "Where is the pain, how severe is it, and when did it start?"
    ),
    "perineum": BrainResponse(
        "If you had a vaginal birth, the tissues around the perineum can feel sore, swollen or tender, especially after a tear or stitches. Healing takes time. Gentle hygiene, comfortable positioning and following the care instructions from your maternity team can help you protect the area while it heals.\n\nIf the pain is getting worse rather than better, or you notice fever, worsening swelling, foul-smelling discharge or feel very unwell, please contact a healthcare professional promptly.",
        "Did you have a tear or stitches, and how many days postpartum are you?"
    ),
    "csection": BrainResponse(
        "After a C-section, it is normal for the abdomen and incision area to feel tender while the tissues heal. Recovery is real recovery—you have had major abdominal surgery as well as given birth, so please be gentle with yourself. Avoid putting pressure on the wound and follow the instructions from your maternity team about wound care and activity.\n\nIncreasing pain, fever, worsening redness or swelling, pus or other concerning changes around the wound need medical review.",
        "How many days has it been since your C-section, and what are you noticing around the wound?"
    ),
    "breastfeeding": BrainResponse(
        "Breastfeeding can take practice. You and your baby are learning each other, and difficulty with feeding does not mean you are failing. Positioning, attachment and responsive feeding are important, and getting hands-on support from a midwife, nurse or lactation professional can make a big difference.\n\nIf feeding is painful, your baby is struggling to feed, or you are worried about whether your baby is getting enough, let's look at what is happening rather than blaming yourself.",
        "Is the main difficulty the latch, pain, milk supply, or your baby's feeding pattern?"
    ),
    "breast": BrainResponse(
        "Breast fullness and tenderness can happen as milk production changes after birth. Supportive feeding, good positioning and attachment, and expressing milk when appropriate can help. Warm or cold compresses may also be comfortable depending on what feels better for you.\n\nA breast that becomes increasingly painful, red or hot, especially with fever or feeling unwell, needs medical attention.",
        "Is the breast mainly full and uncomfortable, or is there a painful/red area or fever?"
    ),
    "sleep": BrainResponse(
        "Mama, exhaustion after birth is not a character flaw. Your body is recovering while you are caring for a newborn whose needs do not follow a normal sleep schedule. If you can, accept practical help with meals, chores and baby care so you can get protected periods of rest.\n\nYou do not have to be productive right now. Recovery is productive too.",
        "Are you getting any opportunity to rest, and is the exhaustion making it hard to function or care for yourself?"
    ),
    "nutrition": BrainResponse(
        "Your body needs nourishment while it heals. Aim for regular meals or small nourishing meals when appetite is low, enough fluids, and a variety of foods that work for your culture, budget and healthcare needs. If your clinician prescribed supplements such as iron or folate, take them as directed.\n\nThere is no single perfect postpartum food. ACHOT is about helping you recover in a way that is practical, culturally respectful and safe.",
        "Are you struggling more with appetite, getting enough fluids, or knowing what foods will support recovery?"
    ),
    "constipation": BrainResponse(
        "Constipation can be uncomfortable after birth, especially when you are sore or worried about using the toilet. Fluids, gentle movement as tolerated, and fibre-rich foods can support normal bowel function. If you were prescribed a stool softener or other medicine, follow your clinician's instructions.\n\nSevere abdominal pain, persistent vomiting, inability to pass stool or gas, or significant worsening symptoms need medical advice.",
        "When was your last comfortable bowel movement, and are you having significant pain?"
    ),
    "urination": BrainResponse(
        "Urination can feel different after birth, especially after a vaginal birth, stitches or a catheter. Burning, difficulty passing urine, inability to empty your bladder, or worsening urinary symptoms should be discussed with a healthcare professional because infection or other problems may need assessment.",
        "Are you having burning, difficulty passing urine, leaking, or feeling that your bladder is not emptying?"
    ),
    "mood": BrainResponse(
        "Mama, your emotional world can feel very different after birth. Crying, feeling overwhelmed or having changing emotions can happen during the adjustment to life with a newborn, but you deserve support rather than being told to simply 'be strong.'\n\nIf low mood, hopelessness, anxiety or feeling unlike yourself is persistent, worsening or making it difficult to function, please talk to a healthcare professional. Getting help is not failing your baby—it is caring for both of you.",
        "How have you been feeling emotionally over the last few days, and do you feel supported by someone you trust?"
    ),
    "anxiety": BrainResponse(
        "Postpartum anxiety can feel intense—your mind may stay on alert, especially when you are responsible for a newborn. You are not weak for feeling anxious. Try to share what you are carrying with someone you trust and give yourself small moments to breathe, eat and rest.\n\nIf anxiety is persistent, overwhelming, stopping you from sleeping or functioning, or feels unsafe, please seek professional support.",
        "What has your mind been most worried about lately?"
    ),
    "trauma": BrainResponse(
        "Mama, a birth can be physically safe and still feel emotionally difficult. If your birth experience left you frightened, distressed, numb or stuck replaying what happened, those feelings deserve care. You do not have to minimise them because your baby arrived safely.\n\nTalking with a trusted healthcare professional or mental-health professional can help you process what happened at your own pace.",
        "Would you like to tell me what part of the birth experience is staying with you most?"
    ),
    "body": BrainResponse(
        "Your body may feel unfamiliar after pregnancy and birth. Your abdomen, breasts, pelvic area, skin, energy and appetite can all feel different while recovery is underway. None of that means your body has failed you.\n\nACHOT's goal is not to rush you back to an old version of yourself. It is to help you understand your changing body, care for it and rebuild strength safely over time.",
        "Which change in your body are you finding hardest to understand right now?"
    ),
    "sex": BrainResponse(
        "There is no need to rush intimacy after birth. Comfort, healing, bleeding, stitches or a C-section, dryness, emotions and your own readiness all matter. If sex is painful, you do not need to push through it—talk with your healthcare professional about what you are experiencing.",
        "Is your question mainly about when to resume sex, pain, dryness, or feeling emotionally ready?"
    ),
    "contraception": BrainResponse(
        "Fertility can return before a first postpartum period, so postpartum family planning is worth discussing even while you are breastfeeding. The best option depends on your health, feeding plans, preferences and when you may want another pregnancy. A clinician can help you choose safely.",
        "Would you like information about postpartum contraception options to discuss with your healthcare provider?"
    ),
    "baby_feeding": BrainResponse(
        "Feeding a newborn can be one of the biggest learning curves of the early days. Babies need frequent feeds, and patterns can vary. What matters is whether your baby is feeding effectively and showing signs of adequate intake. If feeding is difficult or your baby is unusually sleepy and hard to feed, seek professional assessment.",
        "Is your concern breastfeeding, formula feeding, how often baby feeds, or whether baby is getting enough?"
    ),
    "baby_sleep": BrainResponse(
        "Newborn sleep can be unpredictable. Your baby may wake frequently because their needs are small and frequent. You are not doing something wrong because your newborn does not sleep like an older child.\n\nIf your baby is unusually difficult to wake, is feeding poorly, has breathing difficulty, fever or another concerning change, seek medical care promptly.",
        "How old is your baby, and what is worrying you most about the sleep or crying?"
    ),
    "baby_jaundice": BrainResponse(
        "Yellowing of a newborn's skin or eyes can be jaundice. Some newborn jaundice is common, but it still deserves appropriate assessment because the baby's age, feeding and level of yellowing matter. Please contact your baby's healthcare provider for guidance rather than trying to judge severity from colour alone.",
        "How old is your baby, and when did you first notice the yellowing?"
    ),
    "cord": BrainResponse(
        "The umbilical cord stump needs to be kept clean and protected while it dries and separates. Follow the cord-care instructions given by your maternity or newborn-care team. Increasing redness around the skin, swelling, pus, foul smell, fever or a baby who seems unwell needs prompt medical assessment.",
        "What are you noticing around the cord—drying normally, redness, discharge or bleeding?"
    ),
    "hope": BrainResponse(
        "Mama, pause with me for a moment. You are learning how to live in a completely new chapter, and struggling does not mean you are a bad mother. You do not have to solve everything today.\n\nLet's make the next step very small: tell me what feels heaviest right now. We can take it one piece at a time. And if you are feeling unsafe or having thoughts of harming yourself or someone else, please tell a trusted person and seek urgent professional help now—you deserve immediate support.",
        "What feels heaviest right now: your body, your emotions, the baby, your relationship, or simply being exhausted?"
    ),
}


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower().strip())


def detect_intent(text: str) -> str | None:
    value = _normalise(text)
    if not value:
        return None

    # More specific topics should win over generic terms such as "pain" or "blood".
    ordered = [
        "lochia", "baby_jaundice", "hope", "trauma", "csection", "perineum",
        "breastfeeding", "breast", "contraception", "baby_feeding", "baby_sleep",
        "cord", "anxiety", "mood", "constipation", "urination", "nutrition",
        "sleep", "sex", "body", "pain", "bleeding", "greeting",
    ]
    for intent in ordered:
        for phrase in INTENTS[intent]:
            if phrase in value:
                return intent
    return None


def answer_postpartum_question(text: str) -> BrainResponse | None:
    intent = detect_intent(text)
    if intent == "greeting":
        return BrainResponse(
            "Hello Mama. I'm here with you. You can ask me anything about your recovery, your emotions, breastfeeding, your baby, sleep, nutrition, or changes in your body. There is no silly question here."
        )
    return RESPONSES.get(intent) if intent else None
