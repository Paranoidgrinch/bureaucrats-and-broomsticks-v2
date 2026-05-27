from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.systems.encounters import choose_random_encounter


EXPECTED_STAGE_ELITES = {
    "delay": {
        "city_elite_delay_01",
        "city_elite_delay_02",
        "city_elite_delay_03",
    },
    "appeal": {
        "city_elite_appeal_01",
        "city_elite_appeal_02",
        "city_elite_appeal_03",
    },
    "enforcement": {
        "city_elite_01",
        "city_elite_02",
        "city_elite_06",
        "city_elite_08",
    },
}


def test_act_1_elites_are_partitioned_across_elite_capable_stages() -> None:
    catalog = load_default_content_catalog()

    for stage, expected_ids in EXPECTED_STAGE_ELITES.items():
        stage_tag = f"stage_{stage}"
        stage_elites = {
            encounter.id
            for encounter in catalog.encounter_database.values()
            if (
                encounter.act == 1
                and encounter.difficulty == "elite"
                and stage_tag in encounter.tags
            )
        }

        assert expected_ids <= stage_elites


def test_stage_aware_elite_selection_uses_stage_tagged_elites() -> None:
    catalog = load_default_content_catalog()

    for stage, expected_ids in EXPECTED_STAGE_ELITES.items():
        stage_tag = f"stage_{stage}"

        for seed in range(30):
            encounter = choose_random_encounter(
                catalog.encounter_database,
                Random(seed),
                act=1,
                difficulty="elite",
                stage=stage,
            )

            assert encounter.id in expected_ids
            assert stage_tag in encounter.tags
