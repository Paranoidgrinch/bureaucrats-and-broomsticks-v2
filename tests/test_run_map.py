from random import Random

import pytest

from bab.run.map import (
    RunMap,
    STAGED_PILGRIMAGE_STAGES,
    combat_difficulty_for_depth,
    generate_act_map,
    generate_staged_pilgrimage_map,
)


def test_generate_act_map_creates_variable_start_nodes_and_boss() -> None:
    run_map = generate_act_map(
        Random(1),
        act=1,
        steps_before_boss=9,
        width=4,
    )

    assert isinstance(run_map, RunMap)
    assert run_map.act == 1
    assert 2 <= len(run_map.start_node_ids) <= 4
    assert run_map.boss_node_id == "act_1_boss"

    boss_node = run_map.get_node(run_map.boss_node_id)

    assert boss_node.node_type == "boss"
    assert boss_node.encounter_difficulty == "boss"
    assert boss_node.next_node_ids == ()


def test_generated_map_does_not_need_full_grid() -> None:
    steps_before_boss = 9
    width = 4

    run_map = generate_act_map(
        Random(1),
        act=1,
        steps_before_boss=steps_before_boss,
        width=width,
    )

    maximum_nodes = steps_before_boss * width + 1

    assert len(run_map.nodes) <= maximum_nodes
    assert len(run_map.nodes) > steps_before_boss


def test_every_non_boss_node_points_to_later_nodes() -> None:
    run_map = generate_act_map(
        Random(1),
        act=1,
        steps_before_boss=9,
        width=4,
    )

    for node in run_map.nodes.values():
        if node.node_type == "boss":
            assert node.next_node_ids == ()
            continue

        assert node.next_node_ids

        for next_node_id in node.next_node_ids:
            next_node = run_map.get_node(next_node_id)
            assert next_node.depth > node.depth


def test_available_next_nodes_returns_node_objects() -> None:
    run_map = generate_act_map(
        Random(1),
        act=1,
        steps_before_boss=9,
        width=4,
    )

    start_node = run_map.get_node(run_map.start_node_ids[0])
    next_nodes = run_map.available_next_nodes(start_node.id)

    assert next_nodes
    assert all(next_node.id in start_node.next_node_ids for next_node in next_nodes)


def test_standard_act_map_contains_core_node_types() -> None:
    run_map = generate_act_map(
        Random(1),
        act=1,
        steps_before_boss=9,
        width=4,
    )

    node_types = {
        node.node_type
        for node in run_map.nodes.values()
    }

    assert {
        "combat",
        "event",
        "waiting_room",
        "treasure",
        "boss",
    } <= node_types


def test_standard_act_maps_can_contain_elites_after_early_run() -> None:
    elite_depths = []

    for seed in range(100):
        run_map = generate_act_map(
            Random(seed),
            act=1,
            steps_before_boss=9,
            width=4,
        )

        elite_depths.extend(
            node.depth
            for node in run_map.nodes.values()
            if node.node_type == "elite"
        )

    assert elite_depths
    assert min(elite_depths) >= 6


def test_waiting_rooms_are_not_too_common() -> None:
    run_map = generate_act_map(
        Random(1),
        act=1,
        steps_before_boss=9,
        width=4,
    )

    non_boss_nodes = [
        node
        for node in run_map.nodes.values()
        if node.node_type != "boss"
    ]
    waiting_rooms = [
        node
        for node in non_boss_nodes
        if node.node_type == "waiting_room"
    ]

    assert len(waiting_rooms) <= max(2, len(non_boss_nodes) // 4)


def test_map_allows_splits_and_merges() -> None:
    run_map = generate_act_map(
        Random(2),
        act=1,
        steps_before_boss=9,
        width=4,
    )

    split_nodes = [
        node
        for node in run_map.nodes.values()
        if len(node.next_node_ids) > 1
    ]

    incoming_counts: dict[str, int] = {}

    for node in run_map.nodes.values():
        for next_node_id in node.next_node_ids:
            incoming_counts[next_node_id] = incoming_counts.get(next_node_id, 0) + 1

    merged_nodes = [
        node_id
        for node_id, incoming_count in incoming_counts.items()
        if incoming_count > 1
    ]

    assert split_nodes
    assert merged_nodes


def test_combat_and_special_nodes_have_expected_payloads() -> None:
    run_map = generate_act_map(
        Random(1),
        act=1,
        steps_before_boss=9,
        width=4,
    )

    for node in run_map.nodes.values():
        if node.node_type == "combat":
            assert node.encounter_difficulty in {"easy", "normal"}
            assert node.event_type is None

        if node.node_type == "elite":
            assert node.encounter_difficulty == "elite"
            assert node.event_type is None

        if node.node_type == "boss":
            assert node.encounter_difficulty == "boss"
            assert node.event_type is None

        if node.node_type == "event":
            assert node.encounter_difficulty is None
            assert node.event_type in {"narrative", "risk_reward", "deck"}

        if node.node_type in {"waiting_room", "treasure"}:
            assert node.encounter_difficulty is None
            assert node.event_type is None


def test_staged_pilgrimage_map_assigns_expected_stage_sequence() -> None:
    run_map = generate_staged_pilgrimage_map(
        Random(1),
        act=1,
        steps_before_boss=9,
        width=4,
    )

    for depth, expected_stage in STAGED_PILGRIMAGE_STAGES.items():
        nodes_at_depth = [
            node
            for node in run_map.nodes.values()
            if node.depth == depth
        ]
        assert nodes_at_depth
        assert {node.stage for node in nodes_at_depth} == {expected_stage}

    boss_node = run_map.get_node(run_map.boss_node_id)
    assert boss_node.stage == "commissioner"


def test_staged_pilgrimage_map_respects_global_node_caps() -> None:
    for seed in range(100):
        run_map = generate_staged_pilgrimage_map(
            Random(seed),
            act=1,
            steps_before_boss=9,
            width=4,
            max_events=3,
            max_treasures=1,
            max_elites=2,
        )
        non_boss_nodes = [
            node
            for node in run_map.nodes.values()
            if node.node_type != "boss"
        ]
        assert sum(node.node_type == "event" for node in non_boss_nodes) <= 3
        assert sum(node.node_type == "treasure" for node in non_boss_nodes) <= 1
        assert sum(node.node_type == "elite" for node in non_boss_nodes) <= 2


def test_staged_pilgrimage_final_pre_boss_depth_is_waiting_room() -> None:
    run_map = generate_staged_pilgrimage_map(
        Random(3),
        act=1,
        steps_before_boss=9,
        width=4,
    )

    final_nodes = [
        node
        for node in run_map.nodes.values()
        if node.depth == 9
    ]
    assert final_nodes
    assert {node.node_type for node in final_nodes} == {"waiting_room"}
    assert all(node.next_node_ids == (run_map.boss_node_id,) for node in final_nodes)



def test_staged_pilgrimage_event_nodes_are_not_narrative() -> None:
    for seed in range(100):
        run_map = generate_staged_pilgrimage_map(
            Random(seed),
            act=1,
            steps_before_boss=9,
            width=4,
        )
        event_nodes = [
            node
            for node in run_map.nodes.values()
            if node.node_type == "event"
        ]
        assert all(node.event_type in {"risk_reward", "deck"} for node in event_nodes)



def test_staged_pilgrimage_event_type_distribution_follows_pool_weights() -> None:
    event_type_counts = {
        "risk_reward": 0,
        "deck": 0,
    }

    for seed in range(1500):
        run_map = generate_staged_pilgrimage_map(
            Random(seed),
            act=1,
            steps_before_boss=9,
            width=4,
        )
        for node in run_map.nodes.values():
            if node.node_type == "event":
                assert node.event_type in {"risk_reward", "deck"}
                event_type_counts[node.event_type] += 1

    total_events = sum(event_type_counts.values())
    assert total_events > 0

    risk_reward_ratio = event_type_counts["risk_reward"] / total_events

    assert event_type_counts["risk_reward"] > event_type_counts["deck"]
    assert 0.50 <= risk_reward_ratio <= 0.58


def test_combat_difficulty_for_depth_starts_easy_then_becomes_normal() -> None:
    assert combat_difficulty_for_depth(1, 9) == "easy"
    assert combat_difficulty_for_depth(2, 9) == "easy"
    assert combat_difficulty_for_depth(3, 9) == "easy"
    assert combat_difficulty_for_depth(9, 9) == "normal"


def test_generate_act_map_rejects_invalid_arguments() -> None:
    with pytest.raises(ValueError, match="Act must be at least 1"):
        generate_act_map(Random(1), act=0)

    with pytest.raises(ValueError, match="at least 6 steps"):
        generate_act_map(Random(1), steps_before_boss=5)

    with pytest.raises(ValueError, match="width must be at least 2"):
        generate_act_map(Random(1), width=1)


def test_unknown_node_id_raises_clear_error() -> None:
    run_map = generate_act_map(Random(1))

    with pytest.raises(KeyError, match="Unknown map node id"):
        run_map.get_node("missing_node")