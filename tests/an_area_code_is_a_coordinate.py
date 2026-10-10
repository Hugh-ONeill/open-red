#!/usr/bin/env python3
"""An area code names a part by a coordinate, never by a word.

Leg 7 ended "enter_pewter_gym" on {"area": "PEWTER_CITY|GYM"}. The map was
real, so the plan passed, and the step could never be true: it failed with
the party standing inside the gym (run 44, 2026-10-10). The gym is its own
map, PEWTER_GYM.

Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def plan(dw):
    return {"subgoals": [{"id": "enter_pewter_gym", "goal_text": "Enter the gym",
                          "done_when": dw}]}


def area_probs(dw):
    return [p for p in A.validate(plan(dw)) if "area '" in p]


word = area_probs({"area": "PEWTER_CITY|GYM"})
checks.append(("a word after | is refused", len(word) == 1))
checks.append(("the refusal names the building's own map",
               bool(word) and '{"map": "PEWTER_GYM"}' in word[0]))
checks.append(("a coordinate code passes",
               area_probs({"area": "MT_MOON_B2F|20,5"}) == []))
checks.append(("a code with its gloss still passes",
               area_probs({"area": "ROUTE_20|44,2 (the west part of ROUTE_20)"}) == []))
lab = area_probs({"area": "PALLET_TOWN|lab"})
checks.append(("no map is guessed when none carries the words",
               len(lab) == 1 and '{"map"' not in lab[0]))

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"{len(checks) - len(bad)}/{len(checks)} passed")
sys.exit(1 if bad else 0)
