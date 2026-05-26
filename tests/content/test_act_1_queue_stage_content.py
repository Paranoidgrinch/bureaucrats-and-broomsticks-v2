from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.systems.encounters import choose_random_encounter


QUEUE_STAGE_ENCOUNTERS = {
    "city_easy_01",
    "city_easy_04",
    "city_easy_queue_01",
    "city_easy_queue_02",
}

QUEUE_STAGE_ENEMIES = {
    "queue_imp",
    "pigeon_courier",
    "number_ticket_wisp",
    "line_cutter_familiar",
}


def _enemy_applies_panic_to_player(enemy) -> bool:
    for intent in enemy.intents:
        for action in intent.actions:
            if (
                action.type == "apply_status"
                and action.target == "player"
                and action.status == "panic"
                and action.amount >= 1
            ):
                return True
    return False


def test_queue_stage_easy_encounters_are_single_enemy_panic_introductions() -> None:
    catalog = load_default_content_catalog()

    queue_encounters = [
        encounter
        for encounter in catalog.encounter_database.values()
        if (
            encounter.act == 1
            and encounter.difficulty == "easy"
            and "stage_queue" in encounter.tags
        )
    ]

    assert QUEUE_STAGE_ENCOUNTERS <= {encounter.id for encounter in queue_encounters}
    assert len(queue_encounters) >= 4

    for encounter in queue_encounters:
        assert len(encounter.enemies) == 1
        enemy = catalog.enemy_database[encounter.enemies[0]]
        assert _enemy_applies_panic_to_player(enemy), encounter.id


def test_queue_stage_enemies_are_loaded_and_tagged_for_queue() -> None:
    catalog = load_default_content_catalog()

    assert QUEUE_STAGE_ENEMIES <= set(catalog.enemy_database)

    for enemy_id in QUEUE_STAGE_ENEMIES:
        enemy = catalog.enemy_database[enemy_id]
        assert "city" in enemy.tags
        assert _enemy_applies_panic_to_player(enemy)


def test_stage_queue_easy_selection_uses_only_queue_tagged_encounters() -> None:
    catalog = load_default_content_catalog()

    for seed in range(20):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="easy",
            stage="queue",
        )
        assert "stage_queue" in encounter.tags
        assert encounter.id in QUEUE_STAGE_ENCOUNTERS
