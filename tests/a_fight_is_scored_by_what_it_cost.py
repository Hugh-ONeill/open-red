#!/usr/bin/env python3
"""An arena trial's quality is the damage race and what it spent: most damage
for least HP, PP and medicine (user, 2026-10-01: "hp and pp counts, most
damage for least cost").

The quality bonus was bodies left plus agreement with the move oracle, and
in the league rooms every policy loses: bodies are zero, so the fights were
told apart by nothing that reads inside a loss.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


import policy_author as PA  # noqa: E402

td = Path(tempfile.mkdtemp())
spec = td / "room.json"
spec.write_text(json.dumps({"party": [{"species": "GRAVELER", "level": 50,
                                       "moves": ["EARTHQUAKE", "ROCK_THROW"]}],
                            "bag": {"SUPER_POTION": 4, "POKE_BALL": 5}}))
g = object.__new__(PA.Gym)
g.arena_spec = spec


def turn(op, foe, me):
    return {"kind": "battle_turn", "op": op, "foe_hp": foe, "me_hp": me}


rows = [{"kind": "battle_start"},
        turn("battle_move", 100, 90),
        turn("battle_move", 60, 70),     # dealt 40, took 20
        turn("battle_move", 120, 50),    # a new foe: the 60 one went down; took 20
        turn("pick_party", None, None),  # our member fainted at 50
        turn("battle_move", 80, 120),    # dealt 40; a fresh member, no drop
        turn("battle_switch", 80, 100),  # took 20, then a switch
        turn("battle_move", 80, 140)]    # a switch-in is not damage
res = {}
g._add_cost(res, rows, {"bag": {"SUPER_POTION": 3, "POKE_BALL": 5}})
ck("damage dealt counts drops and each foe that went down", res["dealt"] == 40 + 60 + 40, res)
ck("damage taken counts drops and each member that fainted, not switch-ins",
   res["taken"] == 20 + 20 + 50 + 20, res)
ck("PP used is one a move turn, against the party's PP",
   res["pp_used"] == 5 and res["pp_had"] == 10 + 15, res)
ck("medicine used is what left the bag, of what the room held (balls are not medicine)",
   res["med_used"] == 1 and res["med_had"] == 4, res)

base = {"arena": "e4", "gauntlet_trials": 1, "bodies": 0.0, "rooms": 2}
cheap = dict(base, dealt=900, taken=300, pp_used=20, pp_had=100, med_used=0, med_had=4)
dear = dict(base, dealt=600, taken=600, pp_used=60, pp_had=100, med_used=4, med_had=4)
ck("inside a loss, more damage for less cost scores higher",
   PA.arena_quality(cheap) > PA.arena_quality(dear),
   (PA.arena_quality(cheap), PA.arena_quality(dear)))
ck("...but never outweighs one more room won",
   PA.arena_points(dict(dear, rooms=3)) > PA.arena_points(cheap))
ck("a room with no counts keeps the old reading",
   PA.arena_quality({"arena": "e4", "gauntlet_trials": 1, "bodies": 1.0,
                     "agree": 5, "scored": 10}) == 0.6 + 0.2)
src = (ROOT / "planner/policy_author.py").read_text()
ck("every trial loop adds its cost", src.count("self._add_cost(res, self._log_delta(start), obs)") == 3)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
