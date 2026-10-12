#!/usr/bin/env python3
"""A flag that has already fired, or standing on a cell, is not a deed that
unlocks a refused walk.

Run 53 (2026-10-12): "every party member is at least level 40" failed walking
to ROUTE_17 (the Cycling Road gate turns walkers back). Its rewrite put
"travel_to_route_16_south: player_at (26,10)" and "wake_snorlax: flag
EVENT_BEAT_ROUTE16_SNORLAX" in front of the same walk, with that flag fired
the plan before, and both passed as doing something first. On the run's own
log cut to the rewrite, the old code accepts that plan and this code refuses it.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


run = Path(tempfile.mkdtemp())
(run / "obs.json").write_text(json.dumps({"flags": ["EVENT_BEAT_ROUTE16_SNORLAX"]}))
A._failed_walk_places = lambda goal, run: [("travel_to_route_17", "ROUTE_17")]
A.untried_leads = lambda *a, **k: []
G = "every party member is at least level 40"

v1 = {"subgoals": [
    {"id": "heal_at_celadon_center",
     "done_when": {"area": "CELADON_POKECENTER|0,3", "party_healthy": True}},
    {"id": "travel_to_route_16_south",
     "done_when": {"player_at": {"x": 26, "y": 10, "radius": 2}}},
    {"id": "wake_snorlax", "done_when": {"flag": "EVENT_BEAT_ROUTE16_SNORLAX"}},
    {"id": "travel_to_route_17", "done_when": {"map": "ROUTE_17"}},
    {"id": "grind_eevee_40", "done_when": {"slot_level": {"slot": 6, "min": 40}}}]}
r = A.same_failed_walk_problems(v1, goal=G, run=run)
ck("run 53's rewrite (a cell, then a fired flag, then the same walk) is refused",
   r and "this is the same walk" in r[0] and "travel_to_route_17" in r[0], r)
ck("...and the refusal says a flag already fired does not count",
   r and "a flag that has already fired does not" in r[0], r)

cell = {"subgoals": [v1["subgoals"][1], v1["subgoals"][3]]}
ck("standing on a cell alone is travel",
   A.same_failed_walk_problems(cell, goal=G, run=run) != [])

fresh = {"subgoals": [{"id": "wake", "done_when": {"flag": "EVENT_BEAT_ROUTE12_SNORLAX"}},
                      v1["subgoals"][3]]}
ck("a flag not yet fired is still a deed that lets the walk follow",
   A.same_failed_walk_problems(fresh, goal=G, run=run) == [])

empty = Path(tempfile.mkdtemp())
ck("with no observation to read, a flag step is a deed as before",
   A.same_failed_walk_problems({"subgoals": [v1["subgoals"][2], v1["subgoals"][3]]},
                               goal=G, run=empty) == [])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
