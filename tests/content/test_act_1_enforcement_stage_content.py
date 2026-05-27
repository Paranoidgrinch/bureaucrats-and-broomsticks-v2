from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.systems.encounters import choose_random_encounter


ENFORCEMENT_STAGE_ENCOUNTERS = {
    "city_normal_enforcement_01",
    "city_normal_enforcement_02",
    "city_normal_enforcement_03",
    "city_normal_enforcement_04",
    "city_normal_enforcement_05",
    "city_normal_enforcement_06",
    "city_normal_enforcement_07",
    "city_normal_enforcement_08",
}

ENFORCEMENT_STAGE_ENEMIES = {
    "warrant_bailiff",
    "levy_constable",
    "gatehouse_enforcer",
    "compliance_chain_guard",
    "threshold_seizure_ward",
    "civic_battering_ram",
}

RETIRED_FROM_ENFORCEMENT_NORMAL_ENEMIES = {
    "second_opinion_hound",
    "archivists_hound",
    "receipt_mimic",
    "red_ribbon_serpent",
    "stamp_goblin",
    "ink_spattered_scribe",
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


def test_enforcement_stage_normal_encounters_are_exact_civic_force_pool() -> None:
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

    assert {encounter.id for encounter in enforcement_encounters} == ENFORCEMENT_STAGE_ENCOUNTERS

    for encounter in enforcement_encounters:
        assert RETIRED_FROM_ENFORCEMENT_NORMAL_ENEMIES.isdisjoint(
            set(encounter.enemies)
        ), encounter.id

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

    for seed in range(160):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="normal",
            stage="enforcement",
        )

        assert "stage_enforcement" in encounter.tags
        assert encounter.id in ENFORCEMENT_STAGE_ENCOUNTERS


# --- Enforcement elite pool tests ---

ENFORCEMENT_ELITE_STAGE_ENCOUNTERS = {
    "city_elite_enforcement_01",
    "city_elite_enforcement_02",
    "city_elite_enforcement_03",
    "city_elite_enforcement_04",
}

ENFORCEMENT_ELITE_STAGE_ENEMIES = {
    "iron_warrant_avatar",
    "seizure_marshal",
    "inventory_lantern",
    "lock_cart",
    "portcullis_judicator",
    "final_notice_knight",
    "sealed_spear",
}

RETIRED_FROM_ENFORCEMENT_ELITES = {
    "city_elite_01",
    "city_elite_02",
    "city_elite_06",
    "city_elite_08",
    "senior_clerk",
    "red_tape_golem",
    "bailiff_of_writs",
    "bailiff_of_warrants",
    "licensed_chimera",
}


def _enemy_gains_any_block(enemy) -> bool:
    for intent in enemy.intents:
        for action in intent.actions:
            if (
                action.type == "gain_block"
                and action.target in {"owner", "all_enemies"}
                and action.amount >= 1
            ):
                return True
    return False


def test_enforcement_stage_elite_encounters_are_exact_civic_force_pool() -> None:
    catalog = load_default_content_catalog()

    enforcement_elites = [
        encounter
        for encounter in catalog.encounter_database.values()
        if (
            encounter.act == 1
            and encounter.difficulty == "elite"
            and "stage_enforcement" in encounter.tags
        )
    ]

    assert {encounter.id for encounter in enforcement_elites} == ENFORCEMENT_ELITE_STAGE_ENCOUNTERS

    for encounter in enforcement_elites:
        assert RETIRED_FROM_ENFORCEMENT_ELITES.isdisjoint(set(encounter.enemies)), encounter.id

        enemies = [
            catalog.enemy_database[enemy_id]
            for enemy_id in encounter.enemies
        ]

        assert any(_enemy_gains_any_block(enemy) for enemy in enemies), encounter.id
        assert any(_enemy_gains_strength(enemy) for enemy in enemies), encounter.id
        assert all(len(enemy.intents) >= 4 for enemy in enemies), encounter.id


def test_enforcement_stage_elite_enemies_are_loaded_tagged_and_have_long_cycles() -> None:
    catalog = load_default_content_catalog()

    assert ENFORCEMENT_ELITE_STAGE_ENEMIES <= set(catalog.enemy_database)

    for enemy_id in ENFORCEMENT_ELITE_STAGE_ENEMIES:
        enemy = catalog.enemy_database[enemy_id]
        assert "city" in enemy.tags
        assert "stage_enforcement" in enemy.tags
        assert "elite_enforcement" in enemy.tags
        assert len(enemy.intents) >= 4
        assert _enemy_gains_any_block(enemy)
        assert _enemy_gains_strength(enemy)


def test_stage_enforcement_elite_selection_uses_only_enforcement_elite_encounters() -> None:
    catalog = load_default_content_catalog()

    for seed in range(160):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="elite",
            stage="enforcement",
        )

        assert "stage_enforcement" in encounter.tags
        assert encounter.id in ENFORCEMENT_ELITE_STAGE_ENCOUNTERS

# --- End enforcement elite pool tests ---
