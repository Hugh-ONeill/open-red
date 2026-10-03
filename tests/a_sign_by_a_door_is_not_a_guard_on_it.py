#!/usr/bin/env python3
"""A sign near a door is not somebody standing on it, and a person eight
cells off is not standing there either.

Run 30, 2026-10-02: the doors note named the nearest reachable OBJECT
within eight cells, signs included, as "(X is standing there)". Pewter's
gym door read "(SIGN_PEWTER_CITY_24_17 is standing there)", the plan
author's held-door rule took it for a posted guard, refused thirty Brock
plans for want of "the deed that moves them", and pushed the badge leg
behind Mt Moon (user: "did it skip brock somehow?").

Pinned: only people are named; "standing there" only within one cell, a
farther person is "nearest person X, N cells off"; the validator ignores a
sign named in an old record. Synthetic: no game.
"""
from __future__ import annotations
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A     # noqa: E402
import executor as E   # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = object.__new__(E.Executor)
ex._where = lambda o: "PEWTER_CITY|4,2"
ex._taken_here = lambda h: {}
ex._door_groups = lambda w: {}

def obs(objs):
    return {"map": {"id": "PEWTER_CITY", "warps": [
        {"x": 16, "y": 17, "dest": "PEWTER_GYM", "reachable": False}],
        "objects": objs}}

got = ex._unopened_doors(obs([{"name": "SIGN_PEWTER_CITY_24_17", "kind": "sign",
                               "x": 24, "y": 17, "reachable": True}]))
ck("a sign is never named at a door", got and got[0][2] is None, got)

got = ex._unopened_doors(obs([{"name": "PEWTERCITY_YOUNGSTER", "kind": "npc",
                               "x": 20, "y": 17, "reachable": True}]))
ck("a person nearby is named, with how far off", got and got[0][2] == "PEWTERCITY_YOUNGSTER"
   and got[0][3] == 4, got)

src = (ROOT / "planner/executor.py").read_text()
ck("'standing there' is written only within one cell",
   "if who and far is not None and far <= 1" in src
   and "nearest person \"\n                            f\"{who}, {far} cells off" in src)

with tempfile.TemporaryDirectory() as td:
    rec = {"visits": {"PEWTER_CITY|4,2": 5},
           "door_dests": {"PEWTER_CITY": {"16,17": "PEWTER_GYM"}},
           "shut_doors": {"PEWTER_CITY|4,2": ["16,17 (SIGN_PEWTER_CITY_24_17 is standing there)"]}}
    p = Path(td) / "explored.json"
    p.write_text(json.dumps(rec))
    plan = {"subgoals": [{"id": "enter_pewter_gym", "done_when": {"map": "PEWTER_GYM"}},
                         {"id": "beat_brock", "done_when": {"badge": "BOULDERBADGE"}}]}
    probs = A.held_step_problems(plan, observed=str(p))
    ck("an old record naming a sign does not hold the door", probs == [], probs)
    rec["shut_doors"]["PEWTER_CITY|4,2"] = ["16,17 (PEWTERGYM_GUARD is standing there)"]
    p.write_text(json.dumps(rec))
    probs = A.held_step_problems(plan, observed=str(p))
    ck("...while a person standing there still does", len(probs) == 1, probs)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
