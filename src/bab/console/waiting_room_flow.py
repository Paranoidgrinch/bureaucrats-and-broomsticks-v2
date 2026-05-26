"""Console waiting-room flow."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from rich.panel import Panel
from rich.table import Table

from bab.console.io import console
from bab.console.reward_flow import offer_card_upgrade
from bab.run.state import RunState, complete_current_map_node


@dataclass(frozen=True)
class WaitingRoomCopy:
    title: str
    description: str
    table_title: str
    productive_choice: str
    productive_effect: str
    nap_choice: str
    heal_effect: str
    prompt: str
    nap_result_template: str


def waiting_room_copy_for_stage(
    stage: str | None,
    *,
    heal_percent: int,
) -> WaitingRoomCopy:
    if stage == "final_office":
        return WaitingRoomCopy(
            title="Final Office",
            description=(
                "The last bench waits outside the Commissioner's door. "
                "Every stamped paper in the building seems to be listening."
            ),
            table_title="Final Office Choices",
            productive_choice="Review one last document.",
            productive_effect="Upgrade one card before the final door.",
            nap_choice="Rest on the hard bench.",
            heal_effect=f"Heal {heal_percent}% of max HP.",
            prompt="[bold yellow]Choose a Final Office option: [/bold yellow]",
            nap_result_template=(
                "[green]You rest before the final office and recover {healed} HP. "
                "Current HP: {current_hp}/{max_hp}.[/green]"
            ),
        )

    return WaitingRoomCopy(
        title="Waiting Room",
        description=(
            "The Waiting Room smells faintly of dust, old coffee, "
            "and postponed decisions."
        ),
        table_title="Waiting Room Choices",
        productive_choice="Do something productive.",
        productive_effect="Upgrade one card.",
        nap_choice="Take a Nap.",
        heal_effect=f"Heal {heal_percent}% of max HP.",
        prompt="[bold yellow]Choose a Waiting Room option: [/bold yellow]",
        nap_result_template=(
            "[green]You take a nap and recover {healed} HP. "
            "Current HP: {current_hp}/{max_hp}.[/green]"
        ),
    )


def resolve_waiting_room_node(run_state: RunState) -> None:
    current_node = run_state.current_node()
    stage = current_node.stage if current_node is not None else None
    copy = waiting_room_copy_for_stage(
        stage,
        heal_percent=run_state.waiting_room_heal_percent,
    )

    console.print()
    console.print(
        Panel(
            copy.description,
            title=copy.title,
        )
    )

    table = Table(title=copy.table_title)
    table.add_column("#", justify="right")
    table.add_column("Choice")
    table.add_column("Effect")
    table.add_row(
        "0",
        copy.productive_choice,
        copy.productive_effect,
    )
    table.add_row(
        "1",
        copy.nap_choice,
        copy.heal_effect,
    )
    console.print(table)

    while True:
        command = console.input(copy.prompt).strip().lower()

        if command == "0":
            offer_card_upgrade(run_state)
            break

        if command == "1":
            heal_amount = ceil(
                run_state.character_class.max_hp
                * run_state.waiting_room_heal_percent
                / 100
            )
            old_hp = run_state.current_hp
            run_state.current_hp = min(
                run_state.character_class.max_hp,
                run_state.current_hp + heal_amount,
            )
            healed = run_state.current_hp - old_hp
            console.print(
                copy.nap_result_template.format(
                    healed=healed,
                    current_hp=run_state.current_hp,
                    max_hp=run_state.character_class.max_hp,
                )
            )
            break

        console.print("[red]Invalid Waiting Room choice.[/red]")

    complete_current_map_node(run_state)
