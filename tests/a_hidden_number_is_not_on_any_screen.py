#!/usr/bin/env python3
"""The model's view of an observation carries no number the game never
shows: no DVs, no stat experience, no catch rate.

The save holds all three for every party member and the shim published them
whole, so CURRENT_OBSERVATION handed the model a Pokemon's DVs (user,
2026-09-19: "is the pokemons dvs even something we should be giving the bot?
i dont think its directly visible anywhere doesnt it have to get calculated
or something?"). Gen 1's status screen shows level, HP, the four stats,
types, moves and PP, the OT name, the ID number, EXP POINTS and the points
to the next level. It shows no DV, no stat-experience total, no catch rate.

Pinned: the three are stripped from the party and from the box; what the
status screen does show survives; the raw observation keeps them, because
the harness follows a Pokemon by its DVs (slot_of) and that is check-side;
model_view does not mutate what it was given. Synthetic."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


MON = {"species": "PARAS", "nickname": "PARAS", "level": 8, "hp": 23,
       "max_hp": 23, "types": ["BUG", "GRASS"], "status": None,
       "stats": {"attack": 16, "defense": 14, "speed": 11, "special": 13},
       "moves": [{"id": "SCRATCH", "pp": 35, "max_pp": 35, "power": 40,
                  "type": "NORMAL"}],
       "ot": "PIXEL", "otId": 45799, "exp": 512, "exp_next_level": 89,
       "dvs": {"attack": 8, "defense": 5, "hp": 6, "special": 4, "speed": 1},
       "statExp": {"attack": 49573, "hp": 39324},
       "catchRate": 190}
OBS = {"mode": "overworld", "map": {"id": "ROUTE_4"}, "party": [MON],
       "pc_mons": [dict(MON, species="PIDGEY", box=1, index=1)]}

mv = E.model_view(copy.deepcopy(OBS))
seen = mv["party"][0]
for k in ("dvs", "statExp", "catchRate"):
    ck(f"a party member's {k} is not shown", k not in seen, sorted(seen))
    ck(f"...nor a boxed one's {k}", k not in mv["pc_mons"][0])
for k in ("species", "nickname", "level", "hp", "max_hp", "types", "stats",
          "moves", "ot", "otId", "exp", "exp_next_level"):
    ck(f"what the status screen shows survives: {k}", k in seen, sorted(seen))
ck("a move keeps its PP, which the screen shows",
   seen["moves"][0].get("pp") == 35)

raw = copy.deepcopy(OBS)
before = copy.deepcopy(raw)
E.model_view(raw)
ck("model_view does not mutate what it was given", raw == before)
ck("the raw observation keeps them, for the harness's own reading",
   all(k in raw["party"][0] for k in ("dvs", "statExp", "catchRate")))
ck("...which is how a slot check follows its Pokemon",
   E.slot_of({"slot": 1, "who": {"species": "MACHOKE", "dvs": MON["dvs"],
                                 "otId": 45799}},
             [{"species": "LAPRAS", "dvs": {"hp": 1}, "otId": 1},
              {"species": "MACHOKE", "dvs": MON["dvs"], "otId": 45799}]) == 2)
ck("an empty observation is still fine",
   E.model_view({}) == {} and E.model_view(None) == {})
ck("the hidden list is named once",
   E.HIDDEN_MON_FIELDS == ("dvs", "statExp", "catchRate"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
