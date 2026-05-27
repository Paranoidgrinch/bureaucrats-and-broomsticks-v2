from bab.content.catalog import load_default_content_catalog


BOSS_MECHANICS = {
    "deputy_undersecretary": {
        "tag": "boss_fatigue",
        "required_action": ("apply_status", "fatigue"),
        "required_scaling": ("damage_per_status", "fatigue"),
        "hp": 118,
    },
    "queue_commissioner": {
        "tag": "boss_panic",
        "required_action": ("apply_status", "panic"),
        "required_scaling": ("damage_per_status", "panic"),
        "hp": 112,
    },
    "lord_sealkeeper": {
        "tag": "boss_block",
        "required_action": ("gain_block", None),
        "required_scaling": None,
        "hp": 124,
    },
    "municipal_dragon": {
        "tag": "boss_strength",
        "required_action": ("gain_strength", None),
        "required_scaling": None,
        "hp": 132,
    },
    "living_charter": {
        "tag": "boss_paperwork",
        "required_action": ("apply_status", "paperwork"),
        "required_scaling": ("damage_per_status", "paperwork"),
        "hp": 120,
    },
}


def _enemy_has_action(enemy, action_type: str, status: str | None = None) -> bool:
    for intent in enemy.intents:
        for action in intent.actions:
            if action.type != action_type:
                continue
            if status is not None and action.status != status:
                continue
            return True
    return False


def test_act_1_bosses_have_distinct_mechanic_identities() -> None:
    catalog = load_default_content_catalog()

    for enemy_id, expectation in BOSS_MECHANICS.items():
        enemy = catalog.enemy_database[enemy_id]

        assert enemy.max_hp == expectation["hp"]
        assert "boss" in enemy.tags
        assert expectation["tag"] in enemy.tags
        assert len(enemy.intents) == 5
        assert _enemy_has_action(
            enemy,
            expectation["required_action"][0],
            expectation["required_action"][1],
        ), enemy_id

        if expectation["required_scaling"] is not None:
            assert _enemy_has_action(
                enemy,
                expectation["required_scaling"][0],
                expectation["required_scaling"][1],
            ), enemy_id


def test_living_charter_covers_doubt_as_secondary_boss_mechanic() -> None:
    catalog = load_default_content_catalog()

    living_charter = catalog.enemy_database["living_charter"]

    assert "boss_doubt" in living_charter.tags
    assert _enemy_has_action(living_charter, "apply_status", "doubt")


def test_act_1_boss_encounters_remain_single_boss_showdowns() -> None:
    catalog = load_default_content_catalog()

    boss_encounters = [
        encounter
        for encounter in catalog.encounter_database.values()
        if encounter.act == 1 and encounter.difficulty == "boss"
    ]

    assert len(boss_encounters) == 5

    for encounter in boss_encounters:
        assert len(encounter.enemies) == 1
        enemy = catalog.enemy_database[encounter.enemies[0]]
        assert "boss" in enemy.tags
