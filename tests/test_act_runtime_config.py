from bab.console.run_flow import create_run_state
from bab.content.catalog import load_content_catalog_from_act_manifest
from bab.game_config import ACT_MANIFEST_FILES


def test_run_state_uses_act_manifest_runtime_config() -> None:
    for manifest_path in ACT_MANIFEST_FILES:
        catalog = load_content_catalog_from_act_manifest(manifest_path)
        run_state = create_run_state(catalog=catalog)

        assert run_state.mimic_chance == catalog.act_manifest.treasure.mimic_chance
        assert (
            run_state.treasure_mimic_encounter_id
            == catalog.act_manifest.treasure.mimic_encounter_id
        )
        assert (
            run_state.waiting_room_heal_percent
            == catalog.act_manifest.waiting_room.heal_percent
        )


def test_run_state_treasure_mimic_encounter_id_exists_when_enabled() -> None:
    for manifest_path in ACT_MANIFEST_FILES:
        catalog = load_content_catalog_from_act_manifest(manifest_path)
        run_state = create_run_state(catalog=catalog)

        if catalog.act_manifest.treasure.mimic_chance <= 0:
            assert run_state.treasure_mimic_encounter_id is None
            continue

        assert run_state.treasure_mimic_encounter_id is not None
        assert run_state.treasure_mimic_encounter_id in run_state.encounter_database



def test_act_1_uses_staged_pilgrimage_runtime_config() -> None:
    catalog = load_content_catalog_from_act_manifest("data/acts/act_1_city.json")
    run_state = create_run_state(catalog=catalog)

    assert catalog.act_manifest.name == "Act I: The Old City Offices"
    assert catalog.act_manifest.map.layout == "staged_pilgrimage"
    assert catalog.act_manifest.map.max_events == 3
    assert catalog.act_manifest.map.max_treasures == 1
    assert catalog.act_manifest.map.max_elites == 2

    non_boss_nodes = [
        node
        for node in run_state.run_map.nodes.values()
        if node.node_type != "boss"
    ]
    assert sum(node.node_type == "event" for node in non_boss_nodes) <= 3
    assert sum(node.node_type == "treasure" for node in non_boss_nodes) <= 1
    assert sum(node.node_type == "elite" for node in non_boss_nodes) <= 2
    assert {node.stage for node in non_boss_nodes if node.depth == 9} == {"final_office"}
