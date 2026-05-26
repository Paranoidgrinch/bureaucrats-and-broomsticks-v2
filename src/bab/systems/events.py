from random import Random

from bab.models import EventDefinition, EventType


def _stage_tag(stage: str) -> str:
    return f"stage_{stage}"


def choose_random_event(
    event_database: dict[str, EventDefinition],
    rng: Random,
    *,
    act: int | None = None,
    event_type: EventType | None = None,
    stage: str | None = None,
    excluded_event_ids: set[str] | None = None,
) -> EventDefinition:
    events = list(event_database.values())

    if act is not None:
        events = [
            event
            for event in events
            if event.act == act
        ]

    if event_type is not None:
        events = [
            event
            for event in events
            if event.event_type == event_type
        ]

    if excluded_event_ids:
        non_excluded_events = [
            event
            for event in events
            if event.id not in excluded_event_ids
        ]
        if non_excluded_events:
            events = non_excluded_events

    if stage is not None:
        tagged_events = [
            event
            for event in events
            if _stage_tag(stage) in event.tags
        ]
        if tagged_events:
            events = tagged_events

    if not events:
        raise ValueError("No events available for the requested filters.")

    weights = [event.weight for event in events]
    return rng.choices(events, weights=weights, k=1)[0]
