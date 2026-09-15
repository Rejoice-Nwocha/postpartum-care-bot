from app.contextual_response import contextual_response
from app.postpartum_brain import answer_postpartum_question, detect_intent


def test_explicit_bleeding_topic_overrides_stale_mood_topic():
    result = contextual_response(
        "my bleeding has been getting heavier today",
        current_topic="mood",
        postpartum_days=5,
    )
    assert result is not None
    assert "heavier postpartum bleeding" in result.text.lower()


def test_short_bleeding_followup_stays_on_bleeding_thread():
    result = contextual_response(
        "it was lighter yesterday",
        current_topic="bleeding",
        pending_question="Has the amount increased suddenly, or has it been gradually getting heavier?",
        postpartum_days=5,
    )
    assert result is not None
    assert "yesterday" in result.text.lower()
    assert "bleeding" in result.text.lower()


def test_unrelated_explicit_topic_can_replace_old_topic():
    result = contextual_response(
        "my breasts hurt",
        current_topic="mood",
        postpartum_days=5,
    )
    assert result is None


def test_cultural_request_does_not_inherit_stale_sleep_topic():
    assert detect_intent("cultural practices") == "cultural"
    result = answer_postpartum_question("cultural practices")
    assert result is not None
    assert "cultural" in result.text.lower()
    assert "sleep" not in result.text.lower()


def test_menu_category_phrases_are_recognised():
    assert detect_intent("my emotions") == "mood"
    assert detect_intent("my baby") == "baby"
    assert detect_intent("my recovery") == "recovery"
    assert detect_intent("cultural care") == "cultural"
