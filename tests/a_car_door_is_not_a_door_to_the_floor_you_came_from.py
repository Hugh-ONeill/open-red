#!/usr/bin/env python3
"""Stepping into an elevator car files a lift edge, not a door edge.

Run 66, 2026-10-25: entering the Silph Co. car from 1F filed "(1,3) ->
SILPH_CO_1F|20,0" on the car as the far side of the door just used. The
car's exit goes wherever the panel was last set, so `go` from 5F to the
Saffron Pokemon Center walked into the car and out of (1,3) with no ride,
landed back on 5F, and stopped.

Pinned: arriving in a car writes "lift:<floor you came from>" and no
door-keyed edge; arriving through an ordinary door still writes the door.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

def rig():
    ex = E.Executor.__new__(E.Executor)
    ex.explored = {}
    ex.visits = {}
    ex._entered_map = {}
    ex._cur_target = None
    ex.log = lambda *a, **k: None
    ex._save_memory = lambda: None
    ex._count_visit = lambda r: None
    return ex

CAR = "SILPH_CO_ELEVATOR"
before = {"map": {"id": "SILPH_CO_1F", "outdoor": False}, "player": {"x": 20, "y": 0}}
after = {"map": {"id": CAR, "outdoor": False, "lift_floors": ["1F", "5F"],
                 "warps": [{"x": 1, "y": 3, "dest": "SILPH_CO_1F", "look": "door"}]},
         "player": {"x": 1, "y": 3}}
ex = rig()
ex._note_arrival("SILPH_CO_1F|20,0", f"{CAR}|0,1", before, after)
node = ex.explored.get(f"{CAR}|0,1", {})
ck("entering the car files the floor as a lift ride",
   node.get("lift:SILPH_CO_1F", {}).get("to") == "SILPH_CO_1F|20,0", node)
ck("...and not the car's door as a way to that floor", "1,3" not in node, node)

before = {"map": {"id": "SAFFRON_CITY", "outdoor": True}, "player": {"x": 9, "y": 29}}
after = {"map": {"id": "SAFFRON_POKECENTER", "outdoor": False,
                 "warps": [{"x": 3, "y": 7, "dest": "SAFFRON_CITY", "look": "door"}]},
         "player": {"x": 3, "y": 7}}
ex = rig()
ex._note_arrival("SAFFRON_CITY|12,0", "SAFFRON_POKECENTER|0,3", before, after)
ck("an ordinary door is still filed as the way back",
   ex.explored.get("SAFFRON_POKECENTER|0,3", {}).get("3,7", {}).get("to")
   == "SAFFRON_CITY|12,0", ex.explored)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
