#!/usr/bin/env python3
"""A door a sweep walked through is an arrival, and the far side's door is
the door you came in by.

The run of record on 2026-09-24, leg 4: a sweep on Route 2 walked into the
Viridian Forest south gate. The shim read the door's fade as "interrupted
(battle or script) on the way to (3,43)", no door was named, and the
recorder returned without a word: no edge, and no arrival either. The
gate's page then offered "door (4,7), two tiles wide, on the room's south
wall -> UNKNOWN — never taken from here", the model wrote "I will now use
the north exit to enter Viridian Forest", took it, and walked back out onto
Route 2, ending the attempt (user watching).

Pinned: a crossing with no door to file still sets the arrival (the door
you came in by, where you came from, the far side written as the way
back); a sweep that stopped on the way to a doorway whose own table sends
it where it landed files that door; a target that is not a doorway, or
one that leads somewhere else, files nothing; the page's came-in-by test
then reads either tile of the gate's door as the door you came in by.
Synthetic."""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
import ledger as LG  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def ex():
    e = E.Executor.__new__(E.Executor)
    e.logf = io.StringIO()
    e.t0 = time.time()
    e.explored = {}
    e._entered_map = {}
    e._cur_target = "map:VIRIDIAN_FOREST"
    e._arrived = ("ROUTE_2|3,43", (8, 71))
    e._came_from = "VIRIDIAN_CITY|17,0"
    e._reversals = 0
    e.door_dests = {}
    e._faint_at = None
    e.blockers = {}
    e._where = lambda o: f"{o['map']['id']}|{o['_region']}"
    e._count_visit = lambda r: None
    e._save_memory = lambda: None
    e._twin_keys = lambda o, s: []
    return e


ROUTE_2 = {"map": {"id": "ROUTE_2", "outdoor": True, "warps": [
    {"x": 3, "y": 43, "dest": "VIRIDIAN_FOREST_SOUTH_GATE"},
    {"x": 3, "y": 11, "dest": "VIRIDIAN_FOREST_NORTH_GATE"}]},
    "_region": "3,43", "player": {"x": 3, "y": 44}}
GATE = {"map": {"id": "VIRIDIAN_FOREST_SOUTH_GATE", "outdoor": False, "warps": [
    {"x": 4, "y": 0, "dest": "VIRIDIAN_FOREST"},
    {"x": 5, "y": 0, "dest": "VIRIDIAN_FOREST"},
    {"x": 4, "y": 7, "dest": "ROUTE_2"},
    {"x": 5, "y": 7, "dest": "ROUTE_2"}]},
    "_region": "5,0", "player": {"x": 5, "y": 7}}
SWEEP = {"op": "sweep", "until": "map_change"}

# ------------------------------------------------ no door named: still an arrival
e = ex()
e.note_transition(ROUTE_2, dict(SWEEP), GATE)
ck("a crossing with no door to file still sets where you arrived",
   e._arrived == ("VIRIDIAN_FOREST_SOUTH_GATE|5,0", (5, 7))
   and e._came_from == "ROUTE_2|3,43", (e._arrived, e._came_from))
ck("...and writes the far side of the door as the way back",
   (e.explored.get("VIRIDIAN_FOREST_SOUTH_GATE|5,0") or {}).get("5,7", {}).get("to")
   == "ROUTE_2|3,43", e.explored)
ck("...but files no edge on the floor it left",
   "ROUTE_2|3,43" not in e.explored, e.explored)
ck("...and says so in the journal", "crossed_door_unnamed" in e.logf.getvalue())
for tile in ((4, 7), (5, 7)):
    ck(f"the page reads the gate's ({tile[0]},{tile[1]}) as the door you came in by",
       LG._came_in_by(e, GATE, "VIRIDIAN_FOREST_SOUTH_GATE|5,0",
                      f"{tile[0]},{tile[1]}", "ROUTE_2"))
ck("...and the north door as not",
   not LG._came_in_by(e, GATE, "VIRIDIAN_FOREST_SOUTH_GATE|5,0", "4,0",
                      "VIRIDIAN_FOREST"))

# ------------------------------------------------ the sweep's own target
src = (ROOT / "planner/executor.py").read_text()
hook = src[src.index("A DOOR IS A DOOR WHOEVER OPENED IT — and a sweep opens them."):]
hook = hook[:hook.index("self._count_dry_walk(")]
ck("the sweep names the doorway it was walking toward when that fired",
   'r"on the way to \\((\\d+),(\\d+)\\)"' in hook
   and 'str(w.get("dest") or "") == str(_amap)' in hook
   and '_sd["x"], _sd["y"] = _tx, _ty' in hook, hook[-600:])
e = ex()
e.note_transition(ROUTE_2, dict(SWEEP, x=3, y=43), GATE)
ck("...and with the door named the edge is filed on the floor it left",
   (e.explored.get("ROUTE_2|3,43") or {}).get("3,43", {}).get("to")
   == "VIRIDIAN_FOREST_SOUTH_GATE|5,0", e.explored.get("ROUTE_2|3,43"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
