from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.systems.encounters import choose_random_encounter


DELAY_STAGE_ENCOUNTERS = {
    "city_normal_delay_01",
    "city_normal_delay_02",
    "city_normal_delay_03",
    "city_normal_delay_04",
    "city_normal_delay_05",
    "city_normal_delay_06",
    "city_normal_delay_07",
    "city_normal_delay_08",
}

DELAY_STAGE_ENEMIES = {
    "closing_bell_specter",
    "waiting_bench_gremlin",
    "public_hours_clerk",
    "inverted_hourglass",
    "fading_number_token",
    "stationary_queue_marker",
    "minute_moth",
    "stalled_clock_face",
}

RETIRED_FROM_DELAY_ENEMIES = {
    "civic_bell_ringer",
    "receipt_mimic",
    "red_ribbon_serpent",
    "stamp_goblin",
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


def test_delay_stage_normal_encounters_are_exact_fatigue_pressure_pool() -> None:
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

    assert {encounter.id for encounter in delay_encounters} == DELAY_STAGE_ENCOUNTERS

    for encounter in delay_encounters:
        assert RETIRED_FROM_DELAY_ENEMIES.isdisjoint(set(encounter.enemies)), encounter.id

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

    for seed in range(120):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="normal",
            stage="delay",
        )

        assert "stage_delay" in encounter.tags
        assert encounter.id in DELAY_STAGE_ENCOUNTERS


# --- Delay elite pool tests ---

DELAY_ELITE_STAGE_ENCOUNTERS = {
    "city_elite_delay_01",
    "city_elite_delay_02",
    "city_elite_delay_03",
}

DELAY_ELITE_STAGE_ENEMIES = {
    "first_appointment",
    "second_appointment",
    "final_appointment",
    "reopening_hours_monolith",
    "devouring_waiting_room",
    "minute_moth_cloud",
}

RETIRED_FROM_DELAY_ELITES = {
    "city_elite_03",
    "city_elite_04",
    "counter_of_denial",
    "counter_of_delay",
    "counter_of_certification",
    "archivists_hound",
}


def _enemy_has_fatigue_scaling(enemy) -> bool:
    for intent in enemy.intents:
        for action in intent.actions:
            if (
                action.type == "damage_per_status"
                and action.target == "player"
                and action.status == "fatigue"
                and action.amount_per_stack >= 1
            ):
                return True
    return False


def test_delay_stage_elite_encounters_are_exact_fatigue_pressure_pool() -> None:
    catalog = load_default_content_catalog()

    delay_elites = [
        encounter
        for encounter in catalog.encounter_database.values()
        if (
            encounter.act == 1
            and encounter.difficulty == "elite"
            and "stage_delay" in encounter.tags
        )
    ]

    assert {encounter.id for encounter in delay_elites} == DELAY_ELITE_STAGE_ENCOUNTERS

    for encounter in delay_elites:
        assert RETIRED_FROM_DELAY_ELITES.isdisjoint(set(encounter.enemies)), encounter.id

        enemies = [
            catalog.enemy_database[enemy_id]
            for enemy_id in encounter.enemies
        ]

        assert any(_enemy_applies_fatigue_to_player(enemy) for enemy in enemies), encounter.id
        assert all(len(enemy.intents) >= 4 for enemy in enemies), encounter.id


def test_delay_stage_elite_enemies_are_loaded_tagged_and_have_long_cycles() -> None:
    catalog = load_default_content_catalog()

    assert DELAY_ELITE_STAGE_ENEMIES <= set(catalog.enemy_database)

    for enemy_id in DELAY_ELITE_STAGE_ENEMIES:
        enemy = catalog.enemy_database[enemy_id]
        assert "city" in enemy.tags
        assert "stage_delay" in enemy.tags
        assert "elite_delay" in enemy.tags
        assert len(enemy.intents) >= 4
        assert _enemy_applies_fatigue_to_player(enemy)

    assert _enemy_has_fatigue_scaling(catalog.enemy_database["devouring_waiting_room"])


def test_stage_delay_elite_selection_uses_only_delay_elite_encounters() -> None:
    catalog = load_default_content_catalog()

    for seed in range(120):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="elite",
            stage="delay",
        )

        assert "stage_delay" in encounter.tags
        assert encounter.id in DELAY_ELITE_STAGE_ENCOUNTERS

# --- End delay elite pool tests ---
