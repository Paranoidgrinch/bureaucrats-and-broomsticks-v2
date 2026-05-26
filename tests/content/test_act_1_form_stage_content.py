from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.systems.encounters import choose_random_encounter


FORM_STAGE_ENCOUNTERS = {
    "city_easy_05",
    "city_easy_06",
    "city_easy_form_01",
    "city_easy_form_02",
    "city_easy_form_03",
    "city_easy_form_04",
    "city_easy_form_05",
    "city_easy_form_06",
}

FORM_STAGE_ENEMIES = {
    "filing_beetle",
    "form_rat_a",
    "form_rat_b",
    "form_rat_c",
    "unsigned_form_ghost",
    "margin_note_gnawer",
    "misfiled_page",
    "duplicate_copy_mite",
    "blank_line_leech",
    "folded_affidavit_bat",
}

EXPECTED_FORM_HP = {
    "filing_beetle": 32,
    "form_rat_a": 11,
    "form_rat_b": 11,
    "form_rat_c": 11,
    "unsigned_form_ghost": 30,
    "margin_note_gnawer": 33,
    "misfiled_page": 27,
    "duplicate_copy_mite": 16,
    "blank_line_leech": 29,
    "folded_affidavit_bat": 30,
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


def test_form_stage_has_eight_paperwork_intro_encounters() -> None:
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

    assert {encounter.id for encounter in form_encounters} == FORM_STAGE_ENCOUNTERS

    for encounter in form_encounters:
        enemies = [
            catalog.enemy_database[enemy_id]
            for enemy_id in encounter.enemies
        ]
        assert any(_enemy_applies_paperwork_to_player(enemy) for enemy in enemies), encounter.id


def test_form_stage_enemies_have_requested_hp_and_tags() -> None:
    catalog = load_default_content_catalog()

    assert FORM_STAGE_ENEMIES <= set(catalog.enemy_database)

    for enemy_id, expected_hp in EXPECTED_FORM_HP.items():
        enemy = catalog.enemy_database[enemy_id]
        assert enemy.max_hp == expected_hp
        assert "city" in enemy.tags
        assert "stage_form" in enemy.tags
        assert "paperwork_intro" in enemy.tags
        assert _enemy_applies_paperwork_to_player(enemy)


def test_form_rat_swarm_uses_three_rats_with_offset_intent_starts() -> None:
    catalog = load_default_content_catalog()
    encounter = catalog.encounter_database["city_easy_06"]

    assert encounter.enemies == ["form_rat_a", "form_rat_b", "form_rat_c"]

    assert catalog.enemy_database["form_rat_a"].intents[0].name == "Gnaw the Margins"
    assert catalog.enemy_database["form_rat_b"].intents[0].name == "Many Small Bites"
    assert catalog.enemy_database["form_rat_c"].intents[0].name == "Scatter the Pages"


def test_duplicate_copy_mite_encounter_uses_two_identical_mites() -> None:
    catalog = load_default_content_catalog()
    encounter = catalog.encounter_database["city_easy_form_04"]

    assert encounter.enemies == ["duplicate_copy_mite", "duplicate_copy_mite"]
    mite = catalog.enemy_database["duplicate_copy_mite"]
    assert mite.max_hp == 16
    assert [intent.name for intent in mite.intents] == [
        "Make Another Copy",
        "Carbon Bite",
        "Copy Filed Twice",
    ]


def test_form_stage_requested_damage_and_panic_values_are_represented() -> None:
    catalog = load_default_content_catalog()

    assert 12 in _enemy_damage_amounts(catalog.enemy_database["filing_beetle"])
    assert _enemy_damage_amounts(catalog.enemy_database["form_rat_a"]).count(1) >= 6
    assert 12 in _enemy_damage_amounts(catalog.enemy_database["misfiled_page"])
    assert 5 in _enemy_damage_amounts(catalog.enemy_database["duplicate_copy_mite"])
    assert _enemy_applies_panic_to_player(catalog.enemy_database["blank_line_leech"])
    assert _enemy_applies_panic_to_player(catalog.enemy_database["folded_affidavit_bat"])


def test_stage_form_easy_selection_uses_only_form_tagged_encounters() -> None:
    catalog = load_default_content_catalog()

    for seed in range(40):
        encounter = choose_random_encounter(
            catalog.encounter_database,
            Random(seed),
            act=1,
            difficulty="easy",
            stage="form",
        )
        assert "stage_form" in encounter.tags
        assert encounter.id in FORM_STAGE_ENCOUNTERS
