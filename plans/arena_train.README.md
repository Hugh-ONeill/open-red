# The training rooms

Built 2026-09-19 (user: "should we have some kind of training-policy and create a few
training rooms to see if we can promote the best behavior for training").

## What they are for

A step whose goal is a level ("raise this member to L30") paces wild ground, and every
battle it meets is played by the battle policy with no turn-by-turn help. Two tactics
raise a weak member, and each is right in different fights:

- **Switch-feeding.** The trainee leads and goes out on turn one. Experience is shared
  among the Pokemon that took part, so it keeps its share while a strong member
  fights. Right when the trainee would lose.
- **Plowing through.** The trainee just fights. No wasted turn, no split with a member
  that has no use for the experience, no switch-in hit, and so fewer walks to a nurse.
  Right when the trainee wins cleanly.

Until these rooms the harness owned the choice and knew one move: in a `slot_level`
step it switched the trainee **in** on turn one of every wild battle (5,128 times
across the runs), the weak member eating the free hit each time. The policy's `train`
block now decides (`planner/battle_policy.py`, `train_turn`), and these rooms score it.

## The three rooms

| room | ground | trainee | party | what it asks |
|---|---|---|---|---|
| `train_early` | Route 1 grass | PIKACHU L5 to L10 | IVYSAUR 20, PIDGEOTTO 18 | it wins every fight there: plow |
| `train_mid` | Rock Tunnel 1F | ODDISH L13 to L20 | CHARMELEON 28, PIDGEOTTO 26 | takes GEODUDE and ONIX, loses to ZUBAT and MACHOP: per encounter |
| `train_late` | Victory Road 2F, by the Route 23 mouth | MACHOP L24 to L30 | five in the fifties | can take the L22-26 third, must not meet the L36-43 rest; the nurse is far |

Each is a gin save (`run/arena_train_*.lua`, from `planner/gin_gym_arenas.py --only
train_early` and so on) parked on wild ground with every trainer on the map beaten.
The trainee has DVs of its own (8) so the slot check pinned to it follows it when the
policy moves it to the front.

## The score

A trial restores the save, reseeds, and paces the ground through the executor exactly
as a level step would (a `slot_level` condition pinned to the trainee,
`_lead_the_trainee` before each grind, `handle_battle` for every fight) until the
**step budget** is spent, the goal level is reached, or the party blacks out.

- **Steps are the budget**, counted by the shim a cell at a time (`obs.steps_walked`).
- **The walk to the nurse is charged to it.** `heal_walk` is the round trip from the
  start cell to the nearest nurse, counted off the engine's map tables (early 68,
  mid 40, late 134). The trial pays the steps and the shim's `arena_heal` does what
  the nurse does. That op exists only in a game started with `RED_ARENA=1`, which
  only `policy_author.py` sets, for its own isolated game.
- **When the party goes** is the page's decision in a run, so the room uses one plain
  stand-in for every candidate: the trainee has fainted, or three wild battles
  running earned it nothing while somebody is hurt.
- **The room's fraction** is the share of the experience to the goal level the
  trainee earned, each trial capped at 1. Quality (a bonus bounded at a twentieth of
  the room) is steps left over when the goal was reached, how little experience
  landed on members already at the goal, and bodies standing.
- **A blackout ends the trial** where it stands.

Experience that lands on members already at the goal is reported as spilled. It is not
subtracted: in a shared battle it is exactly what the trainee did not get, and the
trainee's own number already shows that.

## Running them

```
# the constant tactics only, as a reading of the rooms
planner/policy_author.py --train-eval --trials 2

# the model writes the rule; every candidate is scored in every room each round
planner/policy_author.py --train-block --rounds 4 --trials 2
```

The rule is laid over a base policy (`--base-spec`, default `plans/policy.pin`) and
the winner is written as `plans/train_model_vN.json` with the references it was read
beside. `planner/pick_policy.py --kind train` ranks those files on their own and
refuses one that scored under a constant tactic; `fresh_run.sh` passes the pick to the
executor as `--train-spec` (`RED_TRAIN` for a one-off, `plans/train.pin` to hold a
choice, `none` in either to turn it off). With no train rule the executor trains the
old way.

## First reading (2026-09-19, three trials a room, over v13)

| rule | early | mid | late | of 3.00 |
|---|---|---|---|---|
| no train rule (the old switch-in) | 22% | 19% | 4% | 0.45 |
| always fight | 82% | 35% | 13% | 1.30 |
| always switch out | 47% | 50% | 50% | 1.47 |
| gemma round 2, `train_model_v1.json` | 80% | 79% | 47% | 2.06 |

`train_model_v1.json`: lead the trainee; fight when its level is at least 0.8 of the
wild's, its HP at least 40% and the wild's types hit it for no more than x1.5;
otherwise switch out to the highest level.

Rooms boot the game: never beside a live chain.

## Limits

- The heal walk is charged, not walked, so wild battles met on the way to the nurse
  are not played.
- One stand-in decides when the party goes to the nurse. In a run that is the model's
  call on the page.
- Two trials a room is a small sample; the wild table's rarer, stronger slots move a
  trial a long way. Read a gap of a few points as noise.
