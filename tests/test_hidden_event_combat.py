from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.console.run_flow import create_run_state
from bab.run.state import (
    create_combat_state_for_hidden_event_node,
    event_node_triggers_hidden_combat,
)


def _first_event_node(run_state):
    return next(
        node
        for node in run_state.run_map.nodes.values()
        if node.node_type == "event"
    )


def test_hidden_event_combat_chance_does_not_change_visible_event_node_type() -> None:
    catalog = load_default_content_catalog()
    run_state = create_run_state(catalog=catalog, rng=Random(1))
    run_state.event_combat_chance = 1.0
    node = _first_event_node(run_state)

    assert node.node_type == "event"
    assert event_node_triggers_hidden_combat(run_state, node)
    assert node.node_type == "event"


def test_hidden_event_combat_uses_event_stage_and_depth_difficulty() -> None:
    catalog = load_default_content_catalog()
    run_state = create_run_state(catalog=catalog, rng=Random(3))
    node = _first_event_node(run_state)

    combat_state = create_combat_state_for_hidden_event_node(run_state, node)
    encounter = run_state.encounter_database[combat_state.encounter_id]

    assert f"stage_{node.stage}" in encounter.tags
    if node.depth <= 3:
        assert encounter.difficulty == "easy"
    else:
        assert encounter.difficulty == "normal"


def test_hidden_event_combat_can_be_forced_off() -> None:
    catalog = load_default_content_catalog()
    run_state = create_run_state(catalog=catalog, rng=Random(1))
    run_state.event_combat_chance = 0.0
    node = _first_event_node(run_state)

    assert not event_node_triggers_hidden_combat(run_state, node)
