import pytest

from app.topic_router import match_topic_route


@pytest.mark.parametrize(
    "message,topic",
    [
        ("My recovery", "recovery"),
        ("My emotions", "emotions"),
        ("My body", "body"),
        ("Breastfeeding", "breastfeeding"),
        ("My baby", "baby"),
        ("Food & hydration", "nutrition"),
        ("Sleep & rest", "sleep"),
        ("Cultural practices", "cultural"),
        ("I just want to talk", "talking"),
        ("Physical recovery", "physical_recovery"),
        ("C-section recovery", "csection"),
        ("Vaginal birth recovery", "physical_recovery"),
        ("Traditional & cultural care", "cultural"),
    ],
)
def test_broad_topic_routes_do_not_inherit_stale_topics(message, topic):
    route = match_topic_route(message)
    assert route is not None
    assert route.topic == topic
    assert route.follow_up
    assert route.response


def test_cultural_practices_is_not_sleep():
    route = match_topic_route("Cultural practices")
    assert route is not None
    assert route.topic == "cultural"
    assert "traditional" in route.follow_up.lower()


def test_unknown_sentence_is_not_forced_into_a_broad_topic():
    assert match_topic_route("I feel strange today") is None
