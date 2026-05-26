from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.systems.encounters import choose_random_encounter


SEAL_STAGE_ENCOUNTERS = {
    "city_normal_seal_01",
    "city_normal_seal_02",
    "city_normal_seal_03",
}

SEAL_STAGE_ENEMIES = {
    "wax_notary",
    "red_ribbon_serpent",
    "seal_witness",
}


def _enemy_applies_paperwork_to_player(enemy) -> bool:
    for intent in enemy.intents:
        for action in intent.actions:
            if (
                action.type == "apply_status"
                and action.target == "player"
                and action.status == "paperwork"
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


def test_seal_stage_normal_encounters_are_certification_pressure() -> None:
    catalog = load_default_content_catalog()

    seal_encounters = [
        encounter
        for encounter in catalog.encounter_database.values()
        if (
            encounter.act == 1
            and encounter.difficulty == "normal"
            and "stage_seal" in encounter.tags
        )
    ]

    assert SEAL_STAGE_ENCOUNTERS <= {encounter.id for encounter in seal_encounters}
    assert len(seal_encounters) >= 3

    for encounter in seal_encounters:
        enemies = [
            catalog.enemy_database[enemy_id]
            for enemy_id in encounter.enemies
        ]
        assert any(_enemy_applies_paperwork_to_player(enemy) for enemy in enemies), encounter.id
        assert any(_enemy_gains_block(enemy) for enemy in enemies), encounter.id


def test_seal_stage_enemies_are_loaded_and_tagged_for_seal() -> None:
    catalog = load_default_content_catalog()

    assert SEAL_STAGE_ENEMIES <= set(catalog.enemy_database)

    for enemy_id in SEAL_STAGE_ENEMIES:
        enemy = catalog.enemy_database[enemy_id]
        assert "city" in enemy.tags
        assert "stage_seal" in enemy.tags
        assert _enemy_applies_paperwork_to_player(enemy)
        assert _enemy_gains_block(enemy)


def test_stage_seal_normal_selection_uses_only_seal_tagged_encounters() -> None:
    catalog = load_default_content_catalog()

    for seed in range(20):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="normal",
            stage="seal",
        )
        assert "stage_seal" in encounter.tags
        assert encounter.id in {
            encounter_id
            for encounter_id, encounter_definition in catalog.encounter_database.items()
            if (
                encounter_definition.act == 1
                and encounter_definition.difficulty == "normal"
                and "stage_seal" in encounter_definition.tags
            )
        }
