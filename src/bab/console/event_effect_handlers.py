"""Console event effect handler registry."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from math import ceil

from bab.console.io import console
from bab.console.reward_flow import (
    offer_card_removal,
    offer_card_reward,
    offer_card_upgrade,
)
from bab.console.shop_flow import open_shop
from bab.models import EventEffect
from bab.run.state import RunState
from bab.systems.event_effects import (
    apply_event_add_card_to_deck,
    apply_event_transform_card,
    apply_event_duplicate_card,
    apply_event_gain_gold,
    apply_event_gain_relic,
    apply_event_heal_percent_max_hp,
    apply_event_lose_gold,
    apply_event_lose_hp,
)

ConsoleEventEffectHandler = Callable[[RunState, EventEffect], None]


def apply_event_effect(run_state: RunState, effect: EventEffect) -> None:
    handler = CONSOLE_EVENT_EFFECT_HANDLERS.get(effect.type)
    if handler is None:
        console.print(f"[yellow]Unhandled event effect: {effect.type}.[/yellow]")
        return
    handler(run_state, effect)


def handle_none(run_state: RunState, effect: EventEffect) -> None:
    return


def handle_gain_card_reward(run_state: RunState, effect: EventEffect) -> None:
    amount = effect.amount or 1
    for _ in range(amount):
        offer_card_reward(run_state)


def handle_upgrade_card(run_state: RunState, effect: EventEffect) -> None:
    amount = effect.amount or 1
    for _ in range(amount):
        offer_card_upgrade(run_state)


def handle_lose_percent_max_hp(run_state: RunState, effect: EventEffect) -> None:
    percent = effect.amount or 0
    loss = ceil(run_state.character_class.max_hp * percent / 100)
    run_state.current_hp = max(1, run_state.current_hp - loss)
    console.print(
        f"[red]Lost {loss} HP. Current HP: "
        f"{run_state.current_hp}/{run_state.character_class.max_hp}.[/red]"
    )


def handle_lose_hp(run_state: RunState, effect: EventEffect) -> None:
    loss = apply_event_lose_hp(run_state, effect)
    console.print(
        f"[red]Lost {loss} HP. Current HP: "
        f"{run_state.current_hp}/{run_state.character_class.max_hp}.[/red]"
    )


def handle_gain_gold(run_state: RunState, effect: EventEffect) -> None:
    amount = apply_event_gain_gold(run_state, effect)
    console.print(f"[yellow]Gained {amount} gold. Gold: {run_state.gold}.[/yellow]")


def handle_lose_gold(run_state: RunState, effect: EventEffect) -> None:
    loss = apply_event_lose_gold(run_state, effect)
    console.print(f"[yellow]Lost {loss} gold. Gold: {run_state.gold}.[/yellow]")


def handle_heal_percent_max_hp(run_state: RunState, effect: EventEffect) -> None:
    healed = apply_event_heal_percent_max_hp(run_state, effect)
    console.print(
        f"[green]Recovered {healed} HP. Current HP: "
        f"{run_state.current_hp}/{run_state.character_class.max_hp}.[/green]"
    )


def handle_add_card_to_deck(run_state: RunState, effect: EventEffect) -> None:
    added_cards = apply_event_add_card_to_deck(run_state, effect)
    for card in added_cards:
        console.print(f"[yellow]Added {card.name} to your deck.[/yellow]")




def handle_duplicate_card(run_state: RunState, effect: EventEffect) -> None:
    duplicated_cards = apply_event_duplicate_card(run_state, effect)
    for card in duplicated_cards:
        console.print(f"[green]Duplicated {card.name}.[/green]")


def handle_transform_card(run_state: RunState, effect: EventEffect) -> None:
    removed_card, replacement = apply_event_transform_card(run_state, effect)
    console.print(
        f"[green]Transformed {removed_card.name} into {replacement.name}.[/green]"
    )


def handle_gain_relic(run_state: RunState, effect: EventEffect) -> None:
    relic = apply_event_gain_relic(run_state, effect)
    console.print(f"[magenta]Gained relic: {relic.name}.[/magenta]")


def handle_gain_max_hp(run_state: RunState, effect: EventEffect) -> None:
    console.print("[yellow]Max HP events are not implemented yet.[/yellow]")


def handle_remove_card(run_state: RunState, effect: EventEffect) -> None:
    amount = effect.amount or 1
    for _ in range(amount):
        offer_card_removal(
            run_state,
            card_id=effect.card_id,
            tag=effect.tag,
        )


def handle_open_shop(run_state: RunState, effect: EventEffect) -> None:
    open_shop(run_state)


CONSOLE_EVENT_EFFECT_HANDLERS: Mapping[str, ConsoleEventEffectHandler] = {
    "none": handle_none,
    "gain_card_reward": handle_gain_card_reward,
    "upgrade_card": handle_upgrade_card,
    "lose_percent_max_hp": handle_lose_percent_max_hp,
    "lose_hp": handle_lose_hp,
    "gain_gold": handle_gain_gold,
    "lose_gold": handle_lose_gold,
    "heal_percent_max_hp": handle_heal_percent_max_hp,
    "add_card_to_deck": handle_add_card_to_deck,
    "gain_relic": handle_gain_relic,
    "duplicate_card": handle_duplicate_card,
    "transform_card": handle_transform_card,
    "gain_max_hp": handle_gain_max_hp,
    "remove_card": handle_remove_card,
    "open_shop": handle_open_shop,
}
