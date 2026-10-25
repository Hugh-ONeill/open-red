#!/usr/bin/env python3
"""A {"new_map_from": X} step is answered mid-leg once X has shown all of
itself and every way out of it leads to ground already stood on.

Run 63 and run 64, 2026-10-24: leg 8/9's reach_mt_moon_exit was
{"new_map_from": "MT_MOON_1F", "not_maps": ["MT_MOON_B1F", "ROUTE_4"]},
written while 1F still had unseen ground; once 1F was fully seen the author's
own shut check held, nothing at run time read it, and each run spent a dozen
rounds walking the ladders and the mouth.

Pinned: the runtime ruled-out check answers such a step from the ledger;
it says nothing while X has ground unseen.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))


def ruled(unseen):
    d = {"map_doors": {"MT_MOON_1F": ["14,35", "15,35", "5,5"]},
         "door_dests": {"MT_MOON_1F": {"14,35": "LAST_MAP", "15,35": "LAST_MAP", "5,5": "MT_MOON_B1F"}},
         "explored": {"MT_MOON_1F|3,2": {"5,5": {"to": "MT_MOON_B1F|1,1"}}},
         "frontier_here": {"MT_MOON_1F|3,2": unseen},
         "visits": {"MT_MOON_1F|3,2": 5, "MT_MOON_B1F|1,1": 2, "ROUTE_4|10,0": 3}}
    p = Path(tempfile.mkdtemp()) / "explored.json"
    p.write_text(json.dumps(d))
    ex = E.Executor.__new__(E.Executor)
    ex.MEMORY = p
    sg = {"id": "reach_mt_moon_exit",
          "done_when": {"new_map_from": "MT_MOON_1F", "not_maps": ["MT_MOON_B1F", "ROUTE_4"]}}
    return ex._new_part_ruled_out(sg, {"mode": "overworld", "map": {"id": "MT_MOON_1F"}})


w = ruled(0)
ck("a walked-out floor answers the step", w and "every way out of MT_MOON_1F" in w
   and "the outdoor map you came in from" in w, w)
ck("...in the run's words, not the author's advice", w and "end the step" not in w, w)
ck("it says nothing while the floor has ground unseen", ruled(34) is None)

# a town with road edges, none walked, is never judged (run 65's Pallet)
d2 = {"map_doors": {"PALLET_TOWN": ["5,5", "13,5", "12,11"]},
      "door_dests": {"PALLET_TOWN": {"5,5": "REDS_HOUSE_1F", "13,5": "BLUES_HOUSE", "12,11": "OAKS_LAB"}},
      "explored": {"PALLET_TOWN|10,0": {"5,5": {"to": "REDS_HOUSE_1F|0,0"}}},
      "frontier_here": {"PALLET_TOWN|10,0": 0},
      "visits": {"PALLET_TOWN|10,0": 5, "REDS_HOUSE_1F|0,0": 2, "BLUES_HOUSE|2,1": 1, "OAKS_LAB|4,1": 3}}
p2 = Path(tempfile.mkdtemp()) / "explored.json"
p2.write_text(json.dumps(d2))
ex2 = E.Executor.__new__(E.Executor)
ex2.MEMORY = p2
ck("a town with road edges nobody has walked is not ruled out",
   ex2._new_part_ruled_out({"id": "go_to_prof_oak_lab", "done_when": {"new_map_from": "PALLET_TOWN"}},
                           {"mode": "overworld", "map": {"id": "PALLET_TOWN"}}) is None)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
