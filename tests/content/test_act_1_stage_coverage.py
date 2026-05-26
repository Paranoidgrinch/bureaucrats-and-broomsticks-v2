from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.run.map import STAGED_PILGRIMAGE_STAGES, generate_staged_pilgrimage_map
from bab.systems.encounters import choose_random_encounter


EXPECTED_STAGE_SEQUENCE = {
    1: "queue",
    2: "counter",
    3: "form",
    4: "seal",
    5: "ordinance",
    6: "delay",
    7: "appeal",
    8: "enforcement",
    9: "final_office",
}

STAGE_COMBAT_EXPECTATIONS = {
    "queue": {
        "difficulty": "easy",
        "required_statuses": {"panic"},
        "required_actions": set(),
    },
    "counter": {
        "difficulty": "easy",
        "required_statuses": {"doubt"},
        "required_actions": set(),
    },
    "form": {
        "difficulty": "easy",
        "required_statuses": {"paperwork"},
        "required_actions": set(),
    },
    "seal": {
        "difficulty": "normal",
        "required_statuses": {"paperwork"},
        "required_actions": {"gain_block"},
    },
    "ordinance": {
        "difficulty": "normal",
        "required_statuses": {"doubt"},
        "required_actions": {"gain_block"},
    },
    "delay": {
        "difficulty": "normal",
        "required_statuses": {"fatigue"},
        "required_actions": set(),
    },
    "appeal": {
        "difficulty": "normal",
        "required_statuses": set(),
        "any_statuses": {"doubt", "paperwork"},
        "required_actions": {"gain_strength"},
    },
    "enforcement": {
        "difficulty": "normal",
        "required_statuses": set(),
        "required_actions": {"gain_block", "gain_strength"},
    },
}

EXPECTED_BOSS_MECHANIC_TAGS = {
    "boss_fatigue",
    "boss_panic",
    "boss_block",
    "boss_strength",
    "boss_paperwork",
}


def _enemy_applies_status(enemy, status_id: str) -> bool:
    for intent in enemy.intents:
        for action in intent.actions:
            if (
                action.type == "apply_status"
                and action.target == "player"
                and action.status == status_id
                and action.amount >= 1
            ):
                return True
    return False


def _enemy_has_action(enemy, action_type: str) -> bool:
    for intent in enemy.intents:
        for action in intent.actions:
            if action.type == action_type:
                return True
    return False


def _encounter_enemies(catalog, encounter):
    return [
        catalog.enemy_database[enemy_id]
        for enemy_id in encounter.enemies
    ]


def _encounter_applies_status(catalog, encounter, status_id: str) -> bool:
    return any(
        _enemy_applies_status(enemy, status_id)
        for enemy in _encounter_enemies(catalog, encounter)
    )


def _encounter_has_action(catalog, encounter, action_type: str) -> bool:
    return any(
        _enemy_has_action(enemy, action_type)
        for enemy in _encounter_enemies(catalog, encounter)
    )


def test_act_1_staged_pilgrimage_sequence_is_the_design_contract() -> None:
    assert STAGED_PILGRIMAGE_STAGES == EXPECTED_STAGE_SEQUENCE


def test_act_1_staged_pilgrimage_generated_maps_keep_stage_contract() -> None:
    for seed in range(50):
        run_map = generate_staged_pilgrimage_map(
            Random(seed),
            act=1,
            steps_before_boss=9,
            width=4,
            max_events=3,
            max_treasures=1,
            max_elites=2,
        )

        for depth, expected_stage in EXPECTED_STAGE_SEQUENCE.items():
            nodes_at_depth = [
                node
                for node in run_map.nodes.values()
                if node.depth == depth
            ]
            assert nodes_at_depth
            assert {node.stage for node in nodes_at_depth} == {expected_stage}

        non_boss_nodes = [
            node
            for node in run_map.nodes.values()
            if node.node_type != "boss"
        ]
        assert sum(node.node_type == "event" for node in non_boss_nodes) <= 3
        assert sum(node.node_type == "treasure" for node in non_boss_nodes) <= 1
        assert sum(node.node_type == "elite" for node in non_boss_nodes) <= 2

        final_office_nodes = [
            node
            for node in non_boss_nodes
            if node.stage == "final_office"
        ]
        assert final_office_nodes
        assert {node.node_type for node in final_office_nodes} == {"waiting_room"}
        assert all(
            node.next_node_ids == (run_map.boss_node_id,)
            for node in final_office_nodes
        )

        boss_node = run_map.get_node(run_map.boss_node_id)
        assert boss_node.node_type == "boss"
        assert boss_node.stage == "commissioner"


def test_act_1_each_combat_stage_has_matching_tagged_encounter_pool() -> None:
    catalog = load_default_content_catalog()

    for stage, expectation in STAGE_COMBAT_EXPECTATIONS.items():
        stage_tag = f"stage_{stage}"
        difficulty = expectation["difficulty"]

        stage_encounters = [
            encounter
            for encounter in catalog.encounter_database.values()
            if (
                encounter.act == 1
                and encounter.difficulty == difficulty
                and stage_tag in encounter.tags
            )
        ]

        assert len(stage_encounters) >= 3, stage

        for encounter in stage_encounters:
            for status_id in expectation.get("required_statuses", set()):
                assert _encounter_applies_status(catalog, encounter, status_id), (
                    stage,
                    encounter.id,
                    status_id,
                )

            any_statuses = expectation.get("any_statuses", set())
            if any_statuses:
                assert any(
                    _encounter_applies_status(catalog, encounter, status_id)
                    for status_id in any_statuses
                ), (stage, encounter.id, any_statuses)

            for action_type in expectation.get("required_actions", set()):
                assert _encounter_has_action(catalog, encounter, action_type), (
                    stage,
                    encounter.id,
                    action_type,
                )


def test_act_1_stage_aware_selection_can_resolve_each_combat_stage() -> None:
    catalog = load_default_content_catalog()

    for stage, expectation in STAGE_COMBAT_EXPECTATIONS.items():
        stage_tag = f"stage_{stage}"
        difficulty = expectation["difficulty"]

        for seed in range(20):
            encounter = choose_random_encounter(
                catalog.encounter_database,
                Random(seed),
                act=1,
                difficulty=difficulty,
                stage=stage,
            )

            assert stage_tag in encounter.tags
            assert encounter.difficulty == difficulty


def test_act_1_boss_pool_covers_all_major_boss_mechanic_identities() -> None:
    catalog = load_default_content_catalog()

    boss_enemies = [
        catalog.enemy_database[encounter.enemies[0]]
        for encounter in catalog.encounter_database.values()
        if encounter.act == 1 and encounter.difficulty == "boss"
    ]

    mechanic_tags = {
        tag
        for enemy in boss_enemies
        for tag in enemy.tags
        if tag.startswith("boss_")
    }

    assert EXPECTED_BOSS_MECHANIC_TAGS <= mechanic_tags

    living_charter = catalog.enemy_database["living_charter"]
    assert "boss_doubt" in living_charter.tags
    assert _enemy_applies_status(living_charter, "doubt")
