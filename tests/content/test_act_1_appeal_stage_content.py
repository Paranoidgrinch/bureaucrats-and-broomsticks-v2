from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.systems.encounters import choose_random_encounter


APPEAL_STAGE_ENCOUNTERS = {
    "city_normal_appeal_01",
    "city_normal_appeal_02",
    "city_normal_appeal_03",
    "city_normal_appeal_04",
    "city_normal_appeal_05",
    "city_normal_appeal_06",
    "city_normal_appeal_07",
    "city_normal_appeal_08",
}

APPEAL_STAGE_ENEMIES = {
    "appeals_clerk",
    "objection_sprite",
    "procedural_advocate",
    "counterclaim_imp",
    "self_correcting_record",
    "motion_to_reconsider",
    "sustaining_gavel",
}

RETIRED_FROM_APPEAL_ENEMIES = {
    "second_opinion_hound",
    "archivists_hound",
    "receipt_mimic",
    "red_ribbon_serpent",
    "stamp_goblin",
    "ink_spattered_scribe",
}


def _enemy_applies_doubt_or_paperwork_to_player(enemy) -> bool:
    for intent in enemy.intents:
        for action in intent.actions:
            if (
                action.type == "apply_status"
                and action.target == "player"
                and action.status in {"doubt", "paperwork"}
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


def test_appeal_stage_normal_encounters_are_exact_escalating_procedure_pool() -> None:
    catalog = load_default_content_catalog()

    appeal_encounters = [
        encounter
        for encounter in catalog.encounter_database.values()
        if (
            encounter.act == 1
            and encounter.difficulty == "normal"
            and "stage_appeal" in encounter.tags
        )
    ]

    assert {encounter.id for encounter in appeal_encounters} == APPEAL_STAGE_ENCOUNTERS

    for encounter in appeal_encounters:
        assert RETIRED_FROM_APPEAL_ENEMIES.isdisjoint(set(encounter.enemies)), encounter.id

        enemies = [
            catalog.enemy_database[enemy_id]
            for enemy_id in encounter.enemies
        ]

        assert any(
            _enemy_applies_doubt_or_paperwork_to_player(enemy)
            for enemy in enemies
        ), encounter.id
        assert any(_enemy_gains_strength(enemy) for enemy in enemies), encounter.id


def test_appeal_stage_enemies_are_loaded_and_tagged_for_appeal() -> None:
    catalog = load_default_content_catalog()

    assert APPEAL_STAGE_ENEMIES <= set(catalog.enemy_database)

    for enemy_id in APPEAL_STAGE_ENEMIES:
        enemy = catalog.enemy_database[enemy_id]
        assert "city" in enemy.tags
        assert "stage_appeal" in enemy.tags
        assert _enemy_applies_doubt_or_paperwork_to_player(enemy)
        assert _enemy_gains_strength(enemy)


def test_stage_appeal_normal_selection_uses_only_appeal_tagged_encounters() -> None:
    catalog = load_default_content_catalog()

    for seed in range(120):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="normal",
            stage="appeal",
        )

        assert "stage_appeal" in encounter.tags
        assert encounter.id in APPEAL_STAGE_ENCOUNTERS


# --- Appeal elite pool tests ---

APPEAL_ELITE_STAGE_ENCOUNTERS = {
    "city_elite_appeal_01",
    "city_elite_appeal_02",
    "city_elite_appeal_03",
}

APPEAL_ELITE_STAGE_ENEMIES = {
    "lower_appellate_step",
    "middle_appellate_step",
    "upper_appellate_step",
    "living_petition_chorus",
    "remanded_case_phantom",
    "escalation_writ",
}

RETIRED_FROM_APPEAL_ELITES = {
    "city_elite_05",
    "city_elite_07",
    "stampede_of_stamps",
    "ink_witch_auditor",
}


def _enemy_has_doubt_scaling(enemy) -> bool:
    for intent in enemy.intents:
        for action in intent.actions:
            if (
                action.type == "damage_per_status"
                and action.target == "player"
                and action.status == "doubt"
                and action.amount_per_stack >= 1
            ):
                return True
    return False


def test_appeal_stage_elite_encounters_are_exact_escalation_pool() -> None:
    catalog = load_default_content_catalog()

    appeal_elites = [
        encounter
        for encounter in catalog.encounter_database.values()
        if (
            encounter.act == 1
            and encounter.difficulty == "elite"
            and "stage_appeal" in encounter.tags
        )
    ]

    assert {encounter.id for encounter in appeal_elites} == APPEAL_ELITE_STAGE_ENCOUNTERS

    for encounter in appeal_elites:
        assert RETIRED_FROM_APPEAL_ELITES.isdisjoint(set(encounter.enemies)), encounter.id

        enemies = [
            catalog.enemy_database[enemy_id]
            for enemy_id in encounter.enemies
        ]

        assert any(
            _enemy_applies_doubt_or_paperwork_to_player(enemy)
            for enemy in enemies
        ), encounter.id
        assert any(_enemy_gains_strength(enemy) for enemy in enemies), encounter.id
        assert all(len(enemy.intents) >= 4 for enemy in enemies), encounter.id


def test_appeal_stage_elite_enemies_are_loaded_tagged_and_have_long_cycles() -> None:
    catalog = load_default_content_catalog()

    assert APPEAL_ELITE_STAGE_ENEMIES <= set(catalog.enemy_database)

    for enemy_id in APPEAL_ELITE_STAGE_ENEMIES:
        enemy = catalog.enemy_database[enemy_id]
        assert "city" in enemy.tags
        assert "stage_appeal" in enemy.tags
        assert "elite_appeal" in enemy.tags
        assert len(enemy.intents) >= 4
        assert _enemy_applies_doubt_or_paperwork_to_player(enemy)
        assert _enemy_gains_strength(enemy)

    assert _enemy_has_doubt_scaling(catalog.enemy_database["remanded_case_phantom"])


def test_stage_appeal_elite_selection_uses_only_appeal_elite_encounters() -> None:
    catalog = load_default_content_catalog()

    for seed in range(120):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="elite",
            stage="appeal",
        )

        assert "stage_appeal" in encounter.tags
        assert encounter.id in APPEAL_ELITE_STAGE_ENCOUNTERS

# --- End appeal elite pool tests ---
