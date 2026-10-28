#!/usr/bin/env python3
"""A new_map_from condition that no walked door can meet says so.

Run 68, 2026-10-28, leg 8 "Exit Mt. Moon": the step "Walk to the east exit
of Mt. Moon to reach Route 4" froze as {"new_map_from": "MT_MOON_1F",
"not_maps": ["MT_MOON_B1F", "ROUTE_4"]}; every 1F door was walked and led
to one of the two, and the run hunted the floor for a third exit.

Pinned: with every door walked and all in not_maps, the page says no way out
meets it; one door not yet taken, or one leading elsewhere, says nothing
more. Synthetic.
"""
import os, sys, tempfile
from pathlib import Path
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
ex = E.Executor.__new__(E.Executor)
ex.visits = {}
DONE = {"new_map_from": "MT_MOON_1F", "not_maps": ["MT_MOON_B1F", "ROUTE_4"]}
OBS = {"map": {"id": "MT_MOON_1F", "warps": [
    {"x": 14, "y": 35}, {"x": 5, "y": 5}, {"x": 17, "y": 11}]}}
ex.explored = {"MT_MOON_1F|3,2": {"14,35": {"to": "ROUTE_4|4,4"},
                                  "5,5": {"to": "MT_MOON_B1F|1,1"}},
               "MT_MOON_1F|13,17": {"17,11": {"to": "MT_MOON_B1F|2,2"}}}
t = ex._words_vs_condition("Walk to the east exit to reach Route 4.", DONE, OBS)
ck("every door walked and ruled out: said",
   "no way out of MT_MOON_1F meets this condition" in t, t)
del ex.explored["MT_MOON_1F|13,17"]
t = ex._words_vs_condition("Walk to the east exit to reach Route 4.", DONE, OBS)
ck("a door not yet taken: not said", "no way out" not in t, t)
ex.explored["MT_MOON_1F|13,17"] = {"17,11": {"to": "MT_MOON_B2F|2,2"}}
t = ex._words_vs_condition("Walk to the east exit to reach Route 4.", DONE, OBS)
ck("a door leading elsewhere: not said", "no way out" not in t, t)
bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d[-300:]}"))
sys.exit(1 if bad else 0)
