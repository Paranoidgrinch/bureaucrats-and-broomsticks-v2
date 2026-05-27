from random import Random

import pytest

from bab.content.catalog import load_default_content_catalog
from bab.console.run_flow import create_run_state
from bab.models import EventEffect
from bab.systems.event_effects import (
    apply_event_duplicate_card,
    apply_event_transform_card,
)


def make_run_state():
    catalog = load_default_content_catalog()
    return create_run_state(catalog=catalog, rng=Random(1))


def make_effect(effect_type: str, **kwargs) -> EventEffect:
    return EventEffect.model_validate(
        {
            "type": effect_type,
            **kwargs,
        }
    )


def test_duplicate_card_adds_copy_of_existing_deck_card() -> None:
    run_state = make_run_state()
    old_size = len(run_state.run_deck)

    duplicated = apply_event_duplicate_card(
        run_state,
        make_effect("duplicate_card", card_id=run_state.run_deck[0].id),
    )

    assert len(duplicated) == 1
    assert duplicated[0].id == run_state.run_deck[0].id
    assert len(run_state.run_deck) == old_size + 1
    assert run_state.run_deck[-1].id == duplicated[0].id


def test_duplicate_card_can_duplicate_multiple_times() -> None:
    run_state = make_run_state()
    old_size = len(run_state.run_deck)
    target_id = run_state.run_deck[0].id

    duplicated = apply_event_duplicate_card(
        run_state,
        make_effect("duplicate_card", amount=2, card_id=target_id),
    )

    assert len(duplicated) == 2
    assert len(run_state.run_deck) == old_size + 2
    assert all(card.id == target_id for card in duplicated)


def test_duplicate_card_rejects_empty_filter() -> None:
    run_state = make_run_state()

    with pytest.raises(ValueError, match="No cards available to duplicate"):
        apply_event_duplicate_card(
            run_state,
            make_effect("duplicate_card", card_id="not_in_deck"),
        )


def test_transform_card_removes_matching_card_and_adds_reward_card() -> None:
    run_state = make_run_state()
    old_size = len(run_state.run_deck)
    target_id = run_state.run_deck[0].id
    old_count = sum(card.id == target_id for card in run_state.run_deck)

    removed, replacement = apply_event_transform_card(
        run_state,
        make_effect("transform_card", card_id=target_id),
    )

    new_count = sum(card.id == target_id for card in run_state.run_deck)

    assert removed.id == target_id
    assert replacement in run_state.run_deck
    assert len(run_state.run_deck) == old_size
    assert new_count == old_count - 1


def test_duplicate_and_transform_card_respect_real_tag_filter() -> None:
    run_state = make_run_state()
    tagged_card = next(
        (card for card in run_state.run_deck if card.tags),
        None,
    )

    assert tagged_card is not None, "Starting deck should contain at least one tagged card."
    tag = tagged_card.tags[0]

    duplicated = apply_event_duplicate_card(
        run_state,
        make_effect("duplicate_card", tag=tag),
    )
    assert tag in duplicated[0].tags

    removed, replacement = apply_event_transform_card(
        run_state,
        make_effect("transform_card", tag=tag),
    )

    assert tag in removed.tags
    assert replacement in run_state.run_deck


def test_transform_card_rejects_empty_filter() -> None:
    run_state = make_run_state()

    with pytest.raises(ValueError, match="No removable cards available"):
        apply_event_transform_card(
            run_state,
            make_effect("transform_card", card_id="not_in_deck"),
        )
