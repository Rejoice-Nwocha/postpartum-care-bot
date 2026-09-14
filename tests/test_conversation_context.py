from app.conversation_context import extract_days, is_affirmative, is_negative, recovery_stage


def test_extract_numeric_days():
    assert extract_days("7 days now") == 7
    assert extract_days("I am 14 days postpartum") == 14


def test_extract_word_days():
    assert extract_days("seven days") == 7


def test_yes_no_helpers():
    assert is_affirmative("yes")
    assert is_negative("no")


def test_recovery_stage():
    assert recovery_stage(7) == "early recovery"
    assert recovery_stage(28) == "healing recovery"
    assert recovery_stage(60) == "ongoing recovery"
