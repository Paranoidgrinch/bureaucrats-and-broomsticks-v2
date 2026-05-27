"""Shared non-interactive event effect helpers."""

from __future__ import annotations

from math import ceil

from bab.models import Card, EventEffect, RelicDefinition
from bab.run.state import RunState
from bab.systems.card_removal import removable_card_indices, remove_card_from_deck
from bab.systems.rewards import choose_card_rewards
from bab.systems.relics import apply_relic_pickup_effects_to_run_state


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



def event_relic_is_allowed(
    relic: RelicDefinition,
    run_state: RunState,
) -> bool:
    """Return whether an event may grant this relic in the current Act-1 pool.

    Event relics are intentionally limited to general act relics loaded by the
    current catalog and relics explicitly allowed for the current class.
    """

    if relic.rarity == "boss":
        return False

    owned_ids = {
        owned_relic.id
        for owned_relic in run_state.relics
    }
    if relic.id in owned_ids:
        return False

    if relic.allowed_classes:
        return run_state.character_class.id in relic.allowed_classes

    return True


def eligible_event_relics(run_state: RunState) -> list[RelicDefinition]:
    return sorted(
        [
            relic
            for relic in run_state.relic_database.values()
            if event_relic_is_allowed(relic, run_state)
        ],
        key=lambda relic: relic.id,
    )


def apply_event_gain_relic(run_state: RunState, effect: EventEffect) -> RelicDefinition:
    pool = eligible_event_relics(run_state)

    if effect.tag is not None:
        pool = [
            relic
            for relic in pool
            if effect.tag in relic.tags
        ]

    if not pool:
        if effect.tag is None:
            raise ValueError("No event-eligible relics available.")
        raise ValueError(
            f"No event-eligible relics available with tag: {effect.tag}"
        )

    relic = run_state.rng.choice(pool)
    run_state.relics.append(relic)
    apply_relic_pickup_effects_to_run_state(run_state, relic)
    return relic



def event_card_indices(run_state: RunState, effect: EventEffect) -> list[int]:
    return [
        index
        for index, card in enumerate(run_state.run_deck)
        if (effect.card_id is None or card.id == effect.card_id)
        and (effect.tag is None or effect.tag in card.tags)
    ]


def event_removable_card_indices(run_state: RunState, effect: EventEffect) -> list[int]:
    return removable_card_indices(
        run_state.run_deck,
        card_id=effect.card_id,
        tag=effect.tag,
    )


def apply_event_duplicate_card(
    run_state: RunState,
    effect: EventEffect,
) -> list[Card]:
    indices = event_card_indices(run_state, effect)
    if not indices:
        raise ValueError("No cards available to duplicate for event effect.")

    count = max(1, effect_amount(effect, default=1))
    duplicated_cards: list[Card] = []

    for _ in range(count):
        deck_index = run_state.rng.choice(indices)
        card = run_state.run_deck[deck_index]
        run_state.run_deck.append(card)
        duplicated_cards.append(card)

    return duplicated_cards


def apply_event_transform_card(
    run_state: RunState,
    effect: EventEffect,
) -> tuple[Card, Card]:
    indices = event_removable_card_indices(run_state, effect)
    if not indices:
        raise ValueError("No removable cards available to transform for event effect.")

    deck_index = run_state.rng.choice(indices)
    removed_card = remove_card_from_deck(run_state.run_deck, deck_index)
    replacement = choose_card_rewards(
        run_state.card_database,
        run_state.rng,
        count=1,
        card_class=run_state.character_class.id,
        act=run_state.act,
    )[0]
    run_state.run_deck.append(replacement)
    return removed_card, replacement



def _positive_event_amount(effect: EventEffect) -> int:
    return max(0, effect_amount(effect, default=0))


def apply_event_next_combat_player_strength(
    run_state: RunState,
    effect: EventEffect,
) -> int:
    amount = _positive_event_amount(effect)
    run_state.next_combat_player_strength += amount
    return amount


def apply_event_next_combat_player_panic(
    run_state: RunState,
    effect: EventEffect,
) -> int:
    amount = _positive_event_amount(effect)
    run_state.next_combat_player_panic += amount
    return amount


def apply_event_next_combat_player_fatigue(
    run_state: RunState,
    effect: EventEffect,
) -> int:
    amount = _positive_event_amount(effect)
    run_state.next_combat_player_fatigue += amount
    return amount


def apply_event_next_combat_enemy_strength(
    run_state: RunState,
    effect: EventEffect,
) -> int:
    amount = _positive_event_amount(effect)
    run_state.next_combat_enemy_strength += amount
    return amount


def apply_event_next_combat_enemy_hp_loss_percent(
    run_state: RunState,
    effect: EventEffect,
) -> int:
    amount = _positive_event_amount(effect)
    run_state.next_combat_enemy_hp_loss_percent += amount
    return amount


def apply_event_next_combat_card_reward_bonus(
    run_state: RunState,
    effect: EventEffect,
) -> int:
    amount = _positive_event_amount(effect)
    run_state.next_combat_card_reward_bonus += amount
    return amount
