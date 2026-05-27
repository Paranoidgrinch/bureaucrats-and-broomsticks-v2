"""Shared non-interactive event effect helpers."""

from __future__ import annotations

from math import ceil

from bab.models import Card, EventEffect
from bab.run.state import RunState


def effect_amount(effect: EventEffect, default: int = 1) -> int:
    return default if effect.amount is None else effect.amount


def apply_event_lose_hp(run_state: RunState, effect: EventEffect) -> int:
    """Lose flat HP, clamped so an event cannot directly kill the player."""

    loss = max(0, effect_amount(effect, default=0))
    old_hp = run_state.current_hp
    run_state.current_hp = max(1, run_state.current_hp - loss)
    return old_hp - run_state.current_hp


def apply_event_gain_gold(run_state: RunState, effect: EventEffect) -> int:
    amount = max(0, effect_amount(effect, default=0))
    run_state.gold += amount
    return amount


def apply_event_lose_gold(run_state: RunState, effect: EventEffect) -> int:
    loss = max(0, effect_amount(effect, default=0))
    old_gold = run_state.gold
    run_state.gold = max(0, run_state.gold - loss)
    return old_gold - run_state.gold


def apply_event_heal_percent_max_hp(run_state: RunState, effect: EventEffect) -> int:
    percent = max(0, effect_amount(effect, default=0))
    heal_amount = ceil(run_state.character_class.max_hp * percent / 100)
    old_hp = run_state.current_hp
    run_state.current_hp = min(
        run_state.character_class.max_hp,
        run_state.current_hp + heal_amount,
    )
    return run_state.current_hp - old_hp


def cards_added_by_event(effect: EventEffect) -> int:
    return max(1, effect_amount(effect, default=1))


def card_for_event_effect(
    run_state: RunState,
    effect: EventEffect,
) -> Card:
    if effect.card_id is None:
        raise ValueError("add_card_to_deck event effect requires card_id.")

    try:
        return run_state.card_database[effect.card_id]
    except KeyError as exc:
        raise ValueError(
            f"add_card_to_deck references unknown card_id: {effect.card_id}"
        ) from exc


def apply_event_add_card_to_deck(
    run_state: RunState,
    effect: EventEffect,
) -> list[Card]:
    card = card_for_event_effect(run_state, effect)
    count = cards_added_by_event(effect)

    added_cards = [
        card
        for _ in range(count)
    ]
    run_state.run_deck.extend(added_cards)
    return added_cards
