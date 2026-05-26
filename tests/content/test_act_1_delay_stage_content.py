from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.systems.encounters import choose_random_encounter


DELAY_STAGE_ENCOUNTERS = {
    "city_normal_delay_01",
    "city_normal_delay_02",
    "city_normal_delay_03",
}

DELAY_STAGE_ENEMIES = {
    "closing_bell_specter",
    "waiting_bench_gremlin",
    "public_hours_clerk",
}


def _enemy_applies_fatigue_to_player(enemy) -> bool:
    for intent in enemy.intents:
        for action in intent.actions:
            if (
                action.type == "apply_status"
                and action.target == "player"
                and action.status == "fatigue"
                and action.amount >= 1
            ):
                return True
    return False


def test_delay_stage_normal_encounters_are_fatigue_introductions() -> None:
    catalog = load_default_content_catalog()

    delay_encounters = [
        encounter
        for encounter in catalog.encounter_database.values()
        if (
            encounter.act == 1
            and encounter.difficulty == "normal"
            and "stage_delay" in encounter.tags
        )
    ]

    assert DELAY_STAGE_ENCOUNTERS <= {
        encounter.id
        for encounter in delay_encounters
    }
    assert len(delay_encounters) >= 3

    for encounter in delay_encounters:
        enemies = [
            catalog.enemy_database[enemy_id]
            for enemy_id in encounter.enemies
        ]
        assert any(_enemy_applies_fatigue_to_player(enemy) for enemy in enemies), encounter.id


def test_delay_stage_enemies_are_loaded_and_tagged_for_delay() -> None:
    catalog = load_default_content_catalog()

    assert DELAY_STAGE_ENEMIES <= set(catalog.enemy_database)

    for enemy_id in DELAY_STAGE_ENEMIES:
        enemy = catalog.enemy_database[enemy_id]
        assert "city" in enemy.tags
        assert "stage_delay" in enemy.tags
        assert _enemy_applies_fatigue_to_player(enemy)


def test_stage_delay_normal_selection_uses_only_delay_tagged_encounters() -> None:
    catalog = load_default_content_catalog()

    for seed in range(20):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="normal",
            stage="delay",
        )
        assert "stage_delay" in encounter.tags
        assert encounter.id in {
            encounter_id
            for encounter_id, encounter_definition in catalog.encounter_database.items()
            if (
                encounter_definition.act == 1
                and encounter_definition.difficulty == "normal"
                and "stage_delay" in encounter_definition.tags
            )
        }
