from random import Random

import pytest

from bab.content.catalog import load_default_content_catalog
from bab.console.run_flow import create_run_state
from bab.models import EventEffect
from bab.systems.event_effects import (
    apply_event_gain_relic,
    eligible_event_relics,
)


def make_run_state(character_id: str = "bureaucrat"):
    catalog = load_default_content_catalog()
    catalog = catalog.__class__(
        act_manifest=catalog.act_manifest,
        character_classes=catalog.character_classes,
        character_class=catalog.character_classes[character_id],
        card_database=catalog.card_database,
        enemy_database=catalog.enemy_database,
        encounter_database=catalog.encounter_database,
        status_database=catalog.status_database,
        event_database=catalog.event_database,
        relic_database=catalog.relic_database,
    )
    return create_run_state(catalog=catalog, rng=Random(1))


def make_effect(**kwargs) -> EventEffect:
    return EventEffect.model_validate(
        {
            "type": "gain_relic",
            **kwargs,
        }
    )


def test_event_relic_pool_excludes_boss_relics_owned_relics_and_other_classes() -> None:
    run_state = make_run_state("bureaucrat")
    run_state.relics.append(run_state.relic_database["self_inking_stamp"])

    pool = eligible_event_relics(run_state)
    pool_ids = {
        relic.id
        for relic in pool
    }

    assert "self_inking_stamp" not in pool_ids
    assert all(relic.rarity != "boss" for relic in pool)
    assert all(
        not relic.allowed_classes
        or run_state.character_class.id in relic.allowed_classes
        for relic in pool
    )

    # A class relic from the current class is eligible.
    assert "brass_filing_tray" in pool_ids

    # Relics from other class-specific pools must not leak into the event pool.
    assert all(
        not relic.allowed_classes
        or relic.allowed_classes == [run_state.character_class.id]
        for relic in pool
    )


def test_gain_relic_adds_relic_and_applies_pickup_effects() -> None:
    run_state = make_run_state("bureaucrat")
    run_state.current_hp = 1

    relic = apply_event_gain_relic(
        run_state,
        make_effect(tag="voucher"),
    )

    assert relic in run_state.relics
    assert "voucher" in relic.tags
    assert run_state.current_hp > 1


def test_gain_relic_can_filter_by_tag() -> None:
    run_state = make_run_state("bureaucrat")

    relic = apply_event_gain_relic(
        run_state,
        make_effect(tag="bureaucrat"),
    )

    assert relic in run_state.relics
    assert "bureaucrat" in relic.tags
    assert relic.allowed_classes == ["bureaucrat"]


def test_gain_relic_rejects_unknown_tag_pool() -> None:
    run_state = make_run_state("bureaucrat")

    with pytest.raises(ValueError, match="No event-eligible relics available with tag"):
        apply_event_gain_relic(
            run_state,
            make_effect(tag="definitely_not_a_real_relic_tag"),
        )


def test_gain_relic_rejects_empty_pool() -> None:
    run_state = make_run_state("bureaucrat")
    run_state.relics.extend(eligible_event_relics(run_state))

    with pytest.raises(ValueError, match="No event-eligible relics available"):
        apply_event_gain_relic(
            run_state,
            make_effect(),
        )
