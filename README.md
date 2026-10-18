# Bureaucrats and Broomsticks (Python version)

A satirical fantasy roguelike deckbuilder about magic, paperwork and questionable career choices, played in
the terminal.

This is the original Python version of the game. All mechanics are hardcoded in Python. It is still playable
as a beta but no longer developed: the game has been rebuilt on the data-driven
[RogueDeck engine](https://github.com/Paranoidgrinch/RogueDeck-Core), with the content in
[bnb-content](https://github.com/Paranoidgrinch/bnb-content) and a Godot frontend in
[bnb-godot](https://github.com/Paranoidgrinch/bnb-godot).

## Download and play (Windows)

1. Download [Bureaucrats-and-Broomsticks-Windows-x64.zip](https://github.com/Paranoidgrinch/bureaucrats-and-broomsticks-v2/releases/download/v0.1.0-beta.1/Bureaucrats-and-Broomsticks-Windows-x64.zip)
   from the [v0.1.0-beta.1 release](https://github.com/Paranoidgrinch/bureaucrats-and-broomsticks-v2/releases/tag/v0.1.0-beta.1).
2. Extract the whole archive. The game does not run from inside the ZIP.
3. Start `Bureaucrats-and-Broomsticks.exe`. Keep it next to the included `_internal` folder.

No installation or Python is required. The build is not signed, so Windows may show a SmartScreen warning;
choose *More info*, then *Run anyway*.

## The game

Magic still exists, but it has been licensed, archived, audited and assigned to departments. The player
chooses one of nine professions and fights through five acts: the City, the Archives, the Green Docket, the
Licensing Labyrinth and the Divine Ledger.

Classes: Bureaucrat, Failed Wizard, Guild Assassin Apprentice, Hedge Witch, Mortuary Apprentice, Night Watch
Recruit, Sewer Diplomat, Shroomancer, Witch Clerk. Each has its own cards, resources and mechanics.

The beta contains:

- nine playable classes and five acts
- normal, elite and boss encounters, including fights against several enemies
- relics, statuses and class resources
- shops, rewards, events and branching map routes
- deterministic seeded runs
- simulation and balancing tools

Balance, presentation and individual mechanics are still unfinished.

## Controls

All choices are listed in the terminal.

| Input | Action |
| --- | --- |
| a listed number | choose a class, route, card, target or reward |
| `end` | end the combat turn |
| `log` | show the full combat log |
| `quit` | leave the game |

Enemy intents, health, block, energy, card costs and statuses are shown during combat.

## Running from source

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
.venv/bin/python -m bab.main     # play
.venv/bin/pytest                 # tests
```

Python 3.11 or newer.

## Bug reports

Please [open an issue](https://github.com/Paranoidgrinch/bureaucrats-and-broomsticks-v2/issues/new) with the
class you played, what happened and any error message shown.

## License

[PolyForm Noncommercial 1.0.0](LICENSE). Noncommercial use with attribution is permitted; commercial use
requires permission.
