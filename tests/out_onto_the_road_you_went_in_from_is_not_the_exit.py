#!/usr/bin/env python3
"""Coming out of a cave onto the road it was entered from is not the exit.

Run 57, 2026-10-16. "Exit Victory Road" was drafted with its own goal
reworded "Reach Route 23 by exiting Victory Road"; "Reach" made it a travel
objective, so its last step {"map": "ROUTE_23"} was not refused as already
stood on. The exit rule skipped the step because the run had gone into the
cave FROM Route 23 (the S.S. Anne pass, written for a town). And the
far-side finder named ROUTE_23|4,31, the cave's mouth, walk-joined to the
part the run came onto from the Route 22 gate, as "that part IS it". The
plan walked back out the south door and the leg was judged done.

Synthetic ledger shaped on the run's own; run from a temp dir.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


LEDGER = {
    "ROUTE_22_GATE|4,0": {"4,0": {"n": 5, "to": "ROUTE_23|10,104"}},
    "ROUTE_23|10,104": {"7,139": {"n": 16, "to": "ROUTE_22_GATE|4,0"},
                        "walk:ROUTE_23|4,31": {"n": 50, "to": "ROUTE_23|4,31", "intra": True}},
    "ROUTE_23|4,31": {"4,31": {"n": 28, "to": "VICTORY_ROAD_1F|5,9"},
                      "walk:ROUTE_23|10,104": {"n": 46, "to": "ROUTE_23|10,104", "intra": True}},
    "VICTORY_ROAD_1F|5,9": {"8,17": {"n": 45, "to": "ROUTE_23|4,31"},
                            "1,1": {"n": 6, "to": "VICTORY_ROAD_2F|1,5"}},
    "VICTORY_ROAD_2F|1,5": {"1,1": {"n": 6, "to": "VICTORY_ROAD_1F|5,9"},
                            "23,7": {"n": 3, "to": "VICTORY_ROAD_3F|23,7"}},
    "VICTORY_ROAD_3F|23,7": {"23,7": {"n": 3, "to": "VICTORY_ROAD_2F|1,5"}},
}
STEPS = [
    {"id": "ascend_to_3f", "goal_text": "Travel from Victory Road 2F up to 3F.",
     "done_when": {"map": "VICTORY_ROAD_3F"}},
    {"id": "exit_victory_road", "goal_text": "Exit Victory Road and reach Route 23.",
     "done_when": {"map": "ROUTE_23"}},
]


def plan(goal, extra=()):
    return {"goal": goal, "subgoals": json.loads(json.dumps(STEPS)) + list(extra)}


d = Path(tempfile.mkdtemp(prefix="vrexit_"))
(d / "run").mkdir()
(d / "run/explored.json").write_text(json.dumps({
    "explored": LEDGER, "visits": {k: 5 for k in LEDGER}}))
(d / "run/obs.json").write_text(json.dumps({"map": {"id": "VICTORY_ROAD_2F", "region": "1,5"}}))
here = os.getcwd()
os.chdir(d)
try:
    A._region_now = lambda *a, **k: "VICTORY_ROAD_2F|1,5"
    A._map_now = lambda *a, **k: "VICTORY_ROAD_2F"
    A._load_explored = lambda: LEDGER
    ck("the cave's mouth, walk-joined to where the run came on, is not a far side",
       A._came_out_onto("VICTORY_ROAD_3F", "ROUTE_23") == [],
       A._came_out_onto("VICTORY_ROAD_3F", "ROUTE_23"))
    A._AUTHORING_GOAL = "Exit Victory Road"
    probs = A.validate(plan("Reach Route 23 by exiting Victory Road"))
    ck("an Exit objective drafted as 'Reach ...' still ends on a place already stood in",
       any("exit_victory_road" in p and "ALREADY stood in" in p for p in probs), probs)
    ck("...and no refusal calls the near side the far side",
       not any("that part IS it" in p and "ROUTE_23|4,31" in p for p in probs), probs)
    A._AUTHORING_GOAL = "Reach the Indigo Plateau"
    probs = A.validate(plan("Reach the Indigo Plateau", [
        {"id": "walk_north", "goal_text": "Walk north to the Plateau.",
         "done_when": {"map": "INDIGO_PLATEAU"}}]))
    hit = [p for p in probs if "exit_victory_road" in p and "comes OUT" in p]
    ck("a mid-plan exit onto the road the cave was entered from is refused",
       hit, probs)
    ck("...with new_part offered as the repair", hit and '"new_part": "ROUTE_23"' in hit[0], hit)
    A._AUTHORING_GOAL = None
finally:
    os.chdir(here)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
