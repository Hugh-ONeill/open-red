#!/usr/bin/env python3
"""A wild that answers a LATER objective on the outline is thrown at now,
while the bag holds balls above the reserve and the party has room.

The outline carries the party's future as states in the model's own
words ("the party holds a GRASS or ELECTRIC type" before Misty), and each
began only when its turn came — by which point the Forest's PIKACHU was
two towns behind and Route 24 offered an ODDISH instead. Run 18's leg 5
ground Routes 1, 2, 22 and the Forest for a WATER or GRASS type that none
of them has (user, 2026-09-16: "opportunistic catching where encounters
trigger a catch if it can fill a future catch goal").

Pinned here:
  * outline_ahead reads only the legs past the run's mark, and only the
    ones a ball answers: a type with the word "type", or a species the
    game knows. Levels, moves, badges and "at least N Pokemon" are not
    catch goals.
  * a goal the party in hand already meets is not a goal.
  * _catch_ahead switches a traversal battle to a catch with the union of
    wants and a ball cap of (balls - reserve); it declines a trainer, a
    wild nothing ahead wants, a full party and a bag at the reserve, and
    says why once.
  * a catch leg that already throws at everything, or at this very thing,
    is left alone.
  * battle_policy honours the cap: one ball, then leave it alive.

Synthetic: no game, no model.
"""
from __future__ import annotations

import inspect
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import battle_policy as bp     # noqa: E402
import executor as E           # noqa: E402
import outline_ahead as OA     # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


OUTLINE = """Choose a starter Pokémon
Retrieve the Poké Ball from the Pallet Town resident
the party has at least 2 Pokemon
Reach Pewter City
the party holds a WATER or GRASS type
every party member is at least level 12
Defeat Brock for the Boulder Badge
Traverse Mt. Moon
the party holds a GRASS or ELECTRIC type
Defeat Misty for the Cascade Badge
the party holds a GROUND type
the party holds a FLYING type
Catch a Farfetch'd on Route 12
the party holds a FIRE or PSYCHIC type
a party pokemon knows SURF
Obtain the Fire Stone from the Celadon Department Store
"""

tmp = Path(tempfile.mkdtemp(prefix="catch_ahead_"))
plans, run = tmp / "plans", tmp / "run"
plans.mkdir()
run.mkdir()
(plans / "outline.txt").write_text(OUTLINE)
(run / "outline_leg").write_text("4\n")

live_plans, live_run = E.PLANS, E.RUN
E.PLANS = plans
E.bind_run(run)
SPECIES = E.Executor._species_names()
ck("the game's species list is readable", "PIKACHU" in SPECIES
   and "FARFETCHD" in SPECIES)

# ---- reading the list ---------------------------------------------------
ahead = OA.legs_ahead(plans, run)
ck("only the legs past the mark are ahead",
   ahead and ahead[0] == (5, "the party holds a WATER or GRASS type")
   and len(ahead) == 12)
ck("a type leg names its types",
   OA.goal_of("the party holds a WATER or GRASS type", SPECIES)
   == {"types": {"WATER", "GRASS"}, "species": set()})
ck("a level leg is not a catch goal",
   OA.goal_of("every party member is at least level 12", SPECIES) is None)
ck("a move leg is not a catch goal",
   OA.goal_of("a party pokemon knows SURF", SPECIES) is None)
ck("a badge is not a catch goal",
   OA.goal_of("Defeat Brock for the Boulder Badge", SPECIES) is None)
ck("'at least N Pokemon' is answered by anything and is not a goal",
   OA.goal_of("the party has at least 2 Pokemon", SPECIES) is None)
ck("a species leg names the species, under the game's spelling",
   OA.goal_of("Catch a Farfetch'd on Route 12", SPECIES)
   == {"types": set(), "species": {"FARFETCHD"}})
ck("a stone is not a type",
   OA.goal_of("Obtain the Fire Stone from the Celadon Department Store",
              SPECIES) is None)
ck("a type word without 'type' is not a type goal",
   OA.goal_of("Obtain a Pokemon that resists FIRE", SPECIES) is None)

goals = OA.catch_goals_ahead(plans, run, SPECIES,
                             [{"species": "CHARMANDER", "types": ["FIRE"]}])
legs = [g["leg"] for g in goals]
ck("the goals ahead are the type and species legs past the mark",
   legs == ["the party holds a WATER or GRASS type",
            "the party holds a GRASS or ELECTRIC type",
            "the party holds a GROUND type",
            "the party holds a FLYING type",
            "Catch a Farfetch'd on Route 12"])
ck("a goal the party already meets is not a goal",
   "the party holds a FIRE or PSYCHIC type" not in legs)
ck("positions are the outline's own numbers",
   goals[0]["pos"] == 5 and goals[1]["pos"] == 9)
ck("a PIKACHU answers the GRASS-or-ELECTRIC leg and nothing else",
   [g["leg"] for g in OA.goals_met_by(goals, "PIKACHU", ["ELECTRIC"])]
   == ["the party holds a GRASS or ELECTRIC type"])
ck("an ODDISH answers two legs",
   len(OA.goals_met_by(goals, "ODDISH", ["GRASS", "POISON"])) == 2)
ck("a FARFETCHD answers by species and by type",
   [g["leg"] for g in OA.goals_met_by(goals, "FARFETCHD",
                                      ["NORMAL", "FLYING"])]
   == ["the party holds a FLYING type", "Catch a Farfetch'd on Route 12"])


# ---- the decision -------------------------------------------------------
def fresh():
    ex = object.__new__(E.Executor)
    ex.logged = []
    ex.log = lambda kind, **kw: ex.logged.append((kind, kw))
    return ex


def obs(foe="PIKACHU", types=("ELECTRIC",), kind="wild", balls=12,
        party=None, level=5):
    party = party if party is not None else [
        {"species": "CHARMANDER", "level": 9, "types": ["FIRE"], "hp": 28}]
    return {"mode": "battle",
            "battle": {"kind": kind,
                       "foe": {"species": foe, "level": level,
                               "types": list(types), "hp": 20},
                       "me": {"species": "CHARMANDER", "level": 9,
                              "hp": 28, "maxhp": 28, "moves": []}},
            "party": party,
            "bag": {"POKE_BALL": balls, "POTION": 1}}


SG = {"id": "go_to_pewter", "goal_text": "Walk to Pewter City",
      "done_when": {"map": "PEWTER_CITY"}}

ex = fresh()
got = ex._catch_ahead(obs(), SG, "traversal", None)
ck("a PIKACHU on a walking leg becomes a catch",
   got and "ELECTRIC" in got["want"]["types"] and got["cap"] == 10)
ck("the want carries the species the goals name too",
   got and got["want"]["species"] == set())
ck("the switch is logged with the leg it serves",
   ex.logged and ex.logged[-1][0] == "catch_ahead"
   and ex.logged[-1][1]["legs"]
   == ["9. the party holds a GRASS or ELECTRIC type"]
   and ex.logged[-1][1]["balls"] == 12 and ex.logged[-1][1]["cap"] == 10)

ex = fresh()
ck("a WEEDLE that nothing ahead wants is left to the walking policy",
   ex._catch_ahead(obs("WEEDLE", ("BUG", "POISON")), SG, "traversal", None)
   is None and not ex.logged)
ck("a trainer's PIKACHU is not a catch",
   fresh()._catch_ahead(obs(kind="trainer"), SG, "traversal", None) is None)
ck("the tower's GHOST is not a catch",
   fresh()._catch_ahead({**obs("GHOST", ()), "battle": {
       **obs("GHOST", ())["battle"], "ghost": True}}, SG, "traversal", None)
   is None)

ex = fresh()
r1 = ex._catch_ahead(obs(balls=2), SG, "traversal", None)
r2 = ex._catch_ahead(obs(balls=2), SG, "traversal", None)
ck("a bag at the reserve does not throw",
   r1 is None and r2 is None)
ck("...and says so once, with the numbers",
   [k for k, _ in ex.logged] == ["catch_ahead_skipped"]
   and ex.logged[0][1]["why"] == "reserve"
   and ex.logged[0][1]["balls"] == 2 and ex.logged[0][1]["reserve"] == 2)
ck("one ball above the reserve is one throw",
   (fresh()._catch_ahead(obs(balls=3), SG, "traversal", None) or {})
   .get("cap") == 1)

ex = fresh()
six = [{"species": s, "types": ["NORMAL"]} for s in
       ("RATTATA", "RATTATA", "RATTATA", "RATTATA", "RATTATA", "RATTATA")]
ck("a full party sends a catch to the box, so none is made",
   ex._catch_ahead(obs(party=six), SG, "traversal", None) is None
   and ex.logged[0][1]["why"] == "party_full")

ck("a catch leg that takes anything is left alone",
   fresh()._catch_ahead(obs(), {"id": "catch_backup",
                                "done_when": {"party_size": 3}},
                        "catch", None) is None)
ck("a catch leg already after this very thing is left alone",
   fresh()._catch_ahead(obs(), SG, "catch", {"species": set(),
                                             "types": {"ELECTRIC"}}) is None)
got = fresh()._catch_ahead(obs(), SG, "catch",
                           {"species": set(), "types": {"WATER", "GRASS"}})
ck("a catch leg for something else takes the union",
   got and got["want"]["types"] == {"WATER", "GRASS", "ELECTRIC"})
ck("a PIDGEY with a FLYING type already in hand is nothing",
   fresh()._catch_ahead(
       obs("PIDGEY", ("NORMAL", "FLYING"),
           party=[{"species": "SPEAROW", "types": ["NORMAL", "FLYING"]}]),
       SG, "traversal", None) is None)

# ---- the policy honours the cap -----------------------------------------
ck("every battle policy accepts the cap",
   all("ball_cap" in inspect.signature(f).parameters
       for f in E.BATTLE_POLICIES.values()))
ck("the runner carries it",
   "ball_cap" in inspect.signature(E._run_policy).parameters)

SPEC = {"catch": {"ball": "ball", "throw_at_hp_frac": 0.2, "max_balls": 5}}
BOBS = {"mode": "battle",
        "battle": {"kind": "wild",
                   "foe": {"species": "PIKACHU", "level": 5, "hp": 20,
                           "maxhp": 20, "types": ["ELECTRIC"]},
                   "me": {"species": "CHARMANDER", "level": 9, "hp": 28,
                          "maxhp": 28, "types": ["FIRE"],
                          "moves": [{"index": 1, "id": "SCRATCH", "pp": 30,
                                     "type": "NORMAL", "power": 40}]}},
        "party": [{"species": "CHARMANDER", "level": 9, "hp": 28,
                   "max_hp": 28, "types": ["FIRE"]}],
        "bag": {"POKE_BALL": 12}}
ctx = {"turn": 1, "intent": "catch", "want": {"species": set(),
                                               "types": {"ELECTRIC"}},
       "ball_cap": 1, "journal": {}}
first = bp.choose(BOBS, SPEC, ctx)
second = bp.choose(BOBS, SPEC, ctx)
ck("the first ball goes", first.get("op") == "throw_ball")
ck("the cap stops the second and leaves it alive",
   second.get("op") == "battle_run"
   and "out of balls" in str(second.get("_why") or ""))
ctx2 = {"turn": 1, "intent": "catch", "want": {"species": set(),
                                                "types": {"ELECTRIC"}},
        "journal": {}}
bp.choose(BOBS, SPEC, ctx2)
ck("without a cap the spec's own count rules",
   bp.choose(BOBS, SPEC, ctx2).get("op") == "throw_ball")

E.PLANS = live_plans
E.bind_run(live_run)
failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
