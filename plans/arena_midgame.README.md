# The room arenas

Built 2026-09-12 to sit between the Brock arena and the Elite Four one, so
a battle spec can be scored at the stage it will actually play.

The tiers are the game's own shelves, not a guess: a rule can only fire on
an item the run can buy, and the shops change three times.

| first sold at | what appears | arena |
|---|---|---|
| Pewter | POTION | **`run/arena_brock_gym.lua`** |
| Vermilion | SUPER_POTION | **`run/arena_erika.lua`** |
| Lavender | GREAT_BALL, REVIVE | " |
| Fuchsia | ULTRA_BALL, FULL_HEAL | **`run/arena_koga.lua`** |
| Saffron | HYPER_POTION | " |
| Indigo Plateau lobby | FULL_RESTORE, MAX_POTION | `run/arena_e4.lua` |

Two items a spec may NOT reach for at any tier: **ETHER and MAX_REVIVE are
not sold anywhere in Red.** Both are field-find only. `policy_model_v6`
named MAX_REVIVE, and FULL_RESTORE and MAX_POTION which are sold in exactly
one shop in the game — three of its five battle-item rules could not have
fired however well the run shopped.

## arena_brock_gym — the Potion tier

Added 2026-09-15, so the earliest shelf is a ROOM like the others rather
than a plan replayed from a new game. `--arena brock` still exists and
still works; it boots into the campaign's own `run/` directory, which is
not a thing to do while a checkpoint is sitting in it waiting to resume.

Base: `run/saves/leg_05_defeat_brock_for_the_boulder_badg.20260913-091044`.
Parked at PEWTER_GYM (4,13), Brock and his one trainer unbeaten.

    CHARMANDER L15   NIDORAN_M L12

Bag off Pewter's shelf at what 1,611 affords: POTION x4, ANTIDOTE x1,
POKE_BALL x1. Charmander's only damage against a Rock/Ground ONIX is
SCRATCH, so this is the fight it really is: four Potions and a Nidoran's
HORN_ATTACK. The hand-seeded baseline blacks out here; v1 wins it with one
Pokemon standing.

## arena_erika — the Super Potion tier

Base: `run/saves/leg_20_defeat_erika_for_the_rainbow_badg.20260907-182506`.
Parked at CELADON_GYM (4,17), Erika and all seven gym trainers unbeaten.

    NIDORINA  L29   GLOOM L30   CHARIZARD L37   EEVEE L25

Bag off Celadon Mart 2F's shelf at what 12,882 affords: SUPER_POTION x8,
REVIVE x2, PARLYZ_HEAL x3, GREAT_BALL x5.

The Charizard's only fire move is EMBER, so this is not the free win a
fire party against a grass gym would normally be.

## arena_koga — the Ultra Ball / Full Heal tier

Base: `run/saves/leg_30_reach_fuchsia_city.20260908-121253` — the leg
BEFORE Koga, so no Soul Badge is held and its stat boost is not in play.
Parked at FUCHSIA_GYM (4,17), Koga and all six gym trainers unbeaten.

    NIDORINA L37   GLOOM L34   CHARIZARD L41   EEVEE L25   DODUO L22

Bag off Fuchsia's own shelf at what 12,814 affords: SUPER_POTION x8,
REVIVE x2, FULL_HEAL x3, ULTRA_BALL x1. Two members are far under level,
which is what makes attrition real and item rules worth having.

That base save arrived with two members fainted. They were healed by
DROPPING `hp` and `stats` from the party in the save, which the game
rebuilds at load from species/level/DVs/statExp — so these are the same
mons with the same training, standing up, rather than a fresh party at
default DVs. The derived max HP came back 113/93/135, matching the
original exactly, which is the check that it worked.

## Scoring a room

Done 2026-09-15. `--arena gym` (and the named arenas `pewter`, `erika`,
`koga`) crosses one room and fights everyone in it:

* The roster comes from the ENGINE'S map table, not from the observation —
  a restored save has seen nothing of the room it is parked in, so
  `map.objects` is empty at the door and a scorer reading it presses
  nobody. `interact` resolves a name against the live NPC list, so the
  names are enough.
* Trainers nearest the door come first. Most never need pressing: a
  trainer whose line of sight the walk crosses starts the fight itself.
* When nobody is in reach, the walk goes to the nearest edge of what has
  been seen, so more of the room comes into view.
* When that runs out too, a CUT_TREE is cut. Celadon pens Erika and her
  last three trainers inside a bed with two bushes in it; without the cut
  every trial stopped at 4 of 8 with the leader never fought.
* A prompt is answered `no` — Pewter's gym guide offers to walk you to the
  top, and the trial otherwise sits in that box forever.
* The score is the arena's own beat-flags, from the gin spec's
  `clear_flags`: what the save reset is exactly what is standing. Bodies
  left at the end break ties, and count zero if the trial ended somewhere
  else, because a blackout heals the party and would otherwise score full
  marks for dying.

## One spec, every arena

`--arenas koga,pewter,erika,e4` authors in the first and carries every
candidate to the rest. Each arena's result becomes the fraction of ITS OWN
objective the spec reached, and those fractions add, so a spec that sweeps
the league by dying everywhere else cannot hide behind a number only the
league produces. The winner records every arena in its provenance, and
`pick_policy` takes a spec fit across the game over any stage line.
