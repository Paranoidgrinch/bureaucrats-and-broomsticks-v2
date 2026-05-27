from dataclasses import dataclass, field
from math import ceil
from random import Random

from bab.combat.state import CombatState, Combatant
from bab.combat.deck import build_deck, shuffle_draw_pile
from bab.systems.encounters import choose_random_encounter
from bab.combat.enemies import create_enemies_for_encounter
from bab.models import (
    Card,
    CharacterClass,
    EncounterDefinition,
    EncounterDifficulty,
    EnemyDefinition,
    EventDefinition,
    RelicDefinition,
    StatusDefinition,
)
from bab.systems.gold import gold_reward_for_map_node
from bab.systems.relics import apply_combat_start_relics, gold_reward_bonus
from bab.run.map import MapNode, RunMap, combat_difficulty_for_depth, generate_act_map, generate_boss_gauntlet_map, generate_staged_pilgrimage_map


@dataclass
class RunState:
    character_class: CharacterClass
    card_database: dict[str, Card]
    enemy_database: dict[str, EnemyDefinition]
    encounter_database: dict[str, EncounterDefinition]
    status_database: dict[str, StatusDefinition]
    rng: Random
    run_deck: list[Card]
    current_hp: int
    run_map: RunMap
    event_database: dict[str, EventDefinition] = field(default_factory=dict)
    relic_database: dict[str, RelicDefinition] = field(default_factory=dict)
    relics: list[RelicDefinition] = field(default_factory=list)
    current_node_id: str | None = None
    completed_node_ids: list[str] = field(default_factory=list)
    seen_event_ids: list[str] = field(default_factory=list)
    act: int = 1
    fight_number: int = 1
    max_fights: int = 99
    gold: int = 0
    mimic_chance: float = 0.20
    treasure_mimic_encounter_id: str | None = "city_elite_02"
    waiting_room_heal_percent: int = 25
    card_reward_choices: int = 3
    card_reward_chance: float = 1.0
    shop_card_offer_count: int = 5
    shop_relic_offer_count: int = 3
    shop_price_multiplier: float = 1.0
    event_combat_chance: float = 0.0
    next_combat_player_strength: int = 0
    next_combat_player_panic: int = 0
    next_combat_player_fatigue: int = 0
    next_combat_enemy_strength: int = 0
    next_combat_enemy_hp_loss_percent: int = 0
    next_combat_card_reward_bonus: int = 0
    pending_card_reward_bonus_choices: int = 0

    def is_complete(self) -> bool:
        return (
            self.run_map.boss_node_id in self.completed_node_ids
            or self.fight_number > self.max_fights
        )

    def is_defeated(self) -> bool:
        return self.current_hp <= 0

    def displayed_fight_number(self) -> int:
        return min(self.fight_number, self.max_fights)

    def current_node(self) -> MapNode | None:
        if self.current_node_id is None:
            return None

        return self.run_map.get_node(self.current_node_id)

    def available_map_nodes(self) -> list[MapNode]:
        if self.current_node_id is None:
            return [
                self.run_map.get_node(node_id)
                for node_id in self.run_map.start_node_ids
            ]

        return self.run_map.available_next_nodes(self.current_node_id)


def create_new_run(
    *,
    character_class: CharacterClass,
    card_database: dict[str, Card],
    enemy_database: dict[str, EnemyDefinition],
    encounter_database: dict[str, EncounterDefinition],
    status_database: dict[str, StatusDefinition],
    event_database: dict[str, EventDefinition] | None = None,
    relic_database: dict[str, RelicDefinition] | None = None,
    rng: Random | None = None,
    act: int = 1,
    max_fights: int = 99,
    map_steps_before_boss: int = 9,
    map_width: int = 4,
    map_first_elite_depth: int = 6,
    map_elite_weight_multiplier: float = 1.0,
    map_layout: str = "standard",
    map_boss_count: int = 1,
    map_boss_encounter_ids: tuple[str, ...] | list[str] | None = None,
    map_max_events: int | None = None,
    map_max_treasures: int | None = None,
    map_max_elites: int | None = None,
    mimic_chance: float = 0.20,
    treasure_mimic_encounter_id: str | None = "city_elite_02",
    waiting_room_heal_percent: int = 25,
    card_reward_choices: int = 3,
    card_reward_chance: float = 1.0,
    shop_card_offer_count: int = 5,
    shop_relic_offer_count: int = 3,
    shop_price_multiplier: float = 1.0,
    event_combat_chance: float = 0.0,
    starting_gold: int = 0,
) -> RunState:
    if rng is None:
        rng = Random()

    run_deck = build_deck(
        character_class.starting_deck,
        card_database,
    )

    if map_layout == "boss_gauntlet":
        run_map = generate_boss_gauntlet_map(
            rng,
            act=act,
            boss_count=map_boss_count,
            boss_encounter_ids=map_boss_encounter_ids,
        )
    elif map_layout == "standard":
        run_map = generate_act_map(
            rng,
            act=act,
            steps_before_boss=map_steps_before_boss,
            width=map_width,
            first_elite_depth=map_first_elite_depth,
            elite_weight_multiplier=map_elite_weight_multiplier,
        )
    elif map_layout == "staged_pilgrimage":
        run_map = generate_staged_pilgrimage_map(
            rng,
            act=act,
            steps_before_boss=map_steps_before_boss,
            width=map_width,
            first_elite_depth=map_first_elite_depth,
            max_events=3 if map_max_events is None else map_max_events,
            max_treasures=1 if map_max_treasures is None else map_max_treasures,
            max_elites=2 if map_max_elites is None else map_max_elites,
        )
    else:
        raise ValueError(f"Unsupported map layout: {map_layout}")

    return RunState(
        character_class=character_class,
        card_database=card_database,
        enemy_database=enemy_database,
        encounter_database=encounter_database,
        status_database=status_database,
        event_database=event_database or {},
        relic_database=relic_database or {},
        relics=[],
        rng=rng,
        run_deck=run_deck,
        current_hp=character_class.max_hp,
        run_map=run_map,
        current_node_id=None,
        completed_node_ids=[],
        act=act,
        fight_number=1,
        max_fights=max_fights,
        gold=starting_gold,
        mimic_chance=mimic_chance,
        treasure_mimic_encounter_id=treasure_mimic_encounter_id,
        waiting_room_heal_percent=waiting_room_heal_percent,
        card_reward_choices=card_reward_choices,
        card_reward_chance=card_reward_chance,
        shop_card_offer_count=shop_card_offer_count,
        shop_relic_offer_count=shop_relic_offer_count,
        shop_price_multiplier=shop_price_multiplier,
        event_combat_chance=event_combat_chance,
    )


def enter_map_node(
    run_state: RunState,
    node_id: str,
) -> None:
    if run_state.current_node_id is None:
        if node_id not in run_state.run_map.start_node_ids:
            raise ValueError("The first map node must be one of the start nodes.")

        run_state.current_node_id = node_id
        return

    if run_state.current_node_id not in run_state.completed_node_ids:
        raise ValueError("Current map node must be completed before advancing.")

    current_node = run_state.run_map.get_node(run_state.current_node_id)

    if node_id not in current_node.next_node_ids:
        raise ValueError("Cannot advance to a node that is not connected.")

    run_state.current_node_id = node_id


def complete_current_map_node(run_state: RunState) -> None:
    if run_state.current_node_id is None:
        raise ValueError("Cannot complete a map node before entering one.")

    if run_state.current_node_id not in run_state.completed_node_ids:
        run_state.completed_node_ids.append(run_state.current_node_id)


def _combat_difficulty_for_run_state(
    run_state: RunState,
    fallback_difficulty: EncounterDifficulty,
) -> EncounterDifficulty:
    current_node = run_state.current_node()

    if current_node is None:
        return fallback_difficulty

    if current_node.encounter_difficulty is None:
        raise ValueError("Current map node does not contain a combat encounter.")

    return current_node.encounter_difficulty


def create_combat_state_for_next_encounter(
    run_state: RunState,
    *,
    difficulty: EncounterDifficulty = "normal",
) -> CombatState:
    if run_state.is_defeated():
        raise ValueError("Cannot start combat because the player has no HP.")

    if run_state.is_complete():
        raise ValueError("Cannot start combat because the run is already complete.")

    encounter_difficulty = _combat_difficulty_for_run_state(
        run_state,
        difficulty,
    )

    current_node = run_state.current_node()
    if current_node is not None and current_node.encounter_id is not None:
        try:
            encounter = run_state.encounter_database[current_node.encounter_id]
        except KeyError as error:
            raise ValueError(
                f"Map node references unknown encounter: {current_node.encounter_id}"
            ) from error
    else:
        encounter = choose_random_encounter(
            run_state.encounter_database,
            run_state.rng,
            act=run_state.act,
            difficulty=encounter_difficulty,
            stage=getattr(current_node, "stage", None),
        )

    enemies = create_enemies_for_encounter(
        encounter.id,
        run_state.encounter_database,
        run_state.enemy_database,
    )

    player = Combatant(
        id=run_state.character_class.id,
        name=run_state.character_class.name,
        max_hp=run_state.character_class.max_hp,
        hp=run_state.current_hp,
    )

    state = CombatState(
        player=player,
        enemies=enemies,
        max_energy=run_state.character_class.starting_energy,
        energy=run_state.character_class.starting_energy,
        draw_pile=list(run_state.run_deck),
        status_database=run_state.status_database,
        card_database=run_state.card_database,
    )
    state.encounter_id = encounter.id
    state.encounter_name = encounter.name
    state.log.append(f"Encounter chosen: {encounter.name}.")
    apply_combat_start_relics(state, run_state.relics)
    apply_next_combat_modifiers(run_state, state)
    shuffle_draw_pile(state, run_state.rng)

    return state



def event_node_triggers_hidden_combat(
    run_state: RunState,
    node: MapNode,
) -> bool:
    if node.node_type != "event":
        return False
    if run_state.event_combat_chance <= 0:
        return False
    return run_state.rng.random() < run_state.event_combat_chance


def _steps_before_boss_for_run_map(run_state: RunState) -> int:
    return max(
        node.depth
        for node in run_state.run_map.nodes.values()
        if node.node_type != "boss"
    )


def _combat_difficulty_for_hidden_event_node(
    run_state: RunState,
    node: MapNode,
) -> EncounterDifficulty:
    return combat_difficulty_for_depth(
        node.depth,
        _steps_before_boss_for_run_map(run_state),
    )


def create_combat_state_for_hidden_event_node(
    run_state: RunState,
    node: MapNode,
) -> CombatState:
    if node.node_type != "event":
        raise ValueError("Hidden event combat can only be created for event nodes.")
    if run_state.is_defeated():
        raise ValueError("Cannot start combat because the player has no HP.")
    if run_state.is_complete():
        raise ValueError("Cannot start combat because the run is already complete.")

    encounter_difficulty = _combat_difficulty_for_hidden_event_node(run_state, node)
    encounter = choose_random_encounter(
        run_state.encounter_database,
        run_state.rng,
        act=run_state.act,
        difficulty=encounter_difficulty,
        stage=node.stage,
    )
    enemies = create_enemies_for_encounter(
        encounter.id,
        run_state.encounter_database,
        run_state.enemy_database,
    )
    player = Combatant(
        id=run_state.character_class.id,
        name=run_state.character_class.name,
        max_hp=run_state.character_class.max_hp,
        hp=run_state.current_hp,
    )
    state = CombatState(
        player=player,
        enemies=enemies,
        max_energy=run_state.character_class.starting_energy,
        energy=run_state.character_class.starting_energy,
        draw_pile=list(run_state.run_deck),
        status_database=run_state.status_database,
        card_database=run_state.card_database,
    )
    state.encounter_id = encounter.id
    state.encounter_name = encounter.name
    state.log.append(f"Hidden event combat: {encounter.name}.")
    apply_combat_start_relics(state, run_state.relics)
    apply_next_combat_modifiers(run_state, state)
    shuffle_draw_pile(state, run_state.rng)
    return state



def _clamped_percent_loss(percent: int) -> int:
    return max(0, min(99, percent))


def apply_next_combat_modifiers(
    run_state: RunState,
    combat_state: CombatState,
) -> None:
    if run_state.next_combat_player_strength > 0:
        combat_state.player.apply_status(
            "strength",
            run_state.next_combat_player_strength,
        )
        combat_state.log.append(
            f"Event modifier: Player starts with "
            f"{run_state.next_combat_player_strength} Strength."
        )

    if run_state.next_combat_player_panic > 0:
        combat_state.player.apply_status(
            "panic",
            run_state.next_combat_player_panic,
        )
        combat_state.log.append(
            f"Event modifier: Player starts with "
            f"{run_state.next_combat_player_panic} Panic."
        )

    if run_state.next_combat_player_fatigue > 0:
        combat_state.player.apply_status(
            "fatigue",
            run_state.next_combat_player_fatigue,
        )
        combat_state.log.append(
            f"Event modifier: Player starts with "
            f"{run_state.next_combat_player_fatigue} Fatigue."
        )

    if run_state.next_combat_enemy_strength > 0:
        for enemy in combat_state.living_enemies():
            enemy.apply_status(
                "strength",
                run_state.next_combat_enemy_strength,
            )
        combat_state.log.append(
            f"Event modifier: Enemies start with "
            f"{run_state.next_combat_enemy_strength} Strength."
        )

    if run_state.next_combat_enemy_hp_loss_percent > 0:
        percent = _clamped_percent_loss(run_state.next_combat_enemy_hp_loss_percent)
        for enemy in combat_state.living_enemies():
            new_hp = max(1, ceil(enemy.max_hp * (100 - percent) / 100))
            enemy.hp = min(enemy.hp, new_hp)
        combat_state.log.append(
            f"Event modifier: Enemies start with {percent}% less HP."
        )

    if run_state.next_combat_card_reward_bonus > 0:
        run_state.pending_card_reward_bonus_choices += (
            run_state.next_combat_card_reward_bonus
        )
        combat_state.log.append(
            f"Event modifier: Next card reward has +"
            f"{run_state.next_combat_card_reward_bonus} choice(s)."
        )

    run_state.next_combat_player_strength = 0
    run_state.next_combat_player_panic = 0
    run_state.next_combat_player_fatigue = 0
    run_state.next_combat_enemy_strength = 0
    run_state.next_combat_enemy_hp_loss_percent = 0
    run_state.next_combat_card_reward_bonus = 0


def finish_victorious_combat(
    run_state: RunState,
    combat_state: CombatState,
) -> int:
    if not combat_state.is_victory():
        raise ValueError("Cannot finish combat as victory because enemies are still alive.")

    current_map_node = None

    if run_state.current_node_id is not None:
        if hasattr(run_state, "current_node"):
            current_map_node = run_state.current_node()
        elif hasattr(run_state, "current_map_node"):
            current_map_node = run_state.current_map_node()
        else:
            run_map_nodes = getattr(run_state.run_map, "nodes", [])

            if isinstance(run_map_nodes, dict):
                current_map_node = run_map_nodes.get(run_state.current_node_id)
            else:
                current_map_node = next(
                    (
                        node
                        for node in run_map_nodes
                        if getattr(node, "id", None) == run_state.current_node_id
                    ),
                    None,
                )

    gold_reward = (
        gold_reward_for_map_node(current_map_node, run_state.rng)
        + gold_reward_bonus(run_state.relics)
    )
    run_state.gold += gold_reward

    run_state.current_hp = combat_state.player.hp
    run_state.fight_number += 1

    if run_state.current_node_id is not None:
        complete_current_map_node(run_state)

    return gold_reward

