from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.console.run_flow import create_run_state
from bab.models import EventEffect
from bab.run.state import (
    apply_next_combat_modifiers,
    create_combat_state_for_next_encounter,
    enter_map_node,
)
from bab.systems.event_effects import (
    apply_event_next_combat_card_reward_bonus,
    apply_event_next_combat_enemy_hp_loss_percent,
    apply_event_next_combat_enemy_strength,
    apply_event_next_combat_player_fatigue,
    apply_event_next_combat_player_panic,
    apply_event_next_combat_player_strength,
)


def make_run_state():
    catalog = load_default_content_catalog()
    return create_run_state(catalog=catalog, rng=Random(1))


def make_effect(effect_type: str, amount: int) -> EventEffect:
    return EventEffect.model_validate(
        {
            "type": effect_type,
            "amount": amount,
        }
    )


def enter_first_combat(run_state) -> None:
    enter_map_node(run_state, run_state.run_map.start_node_ids[0])


def test_next_combat_player_status_modifiers_are_applied_and_consumed() -> None:
    run_state = make_run_state()
    apply_event_next_combat_player_strength(
        run_state,
        make_effect("next_combat_player_strength", 2),
    )
    apply_event_next_combat_player_panic(
        run_state,
        make_effect("next_combat_player_panic", 3),
    )
    apply_event_next_combat_player_fatigue(
        run_state,
        make_effect("next_combat_player_fatigue", 1),
    )

    enter_first_combat(run_state)
    combat_state = create_combat_state_for_next_encounter(run_state)

    assert combat_state.player.get_status_amount("strength") == 2
    assert combat_state.player.get_status_amount("panic") == 3
    assert combat_state.player.get_status_amount("fatigue") == 1
    assert run_state.next_combat_player_strength == 0
    assert run_state.next_combat_player_panic == 0
    assert run_state.next_combat_player_fatigue == 0


def test_next_combat_enemy_modifiers_are_applied_and_consumed() -> None:
    run_state = make_run_state()
    apply_event_next_combat_enemy_strength(
        run_state,
        make_effect("next_combat_enemy_strength", 5),
    )
    apply_event_next_combat_enemy_hp_loss_percent(
        run_state,
        make_effect("next_combat_enemy_hp_loss_percent", 25),
    )

    enter_first_combat(run_state)
    combat_state = create_combat_state_for_next_encounter(run_state)

    for enemy in combat_state.enemies:
        assert enemy.get_status_amount("strength") == 5
        assert enemy.hp <= enemy.max_hp
        assert enemy.hp == max(1, round(enemy.max_hp * 0.75)) or enemy.hp == max(1, enemy.max_hp * 75 // 100)

    assert run_state.next_combat_enemy_strength == 0
    assert run_state.next_combat_enemy_hp_loss_percent == 0


def test_enemy_hp_loss_percent_is_clamped_to_leave_enemies_alive() -> None:
    run_state = make_run_state()
    apply_event_next_combat_enemy_hp_loss_percent(
        run_state,
        make_effect("next_combat_enemy_hp_loss_percent", 500),
    )

    enter_first_combat(run_state)
    combat_state = create_combat_state_for_next_encounter(run_state)

    assert all(enemy.hp >= 1 for enemy in combat_state.enemies)
    assert run_state.next_combat_enemy_hp_loss_percent == 0


def test_next_combat_card_reward_bonus_moves_to_pending_bonus() -> None:
    run_state = make_run_state()
    apply_event_next_combat_card_reward_bonus(
        run_state,
        make_effect("next_combat_card_reward_bonus", 1),
    )

    enter_first_combat(run_state)
    create_combat_state_for_next_encounter(run_state)

    assert run_state.next_combat_card_reward_bonus == 0
    assert run_state.pending_card_reward_bonus_choices == 1


def test_apply_next_combat_modifiers_can_be_called_without_modifiers() -> None:
    run_state = make_run_state()
    enter_first_combat(run_state)
    combat_state = create_combat_state_for_next_encounter(run_state)

    apply_next_combat_modifiers(run_state, combat_state)

    assert combat_state.player.get_status_amount("strength") == 0
