from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.systems.encounters import choose_random_encounter


COUNTER_STAGE_ENCOUNTERS = {
    "city_easy_counter_01",
    "city_easy_counter_02",
    "city_easy_counter_03",
    "city_easy_counter_04",
    "city_easy_counter_05",
    "city_easy_counter_06",
    "city_easy_counter_07",
    "city_easy_counter_08",
}

COUNTER_STAGE_ENEMIES = {
    "wrong_window_scribe",
    "jurisdiction_snail",
    "jurisdictional_clerkling",
    "counter_of_denial_lesser",
    "blue_slip_sprite",
    "counter_bell_toad",
    "receipt_eyed_clerk",
    "triplicate_examiner",
}

EXPECTED_COUNTER_HP = {
    "wrong_window_scribe": 25,
    "jurisdiction_snail": 30,
    "jurisdictional_clerkling": 19,
    "counter_of_denial_lesser": 27,
    "blue_slip_sprite": 23,
    "counter_bell_toad": 30,
    "receipt_eyed_clerk": 24,
    "triplicate_examiner": 33,
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


def _enemy_damage_amounts(enemy) -> list[int]:
    amounts = []
    for intent in enemy.intents:
        for action in intent.actions:
            if action.type == "deal_damage" and action.target == "player":
                amounts.append(action.amount)
    return amounts


def _enemy_block_amounts(enemy) -> list[int]:
    amounts = []
    for intent in enemy.intents:
        for action in intent.actions:
            if action.type == "gain_block" and action.target == "owner":
                amounts.append(action.amount)
    return amounts


def test_counter_stage_has_eight_single_enemy_doubt_introductions() -> None:
    catalog = load_default_content_catalog()

    counter_encounters = [
        encounter
        for encounter in catalog.encounter_database.values()
        if (
            encounter.act == 1
            and encounter.difficulty == "easy"
            and "stage_counter" in encounter.tags
        )
    ]

    assert {encounter.id for encounter in counter_encounters} == COUNTER_STAGE_ENCOUNTERS

    for encounter in counter_encounters:
        assert len(encounter.enemies) == 1
        enemy = catalog.enemy_database[encounter.enemies[0]]
        assert enemy.id in COUNTER_STAGE_ENEMIES
        assert _enemy_applies_doubt_to_player(enemy), encounter.id


def test_counter_stage_enemies_have_requested_hp_and_tags() -> None:
    catalog = load_default_content_catalog()

    assert COUNTER_STAGE_ENEMIES <= set(catalog.enemy_database)

    for enemy_id, expected_hp in EXPECTED_COUNTER_HP.items():
        enemy = catalog.enemy_database[enemy_id]
        assert enemy.max_hp == expected_hp
        assert "city" in enemy.tags
        assert "stage_counter" in enemy.tags
        assert "doubt_intro" in enemy.tags
        assert _enemy_applies_doubt_to_player(enemy)


def test_counter_stage_requested_damage_and_block_values_are_represented() -> None:
    catalog = load_default_content_catalog()

    assert 12 in _enemy_damage_amounts(catalog.enemy_database["wrong_window_scribe"])
    assert 12 in _enemy_block_amounts(catalog.enemy_database["jurisdiction_snail"])
    assert _enemy_damage_amounts(catalog.enemy_database["jurisdictional_clerkling"]).count(6) >= 2
    assert 10 in _enemy_damage_amounts(catalog.enemy_database["counter_of_denial_lesser"])
    assert 6 in _enemy_damage_amounts(catalog.enemy_database["blue_slip_sprite"])
    assert 6 in _enemy_block_amounts(catalog.enemy_database["blue_slip_sprite"])
    assert 12 in _enemy_damage_amounts(catalog.enemy_database["counter_bell_toad"])
    assert 13 in _enemy_damage_amounts(catalog.enemy_database["receipt_eyed_clerk"])
    assert _enemy_damage_amounts(catalog.enemy_database["triplicate_examiner"]).count(3) >= 4


def test_counter_clerkling_has_paper_cuts_multi_hit() -> None:
    catalog = load_default_content_catalog()
    enemy = catalog.enemy_database["jurisdictional_clerkling"]
    paper_cuts = next(intent for intent in enemy.intents if intent.name == "Paper Cuts")

    assert [
        action.amount
        for action in paper_cuts.actions
        if action.type == "deal_damage"
    ] == [6, 6]


def test_triplicate_examiner_has_triplicate_multi_hit() -> None:
    catalog = load_default_content_catalog()
    enemy = catalog.enemy_database["triplicate_examiner"]
    discrepancy = next(intent for intent in enemy.intents if intent.name == "Stamp Discrepancy")

    assert [
        action.amount
        for action in discrepancy.actions
        if action.type == "deal_damage"
    ] == [3, 3, 3]


def test_stage_counter_easy_selection_uses_only_counter_tagged_encounters() -> None:
    catalog = load_default_content_catalog()

    for seed in range(40):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="easy",
            stage="counter",
        )
        assert "stage_counter" in encounter.tags
        assert encounter.id in COUNTER_STAGE_ENCOUNTERS
