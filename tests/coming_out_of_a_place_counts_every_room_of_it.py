#!/usr/bin/env python3
"""Coming out of a place counts the doors of every room of it.

Run 65, 2026-10-25. Leg 20 ("Reach Rock Tunnel") was rewritten from
Vermilion after a Saffron plan failed at the thirsty guard. The new plan went
UNDERGROUND_PATH_NORTH_SOUTH -> ROUTE_5, and its Route 5 step came out as
{"map": "ROUTE_5", "not_area": ["ROUTE_5|1,0"]}: Route 5 has one part, and
the run had stood on it, so the step could never hold. Two checks read only
the corridor's own doors. No door of the corridor opens onto Route 5 (its
Route 5 room's does), so the exit rule said the run had never come out onto
Route 5, and the printed-map hint asked "if that is a part of ROUTE_5 you
have never stood on, write new_part", which froze to excluding the only part.

Pinned: rooms reached by walked doors from the corridor, never crossing a
road, are the same place, so the printed-map hint says where the run has
already come out and offers new_part only for a road it has not; and a plan
that goes in from a road that is neither the exit's map nor its neighbor is
not refused for ending on {"map": "ROUTE_5"}, while one that goes in from
Route 5 still is.
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

EXPLORED = {
    "ROUTE_5|1,0": {"north": {"to": "CERULEAN_CITY|26,7", "n": 0},
                    "17,27": {"to": "UNDERGROUND_PATH_ROUTE_5|3,7", "n": 1}},
    "UNDERGROUND_PATH_ROUTE_5|3,7": {"3,7": {"to": "ROUTE_5|1,0", "n": 0},
                                     "4,4": {"to": "UNDERGROUND_PATH_NORTH_SOUTH|2,3", "n": 1}},
    "UNDERGROUND_PATH_NORTH_SOUTH|2,3": {"5,4": {"to": "UNDERGROUND_PATH_ROUTE_5|1,1", "n": 1},
                                         "2,41": {"to": "UNDERGROUND_PATH_ROUTE_6|1,1", "n": 1}},
    "UNDERGROUND_PATH_ROUTE_5|1,1": {"4,4": {"to": "UNDERGROUND_PATH_NORTH_SOUTH|2,3", "n": 0},
                                     "3,7": {"to": "ROUTE_5|1,0", "n": 1}},
    "CERULEAN_CITY|26,7": {"south": {"to": "ROUTE_5|1,0", "n": 1}},
}
STOOD = {"ROUTE_5|1,0", "CERULEAN_CITY|26,7", "UNDERGROUND_PATH_ROUTE_5|3,7",
         "UNDERGROUND_PATH_ROUTE_5|1,1", "UNDERGROUND_PATH_NORTH_SOUTH|2,3",
         "VERMILION_CITY|0,0", "ROUTE_6|0,0"}

tmp = tempfile.mkdtemp(dir=os.environ.get("RED_BRIDGE_DIR") or None)
(Path(tmp) / "run").mkdir()
(Path(tmp) / "run" / "explored.json").write_text(json.dumps({"explored": EXPLORED}))
os.chdir(tmp)
A.visited_regions = lambda: set(STOOD)
A.holding_town_map = lambda: True
A._map_now = lambda *a, **k: "VERMILION_CITY"
A._region_now = lambda *a, **k: "VERMILION_CITY|0,0"

ls = A._walked_landings("UNDERGROUND_PATH_NORTH_SOUTH", "ROUTE_5", STOOD)
ck("the corridor's Route 5 room is the corridor: the run has come out onto ROUTE_5|1,0",
   [p for p, _d, _r in ls] == ["ROUTE_5|1,0"]
   and ls[0][2] == "UNDERGROUND_PATH_ROUTE_5", ls)
ck("...while the near-door guard still reads the corridor's own doors only",
   not A._walked_door_from_into("UNDERGROUND_PATH_NORTH_SOUTH", "ROUTE_5", STOOD))
ck("a road is never part of the place: nothing past Route 5 is reached through it",
   A._walked_landings("UNDERGROUND_PATH_NORTH_SOUTH", "CERULEAN_CITY", STOOD) == [])
ck("a road it has never come out onto has no landing",
   A._walked_landings("UNDERGROUND_PATH_NORTH_SOUTH", "ROUTE_6", STOOD) == [])

def plan(m, text, dw=None):
    return {"goal": "Reach Rock Tunnel", "subgoals": [
        {"id": "enter_underground_path", "goal_text": "Enter the Underground Path",
         "done_when": {"map": "UNDERGROUND_PATH_NORTH_SOUTH"}},
        {"id": "exit_underground", "goal_text": text, "done_when": dw or {"map": m}},
        {"id": "reach_cerulean_city", "goal_text": "Walk north to Cerulean City",
         "done_when": {"map": "CERULEAN_CITY"}}]}

pin = [p for p in A.validate(plan("SAFFRON_CITY", "Traverse the Underground Path and exit onto Saffron City"))
       if "exit_underground" in p and "printed map pins" in p]
ck("coming out onto Saffron is refused by the printed map", len(pin) == 1, pin)
ck("...and says where the run has already come out, as a map step",
   pin and "You have come out of it onto ROUTE_5 before, onto ROUTE_5|1,0" in pin[0]
   and '{"map": "ROUTE_5"}' in pin[0], pin)
ck("...offering new_part only for the road it has never come out onto",
   pin and '{"new_part": "ROUTE_6"}' in pin[0] and '{"new_part": "ROUTE_5"}' not in pin[0], pin)

out = [p for p in A.validate(plan("ROUTE_5", "Traverse the Underground Path and exit onto Route 5"))
       if "exit_underground" in p]
ck("ending on {\"map\": \"ROUTE_5\"} out of the corridor, gone into from Route 6, is not refused",
   out == [], out)

p5 = plan("ROUTE_5", "Traverse the Underground Path and exit onto Route 5")
p5["subgoals"].insert(0, {"id": "reach_route_5", "goal_text": "Walk to Route 5",
                          "done_when": {"map": "ROUTE_5"}})
back = [p for p in A.validate(p5) if "exit_underground" in p and "comes OUT" in p]
ck("...but gone into FROM Route 5, coming back out onto it is still refused", len(back) == 1, back)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:500]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
