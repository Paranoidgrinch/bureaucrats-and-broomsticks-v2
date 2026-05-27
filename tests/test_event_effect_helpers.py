from random import Random

import pytest

from bab.content.catalog import load_default_content_catalog
from bab.console.run_flow import create_run_state
from bab.models import EventEffect
from bab.systems.event_effects import (
    apply_event_add_card_to_deck,
    apply_event_gain_gold,
    apply_event_heal_percent_max_hp,
    apply_event_lose_gold,
    apply_event_lose_hp,
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


def test_lose_hp_reduces_current_hp_but_cannot_kill_player() -> None:
    run_state = make_run_state()
    run_state.current_hp = 7

    lost = apply_event_lose_hp(
        run_state,
        make_effect("lose_hp", amount=99),
    )

    assert lost == 6
    assert run_state.current_hp == 1


def test_gain_gold_adds_gold() -> None:
    run_state = make_run_state()
    run_state.gold = 10

    gained = apply_event_gain_gold(
        run_state,
        make_effect("gain_gold", amount=25),
    )

    assert gained == 25
    assert run_state.gold == 35


def test_lose_gold_reduces_gold_but_not_below_zero() -> None:
    run_state = make_run_state()
    run_state.gold = 10

    lost = apply_event_lose_gold(
        run_state,
        make_effect("lose_gold", amount=25),
    )

    assert lost == 10
    assert run_state.gold == 0


def test_heal_percent_max_hp_heals_to_maximum() -> None:
    run_state = make_run_state()
    run_state.current_hp = 1

    healed = apply_event_heal_percent_max_hp(
        run_state,
        make_effect("heal_percent_max_hp", amount=10),
    )

    assert healed == 7
    assert run_state.current_hp == 8


def test_heal_percent_max_hp_does_not_exceed_max_hp() -> None:
    run_state = make_run_state()
    run_state.current_hp = run_state.character_class.max_hp - 2

    healed = apply_event_heal_percent_max_hp(
        run_state,
        make_effect("heal_percent_max_hp", amount=50),
    )

    assert healed == 2
    assert run_state.current_hp == run_state.character_class.max_hp


def test_add_card_to_deck_adds_one_or_more_existing_cards() -> None:
    run_state = make_run_state()
    old_size = len(run_state.run_deck)

    added = apply_event_add_card_to_deck(
        run_state,
        make_effect("add_card_to_deck", card_id="duplicate_copy", amount=2),
    )

    assert [card.id for card in added] == ["duplicate_copy", "duplicate_copy"]
    assert len(run_state.run_deck) == old_size + 2
    assert [card.id for card in run_state.run_deck[-2:]] == [
        "duplicate_copy",
        "duplicate_copy",
    ]


def test_add_card_to_deck_requires_card_id() -> None:
    run_state = make_run_state()

    with pytest.raises(ValueError, match="requires card_id"):
        apply_event_add_card_to_deck(
            run_state,
            make_effect("add_card_to_deck", amount=1),
        )


def test_add_card_to_deck_rejects_unknown_card_id() -> None:
    run_state = make_run_state()

    with pytest.raises(ValueError, match="unknown card_id"):
        apply_event_add_card_to_deck(
            run_state,
            make_effect("add_card_to_deck", card_id="not_a_real_card"),
        )
