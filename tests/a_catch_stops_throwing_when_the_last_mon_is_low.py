#!/usr/bin/env python3
"""A catch stops throwing when the last mon standing is too low to take
two more hits, and fights instead.

Run 53, 2026-10-11: a lone BULBASAUR L5 threw three balls at a full-HP
PIDGEY L4 while its own bar went 20 -> 15 -> 10 -> 5, and blacked out on
Route 2. Pinned: at full health it throws; once its bar is at half or
under two of the biggest hits seen this battle it fights; with a second
mon still up it keeps throwing. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as bp  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


TACKLE = {"index": 1, "id": "TACKLE", "type": "NORMAL", "power": 35, "accuracy": 95, "pp": 30}
SPEC = dict(bp.DEFAULT_SPEC, catch={"ball": "ball", "throw_at_hp_frac": 0.3,
                                    "max_balls": 5, "first_ball": False})


def obs(me_hp, party):
    return {"mode": "battle", "bag": {"POKE_BALL": 5}, "party": party,
            "battle": {"kind": "wild", "partyIndex": 0,
                       "me": {"species": "BULBASAUR", "level": 5, "hp": me_hp,
                              "maxhp": 20, "types": ["GRASS", "POISON"],
                              "status": None, "moves": [TACKLE]},
                       "foe": {"species": "PIDGEY", "level": 4, "hp": 17,
                               "maxhp": 17, "types": ["NORMAL", "FLYING"],
                               "status": None}}}


def solo(hp):
    return [{"species": "BULBASAUR", "level": 5, "hp": hp, "max_hp": 20}]


ctx = {"intent": "catch", "probe_done": True}
ops = [bp.choose(obs(hp, solo(hp)), SPEC, ctx)["op"] for hp in (20, 15, 10)]
ck("full health throws, and so does 15 of 20 after a 5 hp hit",
   ops[:2] == ["throw_ball", "throw_ball"], ops)
ck("at half health the last mon fights instead", ops[2] == "battle_move", ops)
ck("...and the catch is over for this battle", ctx.get("intent") == "fight", ctx)

ctx = {"intent": "catch", "probe_done": True}
ops = [bp.choose(obs(hp, solo(hp)), SPEC, ctx)["op"] for hp in (20, 12)]
ck("one 8 hp hit leaves 12, under two of them: it fights",
   ops == ["throw_ball", "battle_move"], ops)

ctx = {"intent": "catch", "probe_done": True}
two = lambda hp: solo(hp) + [{"species": "PIDGEY", "level": 3, "hp": 15, "max_hp": 15}]
ops = [bp.choose(obs(hp, two(hp)), SPEC, ctx)["op"] for hp in (20, 10)]
ck("with a second mon up it keeps throwing", ops == ["throw_ball", "throw_ball"], ops)

bad = [c for c in checks if not c[1]]
for n, ok, d in checks:
    print(("PASS " if ok else "FAIL ") + n + ("" if ok else f"  {d}"))
sys.exit(1 if bad else 0)
