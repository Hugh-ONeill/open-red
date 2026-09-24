#!/usr/bin/env python3
"""The question that produces the party's type legs names no type as its
example, lists the fifteen in alphabetical order, and says what an "or"
means to the checker.

2026-09-24, the user: "whats with all the water catch legs? ... its
particularly dreadful since it satisfies all those catch goals by picking
squirt at the start which would prevent any of the non-water types from
being caught". Over eight outlines, WATER stood in 17 of 44 type legs,
more than any other type, with "WATER, FLYING, GHOST, GROUND and the rest"
as the prompt's type list and "a WATER type in the party" as its worked
example. The starter question then counts those legs, and Squirtle won
three rolls in a row.

MEASURED, the upkeep pass alone, four passes each on the same story legs:
old wording 25 type legs, 13 naming WATER (next type 6), 18 "or" pairs;
neutral wording 24 type legs, 9 naming WATER, GRASS also 9, "FIGHTING or
GRASS" before Brock in all four, 18 "or" pairs. The anchor was ours; the
"or" habit is the model's and is left to it, told only what an "or" is
worth to the checker.

Pinned: no type stands as the example; the fifteen are listed once, in
alphabetical order, so none leads; the "or" sentence is there; nothing
says which type to want. Synthetic."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


S = A.OUTLINE_UPKEEP_SYS
TYPES = ["BUG", "DRAGON", "ELECTRIC", "FIGHTING", "FIRE", "FLYING", "GHOST",
         "GRASS", "GROUND", "ICE", "NORMAL", "POISON", "PSYCHIC", "ROCK", "WATER"]
flat = " ".join(S.split())
ck("the fifteen types are listed once, in alphabetical order",
   ", ".join(TYPES) in flat)
ck("...so no type leads the list", "WATER, FLYING, GHOST, GROUND" not in flat)
ck("no type stands as the worked example",
   "a WATER type in the party" not in flat
   and not re.search(r'"(?:a|an) (?:%s) type' % "|".join(TYPES), flat))
ck("each type is named exactly once, in that list",
   all(len(re.findall(r"\b%s\b" % t, S)) == 1 for t in TYPES),
   {t: len(re.findall(r"\b%s\b" % t, S)) for t in TYPES})
ck("the question says what an 'or' is worth to the checker",
   'an "or" counts as done the moment EITHER is held' in flat)
ck("...and still lets one be written", 'two joined by "or" when either would do' in flat)
ck("nothing says which type to want",
   not re.search(r"\b(should|best|recommend|prefer)\b.{0,40}\btype\b", flat, re.I))
ck("the level and species examples remain",
   '"Every party member at least level 12"' in flat
   and '"catch a PIDGEY or a RATTATA"' in flat)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
