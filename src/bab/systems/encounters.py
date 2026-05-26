from random import Random

from bab.models import EncounterDefinition, EncounterDifficulty


def _stage_tag(stage: str) -> str:
    return f"stage_{stage}"


def choose_random_encounter(
    encounter_database: dict[str, EncounterDefinition],
    rng: Random,
    *,
    act: int | None = None,
    difficulty: EncounterDifficulty | None = None,
    stage: str | None = None,
) -> EncounterDefinition:
    encounters = list(encounter_database.values())

    if act is not None:
        encounters = [
            encounter
            for encounter in encounters
            if encounter.act == act
        ]

    if difficulty is not None:
        encounters = [
            encounter
            for encounter in encounters
            if encounter.difficulty == difficulty
        ]

    if stage is not None:
        tagged_encounters = [
            encounter
            for encounter in encounters
            if _stage_tag(stage) in encounter.tags
        ]
        if tagged_encounters:
            encounters = tagged_encounters

    if not encounters:
        raise ValueError("No encounters available for the requested filters.")

    weights = [encounter.weight for encounter in encounters]
    return rng.choices(encounters, weights=weights, k=1)[0]
