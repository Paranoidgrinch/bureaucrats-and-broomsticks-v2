from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.systems.encounters import choose_random_encounter


ORDINANCE_STAGE_ENCOUNTERS = {
    "city_normal_ordinance_01",
    "city_normal_ordinance_02",
    "city_normal_ordinance_03",
}

ORDINANCE_STAGE_ENEMIES = {
    "ordinance_tablet",
    "bylaw_gargoyle",
    "street_law_writ",
}


def _enemy_applies_doubt_to_player(enemy) -> bool:
    for intent in enemy.intents:
        for action in intent.actions:
            if (
                action.type == "apply_status"
                and action.target == "player"
                and action.status == "doubt"
                and action.amount >= 1
            ):
                return True
    return False


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


def test_ordinance_stage_normal_encounters_are_civic_law_pressure() -> None:
    catalog = load_default_content_catalog()

    ordinance_encounters = [
        encounter
        for encounter in catalog.encounter_database.values()
        if (
            encounter.act == 1
            and encounter.difficulty == "normal"
            and "stage_ordinance" in encounter.tags
        )
    ]

    assert ORDINANCE_STAGE_ENCOUNTERS <= {
        encounter.id
        for encounter in ordinance_encounters
    }
    assert len(ordinance_encounters) >= 3

    for encounter in ordinance_encounters:
        enemies = [
            catalog.enemy_database[enemy_id]
            for enemy_id in encounter.enemies
        ]
        assert any(_enemy_applies_doubt_to_player(enemy) for enemy in enemies), encounter.id
        assert any(_enemy_gains_block(enemy) for enemy in enemies), encounter.id


def test_ordinance_stage_enemies_are_loaded_and_tagged_for_ordinance() -> None:
    catalog = load_default_content_catalog()

    assert ORDINANCE_STAGE_ENEMIES <= set(catalog.enemy_database)

    for enemy_id in ORDINANCE_STAGE_ENEMIES:
        enemy = catalog.enemy_database[enemy_id]
        assert "city" in enemy.tags
        assert "stage_ordinance" in enemy.tags
        assert _enemy_applies_doubt_to_player(enemy)
        assert _enemy_gains_block(enemy)


def test_stage_ordinance_normal_selection_uses_only_ordinance_tagged_encounters() -> None:
    catalog = load_default_content_catalog()

    for seed in range(20):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="normal",
            stage="ordinance",
        )
        assert "stage_ordinance" in encounter.tags
        assert encounter.id in {
            encounter_id
            for encounter_id, encounter_definition in catalog.encounter_database.items()
            if (
                encounter_definition.act == 1
                and encounter_definition.difficulty == "normal"
                and "stage_ordinance" in encounter_definition.tags
            )
        }
