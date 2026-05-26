from random import Random

import pytest

from bab.systems.events import choose_random_event
from bab.models import EventDefinition


def make_event(
    event_id: str,
    *,
    act: int = 1,
    event_type: str = "narrative",
    weight: int = 1,
) -> EventDefinition:
    return EventDefinition.model_validate(
        {
            "id": event_id,
            "name": event_id.replace("_", " ").title(),
            "act": act,
            "event_type": event_type,
            "weight": weight,
            "text": "Test event.",
            "choices": [
                {
                    "id": "test_choice",
                    "text": "Choose the test option.",
                    "result_text": "The test option happens.",
                    "effects": [],
                }
            ],
            "tags": [],
        }
    )


def test_choose_random_event_returns_the_only_available_event() -> None:
    event = make_event("test_event")
    event_database = {
        event.id: event,
    }

    chosen = choose_random_event(event_database, Random(1))

    assert chosen.id == "test_event"


def test_choose_random_event_can_filter_by_act() -> None:
    act_1_event = make_event("act_1_event", act=1)
    act_2_event = make_event("act_2_event", act=2)

    event_database = {
        act_1_event.id: act_1_event,
        act_2_event.id: act_2_event,
    }

    chosen = choose_random_event(
        event_database,
        Random(1),
        act=2,
    )

    assert chosen.id == "act_2_event"


def test_choose_random_event_can_filter_by_event_type() -> None:
    narrative_event = make_event("narrative_event", event_type="narrative")
    deck_event = make_event("deck_event", event_type="deck")

    event_database = {
        narrative_event.id: narrative_event,
        deck_event.id: deck_event,
    }

    chosen = choose_random_event(
        event_database,
        Random(1),
        event_type="deck",
    )

    assert chosen.id == "deck_event"


def test_choose_random_event_can_filter_by_act_and_event_type() -> None:
    wrong_act = make_event("wrong_act", act=2, event_type="deck")
    wrong_type = make_event("wrong_type", act=1, event_type="narrative")
    correct_event = make_event("correct_event", act=1, event_type="deck")

    event_database = {
        wrong_act.id: wrong_act,
        wrong_type.id: wrong_type,
        correct_event.id: correct_event,
    }

    chosen = choose_random_event(
        event_database,
        Random(1),
        act=1,
        event_type="deck",
    )

    assert chosen.id == "correct_event"


def test_choose_random_event_raises_error_for_empty_database() -> None:
    with pytest.raises(ValueError, match="No events available"):
        choose_random_event({}, Random(1))


def test_choose_random_event_raises_error_when_filters_match_nothing() -> None:
    event = make_event("test_event", act=1, event_type="narrative")

    with pytest.raises(ValueError, match="No events available"):
        choose_random_event(
            {event.id: event},
            Random(1),
            act=2,
            event_type="deck",
        )


def test_choose_random_event_prefers_matching_stage_tag() -> None:
    untagged = make_event("untagged_event", event_type="narrative")
    tagged = EventDefinition.model_validate(
        {
            "id": "queue_event",
            "name": "Queue Event",
            "act": 1,
            "event_type": "narrative",
            "weight": 1,
            "text": "A queue forms.",
            "choices": [
                {
                    "id": "wait",
                    "text": "Wait.",
                    "result_text": "You wait.",
                    "effects": [],
                }
            ],
            "tags": ["stage_queue"],
        }
    )
    event_database = {
        untagged.id: untagged,
        tagged.id: tagged,
    }

    chosen = choose_random_event(
        event_database,
        Random(1),
        act=1,
        event_type="narrative",
        stage="queue",
    )

    assert chosen.id == "queue_event"


def test_choose_random_event_falls_back_when_stage_has_no_matches() -> None:
    event = make_event("normal_event", event_type="deck")
    event_database = {
        event.id: event,
    }

    chosen = choose_random_event(
        event_database,
        Random(1),
        act=1,
        event_type="deck",
        stage="queue",
    )

    assert chosen.id == "normal_event"


def test_choose_random_event_respects_excluded_event_ids_when_possible() -> None:
    old_event = make_event("old_event", event_type="narrative")
    new_event = make_event("new_event", event_type="narrative")
    event_database = {
        old_event.id: old_event,
        new_event.id: new_event,
    }

    chosen = choose_random_event(
        event_database,
        Random(1),
        act=1,
        event_type="narrative",
        excluded_event_ids={"old_event"},
    )

    assert chosen.id == "new_event"
