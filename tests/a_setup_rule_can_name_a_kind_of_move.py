#!/usr/bin/env python3
"""A setup rule can name a CLASS of move ("sleep", "paralyze", "confuse",
"poison", "accuracy_down") and fires with whichever such move the Pokemon in
the fight knows.

v18's rule named SLEEP_POWDER, and run 19's POLIWHIRL knew HYPNOSIS: the rule
could never fire for it (user, 2026-10-01: "thats kind of silly isnt it?").
Resolved from the game's own move effect, like an item class from the bag.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


import battle_policy as B  # noqa: E402


def mv(i, mid, eff, power=0, acc=100, pp=10, cat="status", typ="NORMAL"):
    return {"index": i, "id": mid, "effect": eff, "power": power, "accuracy": acc,
            "pp": pp, "category": cat, "type": typ}


SURF = mv(1, "SURF", "NO_ADDITIONAL_EFFECT", 95, 100, 15, "special", "WATER")
HYP = mv(2, "HYPNOSIS", "SLEEP_EFFECT", 0, 60)
ck("a class finds the move the Pokemon knows", B.setup_move("sleep", [SURF, HYP]) is HYP)
ck("...and the surest of two",
   B.setup_move("sleep", [HYP, mv(3, "SLEEP_POWDER", "SLEEP_EFFECT", 0, 75)])["id"] == "SLEEP_POWDER")
ck("...never a damaging move that only might do it",
   B.setup_move("paralyze", [mv(1, "BODY_SLAM", "PARALYZE_SIDE_EFFECT2", 85)]) is None
   and B.setup_move("paralyze", [mv(1, "X", "PARALYZE_EFFECT", 40)]) is None)
ck("a move name still means that move", B.setup_move("HYPNOSIS", [SURF, HYP]) is HYP
   and B.setup_move("SLEEP_POWDER", [SURF, HYP]) is None)
ck("accuracy_down covers SAND_ATTACK",
   B.setup_move("accuracy_down", [mv(4, "SAND_ATTACK", "ACCURACY_DOWN1_EFFECT")])["id"] == "SAND_ATTACK")

spec = dict(B.DEFAULT_SPEC, setup=[{"move": "sleep", "max_uses": 1, "per_foe": True,
                                    "only_if_foe_clear": True, "vs": "any"}])
ck("a class validates", B.validate_spec(spec) == [], B.validate_spec(spec))
bad = B.validate_spec(dict(B.DEFAULT_SPEC, setup=[{"move": "sleepy"}]))
ck("a lower-case word that is no class is named as such",
   any("a move class is one of" in p for p in bad), bad)

obs = {"mode": "battle", "battle": {"kind": "trainer", "me": {
    "species": "POLIWHIRL", "level": 50, "hp": 150, "max_hp": 150, "types": ["WATER"],
    "moves": [SURF, HYP]}, "foe": {"species": "ONIX", "level": 50, "hp": 100,
                                   "max_hp": 100, "types": ["ROCK", "GROUND"]}}}
ctx = {"turn": 1}
op = B.choose(obs, spec, ctx)
ck("in a fight, the sleep rule fires with HYPNOSIS", op and op.get("index") == 2
   and "HYPNOSIS [sleep]" in str(op.get("_why")), op)
op2 = B.choose(
    {**obs, "battle": {**obs["battle"], "foe": {**obs["battle"]["foe"], "status": "SLP"}}},
    spec, {"turn": 1})
ck("...and not on a foe already asleep (only_if_foe_clear)", op2 and op2.get("index") == 1, op2)

ck("the author is told about move classes", '"sleep", "paralyze"' in B.SETUP_DOC
   and "accuracy_down" in B.SETUP_DOC)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
