from collections import Counter
from random import Random

from bab.content.catalog import load_default_content_catalog
from bab.models.types import EventEffectType
from bab.systems.events import choose_random_event


EXPECTED_EVENT_IDS = {
    "misfiling_cabinet",
    "certified_copy_drawer",
    "fee_table_updates_itself",
    "lost_and_found_desk",
    "act_1_shop",
    "complaint_ledger",
    "waiting_token_exchange",
    "clerk_who_almost_helps",
    "witness_queue",
    "sealed_back_door",
    "clerks_tea_break",
    "friendly_filing_cabinet",
    "receipt_of_prior_effort",
    "contradictory_map",
    "archive_window",
}

RISK_REWARD_EVENTS = {
    "certified_copy_drawer",
    "fee_table_updates_itself",
    "act_1_shop",
    "waiting_token_exchange",
    "clerk_who_almost_helps",
    "witness_queue",
    "sealed_back_door",
    "contradictory_map",
}

DECK_EVENTS = EXPECTED_EVENT_IDS - RISK_REWARD_EVENTS


def _effect_types(event):
    return {
        effect.type
        for choice in event.choices
        for effect in choice.effects
    }


def test_act_1_event_pool_has_fifteen_shared_non_narrative_events() -> None:
    catalog = load_default_content_catalog()
    events = [
        event
        for event in catalog.event_database.values()
        if event.act == 1
    ]

    assert {event.id for event in events} == EXPECTED_EVENT_IDS
    assert len(events) == 15
    assert all(event.event_type != "narrative" for event in events)
    assert sum(event.event_type == "risk_reward" for event in events) == 8
    assert sum(event.event_type == "deck" for event in events) == 7

    for event in events:
        assert "city" in event.tags
        assert "act_1_event_pool" in event.tags
        assert not any(tag.startswith("stage_") for tag in event.tags)


def test_act_1_event_choices_are_not_empty_or_none_only() -> None:
    catalog = load_default_content_catalog()

    for event_id in EXPECTED_EVENT_IDS:
        event = catalog.event_database[event_id]
        assert len(event.choices) >= 2, event_id

        for choice in event.choices:
            assert choice.effects, (event_id, choice.id)
            assert not all(effect.type == "none" for effect in choice.effects), (
                event_id,
                choice.id,
            )


def test_act_1_event_pool_uses_only_registered_effects() -> None:
    catalog = load_default_content_catalog()
    registered_effects = set(EventEffectType.__args__)

    for event_id in EXPECTED_EVENT_IDS:
        event = catalog.event_database[event_id]
        for choice in event.choices:
            for effect in choice.effects:
                assert effect.type in registered_effects


def test_act_1_event_pool_includes_distinct_new_effect_archetypes() -> None:
    catalog = load_default_content_catalog()
    all_effects = {
        effect.type
        for event_id in EXPECTED_EVENT_IDS
        for choice in catalog.event_database[event_id].choices
        for effect in choice.effects
    }

    expected_effects = {
        "lose_hp",
        "gain_gold",
        "lose_gold",
        "heal_percent_max_hp",
        "add_card_to_deck",
        "gain_relic",
        "duplicate_card",
        "transform_card",
        "next_combat_player_strength",
        "next_combat_player_panic",
        "next_combat_player_fatigue",
        "next_combat_enemy_strength",
        "next_combat_enemy_hp_loss_percent",
        "next_combat_card_reward_bonus",
        "open_shop",
    }

    assert expected_effects <= all_effects


def test_act_1_event_pool_keeps_shop_event_with_open_shop_choice() -> None:
    catalog = load_default_content_catalog()
    shop = catalog.event_database["act_1_shop"]

    assert shop.name == "The Licensed Vendor"
    assert shop.event_type == "risk_reward"
    assert any(
        effect.type == "open_shop"
        for choice in shop.choices
        for effect in choice.effects
    )
    assert any(
        effect.type == "gain_relic"
        for choice in shop.choices
        for effect in choice.effects
    )


def test_act_1_event_selection_uses_shared_pool_without_stage_tags() -> None:
    catalog = load_default_content_catalog()
    sampled = Counter()

    for event_type in {"risk_reward", "deck"}:
        for seed in range(200):
            event = choose_random_event(
                catalog.event_database,
                Random(seed),
                act=1,
                event_type=event_type,
                stage="form",
            )
            sampled[event.id] += 1
            assert event.act == 1
            assert event.event_type == event_type
            assert not any(tag.startswith("stage_") for tag in event.tags)

    assert RISK_REWARD_EVENTS <= set(sampled)
    assert DECK_EVENTS <= set(sampled)
