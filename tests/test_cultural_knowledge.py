from app.cultural_knowledge import find_cultural_practice, cultural_response


def test_omugwo_is_recognised():
    practice = find_cultural_practice("Tell me about omugwo")
    assert practice is not None
    assert practice.name.startswith("Omugwo")
    assert "Nigeria" in practice.regions


def test_cultural_response_keeps_clinical_boundary():
    response = cultural_response("Can I do postpartum massage?")
    assert response is not None
    assert "cannot diagnose" in response.lower()
    assert "use caution" in response.lower()


def test_herbal_practice_requires_professional_review():
    practice = find_cultural_practice("Can I take a herbal tea after birth?")
    assert practice is not None
    assert practice.safety_level == "professional review"
