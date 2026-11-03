#!/usr/bin/env python3
"""Riding a car to a floor files that floor's door into the car.

Run 71, 2026-11-03: the Rocket Hideout car set the party down on B4F at
(22,12), off the doorway, and the page listed B4F's (24,15) as "door, two
tiles wide -> UNKNOWN — never taken from here". The model took it as a new
door, was back in the car, rode to B1F and left the floor it had come down
to find the boss on. The same ride had done the same to B1F's (24,19).

Pinned: after an elevator exit the floor's warp tiles whose destination is
the car map carry an edge back to the car region; the car itself still
learns only the lift ride, no door.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = E.Executor.__new__(E.Executor)
ex.explored = {}
ex.visits = {}
ex._entered_map = {}
ex._cur_target = None
ex.log = lambda *a, **k: None
ex._save_memory = lambda: None
ex._count_visit = lambda r: None
ex._where = lambda o: (f"{(o.get('map') or {}).get('id')}|"
                       f"{'2,1' if 'ELEVATOR' in str((o.get('map') or {}).get('id')) else '22,12'}")

CAR = "ROCKET_HIDEOUT_ELEVATOR"
before = {"map": {"id": CAR, "outdoor": False, "lift_floors": ["B1F", "B2F", "B4F"],
                  "warps": [{"x": 2, "y": 1, "dest": "ROCKET_HIDEOUT_B1F", "look": "door"}]},
          "player": {"x": 2, "y": 1}}
after = {"map": {"id": "ROCKET_HIDEOUT_B4F", "outdoor": False,
                 "warps": [{"x": 24, "y": 15, "dest": CAR, "look": "door"},
                           {"x": 25, "y": 15, "dest": CAR, "look": "door"},
                           {"x": 19, "y": 10, "dest": "ROCKET_HIDEOUT_B3F",
                            "look": "stairs_up"}]},
         "player": {"x": 22, "y": 12}}
src, dst = f"{CAR}|2,1", "ROCKET_HIDEOUT_B4F|22,12"
ex.note_transition(before, {"op": "elevator", "floor": "B4F"}, after)

floor = ex.explored.get(dst, {})
car = ex.explored.get(src, {})
ck("the car learns the ride to B4F",
   car.get("lift:ROCKET_HIDEOUT_B4F", {}).get("to") == dst, car)
ck("B4F's door into the car leads back to the car",
   floor.get("24,15", {}).get("to") == src, floor)
ck("...both tiles of it", floor.get("25,15", {}).get("to") == src, floor)
ck("the stairs, never taken, stay unknown", "19,10" not in floor, floor)
ck("the car still has no door edge", not any("," in k for k in car), car)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
