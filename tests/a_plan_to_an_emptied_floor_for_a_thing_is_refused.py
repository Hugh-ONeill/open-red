#!/usr/bin/env python3
"""A plan that goes to a floor walked to its end and ends on holding a thing
not found there is refused, as the sentence rungs already were.

Run 67, 2026-10-28: leg 53 "Obtain the Secret Key from the Celadon Game
Corner" was planned as Celadon -> ROCKET_HIDEOUT_B1F -> B4F -> has_item
SECRET_KEY, with every part of B4F on screen and all of it pressed or
taken; names_an_emptied_floor said so of a sentence, and no plan was asked.

Pinned: refused naming the floor; a floor with something untouched stands;
coins are not asked. Synthetic, on a temp record.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

def plan(want):
    return {"goal": "Obtain the Secret Key", "subgoals": [
        {"id": "b1f", "goal": "Enter the hideout", "done_when": {"map": "ROCKET_HIDEOUT_B1F"}},
        {"id": "b4f", "goal": "Reach the bottom", "done_when": {"map": "ROCKET_HIDEOUT_B4F"}},
        {"id": "get", "goal": "Take it", "done_when": {"has_item": want}}]}

def hits(p):
    return [x for x in A.validate(p) if "walked to the end" in x]

REC = {"visits": {"ROCKET_HIDEOUT_B4F|17,1": 3}, "frontier_here": {"ROCKET_HIDEOUT_B4F|17,1": 0},
       "sightings": {"ROCKET_HIDEOUT_B4F|17,1": ["ITEM_ROCKET_HIDEOUT_B4F_10_12"]},
       "touched": {"ROCKET_HIDEOUT_B4F|17,1": ["ITEM_ROCKET_HIDEOUT_B4F_10_12"]}}
d = Path(tempfile.mkdtemp(prefix="emptied_"))
(d / "run").mkdir()
here = os.getcwd()
os.chdir(d)
try:
    (d / "run/explored.json").write_text(json.dumps(REC))
    probe = A.names_an_emptied_floor("Retrieve the Secret Key from Rocket Hideout B4F")
    ck("the record reads as a floor walked to its end", probe, probe)
    h = hits(plan({"SECRET_KEY": 1}))
    ck("a plan ending on SECRET_KEY there is refused",
       h and "ROCKET_HIDEOUT_B4F" in h[0] and "SECRET_KEY" in h[0], h)
    ck("...coins are not asked", hits(plan({"COIN": 50})) == [])
    REC["sightings"]["ROCKET_HIDEOUT_B4F|17,1"].append("ROCKETHIDEOUTB4F_GIOVANNI")
    (d / "run/explored.json").write_text(json.dumps(REC))
    ck("a floor with something untouched stands", hits(plan({"SECRET_KEY": 1})) == [])
finally:
    os.chdir(here)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
