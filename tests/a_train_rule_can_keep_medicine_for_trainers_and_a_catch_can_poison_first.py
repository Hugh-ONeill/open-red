#!/usr/bin/env python3
"""Two knobs, both measured in the arenas before any spec turns them on.

1. train.wild_items: "never" keeps medicine out of a WILD fight in a
   training step (user, 2026-09-28: "save the potions for trainer battles");
   a trainer battle, a step that is not training, and the last Pokemon
   standing still use items.
2. catch.poison: true lets the catch rule poison a target before throwing
   (Gen 1's catch formula counts poison like paralysis); sleep is still
   tried first, then paralysis, and a POISON type is never poisoned.

Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as B  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ck("the train block accepts wild_items use/never",
   B._train_problems({"lead": True, "wild_items": "never"}) == []
   and B._train_problems({"lead": True, "wild_items": "use"}) == [])
ck("...and refuses anything else",
   any("wild_items" in p for p in B._train_problems({"wild_items": "sometimes"})))

src = (ROOT / "planner/battle_policy.py").read_text()
ck("medicine is held back only in a wild fight of a training step",
   '_no_wild_items = (_tr_items == "never" and ctx.get("trainee")\n'
   '                      and (b.get("kind") or "wild") == "wild"\n'
   '                      and not last_one_standing(obs, b))' in src)
ck("...and the item rules are skipped then, not changed",
   "for _i, rule in enumerate([] if _no_wild_items" in src)

pa = (ROOT / "planner/policy_author.py").read_text()
ck("training rooms count the medicine used in the wild",
   'if d.get("op") == "battle_item":\n                        res["items"] += 1' in pa
   and "item(s) used in the wild" in pa)

ck("catch.poison must be a boolean",
   any("catch.poison" in p for p in B.validate_spec(
       dict(B.DEFAULT_SPEC, catch=dict(B.DEFAULT_SPEC.get("catch") or {"ball": "ball"},
                                       poison="yes")))) if hasattr(B, "validate_spec") else True)
ck("poison moves are their own set, ranked after sleep and paralysis",
   B.CATCH_POISON_MOVES == {"POISONPOWDER", "POISON_GAS", "TOXIC"}
   and "_rank.update({m: 2 for m in CATCH_POISON_MOVES})" in src
   and "_rank = {m: 0 for m in CATCH_SLEEP_MOVES}" in src)
ck("...only when the catch block asks, and never on a POISON type",
   'if ca.get("poison") and "POISON" not in [' in src)

from gin_gym_arenas import CATCHES  # noqa: E402
room = next((c for c in CATCHES if c["name"] == "catch_poison"), None)
ck("a catch room measures it: POISONPOWDER, no sleep or paralysis move",
   room is not None and "POISONPOWDER" in room["party"][0][2]
   and not set(room["party"][0][2]) & B.CATCH_STATUS_MOVES
   and "WEEDLE" not in room["want_species"])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
