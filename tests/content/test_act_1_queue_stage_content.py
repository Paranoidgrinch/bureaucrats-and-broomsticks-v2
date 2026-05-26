from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.systems.encounters import choose_random_encounter


QUEUE_STAGE_ENCOUNTERS = {
    "city_easy_01",
    "city_easy_04",
    "city_easy_queue_01",
    "city_easy_queue_02",
    "city_easy_queue_03",
    "city_easy_queue_04",
    "city_easy_queue_05",
    "city_easy_queue_06",
}

QUEUE_STAGE_ENEMIES = {
    "queue_imp",
    "number_ticket_wisp",
    "line_cutter_weasel",
    "pigeon_courier",
    "velvet_rope_mimic",
    "closing_bell_sprite",
    "waiting_room_gnawer",
    "queue_crier_homunculus",
}

EXPECTED_QUEUE_HP = {
    "queue_imp": 22,
    "number_ticket_wisp": 22,
    "line_cutter_weasel": 20,
    "pigeon_courier": 19,
    "velvet_rope_mimic": 22,
    "closing_bell_sprite": 19,
    "waiting_room_gnawer": 19,
    "queue_crier_homunculus": 25,
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


def _enemy_damage_amounts(enemy) -> list[int]:
    amounts = []
    for intent in enemy.intents:
        for action in intent.actions:
            if action.type == "deal_damage" and action.target == "player":
                amounts.append(action.amount)
    return amounts


def test_queue_stage_has_eight_single_enemy_panic_introductions() -> None:
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

    assert {encounter.id for encounter in queue_encounters} == QUEUE_STAGE_ENCOUNTERS

    for encounter in queue_encounters:
        assert len(encounter.enemies) == 1
        enemy = catalog.enemy_database[encounter.enemies[0]]
        assert enemy.id in QUEUE_STAGE_ENEMIES
        assert _enemy_applies_panic_to_player(enemy), encounter.id


def test_queue_stage_enemies_have_requested_hp_and_tags() -> None:
    catalog = load_default_content_catalog()

    assert QUEUE_STAGE_ENEMIES <= set(catalog.enemy_database)
    assert "line_cutter_familiar" not in catalog.enemy_database

    for enemy_id, expected_hp in EXPECTED_QUEUE_HP.items():
        enemy = catalog.enemy_database[enemy_id]
        assert enemy.max_hp == expected_hp
        assert "city" in enemy.tags
        assert "stage_queue" in enemy.tags
        assert "panic_intro" in enemy.tags
        assert _enemy_applies_panic_to_player(enemy)


def test_queue_stage_requested_damage_values_are_represented() -> None:
    catalog = load_default_content_catalog()

    assert 12 in _enemy_damage_amounts(catalog.enemy_database["line_cutter_weasel"])
    assert 9 in _enemy_damage_amounts(catalog.enemy_database["velvet_rope_mimic"])
    assert 8 in _enemy_damage_amounts(catalog.enemy_database["queue_imp"])
    assert 8 in _enemy_damage_amounts(catalog.enemy_database["number_ticket_wisp"])
    assert 8 in _enemy_damage_amounts(catalog.enemy_database["closing_bell_sprite"])
    assert 8 in _enemy_damage_amounts(catalog.enemy_database["waiting_room_gnawer"])


def test_queue_crier_homunculus_repeats_monotone_rebuke() -> None:
    catalog = load_default_content_catalog()
    enemy = catalog.enemy_database["queue_crier_homunculus"]

    assert [intent.name for intent in enemy.intents].count("Monotone Rebuke") == 2


def test_stage_queue_easy_selection_uses_only_queue_tagged_encounters() -> None:
    catalog = load_default_content_catalog()

    for seed in range(40):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="easy",
            stage="queue",
        )
        assert "stage_queue" in encounter.tags
        assert encounter.id in QUEUE_STAGE_ENCOUNTERS
