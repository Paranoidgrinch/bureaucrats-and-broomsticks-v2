from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.systems.encounters import choose_random_encounter


ENFORCEMENT_STAGE_ENCOUNTERS = {
    "city_normal_enforcement_01",
    "city_normal_enforcement_02",
    "city_normal_enforcement_03",
}

ENFORCEMENT_STAGE_ENEMIES = {
    "warrant_bailiff",
    "levy_constable",
    "gatehouse_enforcer",
}


def _enemy_gains_block(enemy) -> bool:
    for intent in enemy.intents:
        for action in intent.actions:
            if (
                action.type == "gain_block"
                and action.target == "owner"
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


def test_enforcement_stage_normal_encounters_are_civic_force_pressure() -> None:
    catalog = load_default_content_catalog()

    enforcement_encounters = [
        encounter
        for encounter in catalog.encounter_database.values()
        if (
            encounter.act == 1
            and encounter.difficulty == "normal"
            and "stage_enforcement" in encounter.tags
        )
    ]

    assert ENFORCEMENT_STAGE_ENCOUNTERS <= {
        encounter.id
        for encounter in enforcement_encounters
    }
    assert len(enforcement_encounters) >= 3

    for encounter in enforcement_encounters:
        enemies = [
            catalog.enemy_database[enemy_id]
            for enemy_id in encounter.enemies
        ]
        assert any(_enemy_gains_block(enemy) for enemy in enemies), encounter.id
        assert any(_enemy_gains_strength(enemy) for enemy in enemies), encounter.id


def test_enforcement_stage_enemies_are_loaded_and_tagged_for_enforcement() -> None:
    catalog = load_default_content_catalog()

    assert ENFORCEMENT_STAGE_ENEMIES <= set(catalog.enemy_database)

    for enemy_id in ENFORCEMENT_STAGE_ENEMIES:
        enemy = catalog.enemy_database[enemy_id]
        assert "city" in enemy.tags
        assert "stage_enforcement" in enemy.tags
        assert _enemy_gains_block(enemy)
        assert _enemy_gains_strength(enemy)


def test_stage_enforcement_normal_selection_uses_only_enforcement_tagged_encounters() -> None:
    catalog = load_default_content_catalog()

    for seed in range(20):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="normal",
            stage="enforcement",
        )
        assert "stage_enforcement" in encounter.tags
        assert encounter.id in {
            encounter_id
            for encounter_id, encounter_definition in catalog.encounter_database.items()
            if (
                encounter_definition.act == 1
                and encounter_definition.difficulty == "normal"
                and "stage_enforcement" in encounter_definition.tags
            )
        }
