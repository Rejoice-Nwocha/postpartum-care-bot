from app.clinical_rules import clinical_response


def test_heavy_bleeding_with_dizziness_is_critical():
    result = clinical_response("I am having very heavy bleeding and I feel dizzy")
    assert result is not None
    assert result.level == "CRITICAL"


def test_breathing_symptoms_are_critical():
    result = clinical_response("I have difficulty breathing")
    assert result is not None
    assert result.level == "CRITICAL"


def test_foul_discharge_with_fever_needs_prompt_assessment():
    result = clinical_response("my postpartum discharge has a foul smell and I have a fever")
    assert result is not None
    assert result.level == "MEDIUM"
    assert "medical assessment" in result.response.lower()


def test_wound_change_with_fever_needs_assessment():
    result = clinical_response("my c section wound is red and painful and I have a fever")
    assert result is not None
    assert result.level == "MEDIUM"


def test_breast_symptoms_with_fever_need_assessment():
    result = clinical_response("my breast is red and painful and I have a fever")
    assert result is not None
    assert result.level == "MEDIUM"


def test_normal_question_has_no_clinical_override():
    result = clinical_response("what is lochia?")
    assert result is None
