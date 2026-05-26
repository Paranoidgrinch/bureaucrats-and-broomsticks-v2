from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.systems.encounters import choose_random_encounter


FORM_STAGE_ENCOUNTERS = {
    "city_easy_form_01",
    "city_easy_form_02",
    "city_easy_form_03",
}

FORM_STAGE_ENEMIES = {
    "unsigned_form_ghost",
    "margin_note_gnawer",
    "misfiled_page",
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


def test_form_stage_easy_encounters_are_single_enemy_paperwork_introductions() -> None:
    catalog = load_default_content_catalog()

    form_encounters = [
        encounter
        for encounter in catalog.encounter_database.values()
        if (
            encounter.act == 1
            and encounter.difficulty == "easy"
            and "stage_form" in encounter.tags
        )
    ]

    assert FORM_STAGE_ENCOUNTERS <= {encounter.id for encounter in form_encounters}
    assert len(form_encounters) >= 3

    for encounter in form_encounters:
        assert len(encounter.enemies) == 1
        enemy = catalog.enemy_database[encounter.enemies[0]]
        assert _enemy_applies_paperwork_to_player(enemy), encounter.id


def test_form_stage_enemies_are_loaded_and_tagged_for_form() -> None:
    catalog = load_default_content_catalog()

    assert FORM_STAGE_ENEMIES <= set(catalog.enemy_database)

    for enemy_id in FORM_STAGE_ENEMIES:
        enemy = catalog.enemy_database[enemy_id]
        assert "city" in enemy.tags
        assert "stage_form" in enemy.tags
        assert _enemy_applies_paperwork_to_player(enemy)


def test_stage_form_easy_selection_uses_only_form_tagged_encounters() -> None:
    catalog = load_default_content_catalog()

    for seed in range(20):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="easy",
            stage="form",
        )
        assert "stage_form" in encounter.tags
        assert encounter.id in {
            encounter_id
            for encounter_id, encounter_definition in catalog.encounter_database.items()
            if (
                encounter_definition.act == 1
                and encounter_definition.difficulty == "easy"
                and "stage_form" in encounter_definition.tags
            )
        }
