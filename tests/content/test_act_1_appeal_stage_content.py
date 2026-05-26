from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.systems.encounters import choose_random_encounter


APPEAL_STAGE_ENCOUNTERS = {
    "city_normal_appeal_01",
    "city_normal_appeal_02",
    "city_normal_appeal_03",
}

APPEAL_STAGE_ENEMIES = {
    "appeals_clerk",
    "objection_sprite",
    "procedural_advocate",
}


def _enemy_applies_doubt_or_paperwork_to_player(enemy) -> bool:
    for intent in enemy.intents:
        for action in intent.actions:
            if (
                action.type == "apply_status"
                and action.target == "player"
                and action.status in {"doubt", "paperwork"}
                and action.amount >= 1
            ):
                return True
    return False


def _enemy_gains_strength(enemy) -> bool:
    for intent in enemy.intents:
        for action in intent.actions:
            if (
                action.type == "gain_strength"
                and action.target == "owner"
                and action.amount >= 1
            ):
                return True
    return False


def test_appeal_stage_normal_encounters_are_escalating_procedures() -> None:
    catalog = load_default_content_catalog()

    appeal_encounters = [
        encounter
        for encounter in catalog.encounter_database.values()
        if (
            encounter.act == 1
            and encounter.difficulty == "normal"
            and "stage_appeal" in encounter.tags
        )
    ]

    assert APPEAL_STAGE_ENCOUNTERS <= {
        encounter.id
        for encounter in appeal_encounters
    }
    assert len(appeal_encounters) >= 3

    for encounter in appeal_encounters:
        enemies = [
            catalog.enemy_database[enemy_id]
            for enemy_id in encounter.enemies
        ]
        assert any(
            _enemy_applies_doubt_or_paperwork_to_player(enemy)
            for enemy in enemies
        ), encounter.id
        assert any(_enemy_gains_strength(enemy) for enemy in enemies), encounter.id


def test_appeal_stage_enemies_are_loaded_and_tagged_for_appeal() -> None:
    catalog = load_default_content_catalog()

    assert APPEAL_STAGE_ENEMIES <= set(catalog.enemy_database)

    for enemy_id in APPEAL_STAGE_ENEMIES:
        enemy = catalog.enemy_database[enemy_id]
        assert "city" in enemy.tags
        assert "stage_appeal" in enemy.tags
        assert _enemy_applies_doubt_or_paperwork_to_player(enemy)
        assert _enemy_gains_strength(enemy)


def test_stage_appeal_normal_selection_uses_only_appeal_tagged_encounters() -> None:
    catalog = load_default_content_catalog()

    for seed in range(20):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="normal",
            stage="appeal",
        )
        assert "stage_appeal" in encounter.tags
        assert encounter.id in {
            encounter_id
            for encounter_id, encounter_definition in catalog.encounter_database.items()
            if (
                encounter_definition.act == 1
                and encounter_definition.difficulty == "normal"
                and "stage_appeal" in encounter_definition.tags
            )
        }
