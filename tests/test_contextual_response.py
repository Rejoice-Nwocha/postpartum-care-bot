from app.contextual_response import contextual_response


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
