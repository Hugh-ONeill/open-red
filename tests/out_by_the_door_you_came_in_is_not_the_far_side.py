#!/usr/bin/env python3
"""Coming back out by the door you went in through is not the far side,
wherever the party stands while the plan is written.

Leg 45, "Clear the boulder puzzle in the Seafoam Islands", was written from
Route 15. Every one of the run's seven trips into Seafoam went in at Route
20 (48,5), landed on 1F (4,17), and came back out by (4,17) onto
ROUTE_20|52,2, which is surf-joined to 44,2. The near-side filter compared
parts with where the party stood (Route 15), matched nothing, and the rule
told the author "that part IS the far side" five rounds running; the model's
own new_part froze into exactly what the rule refused, and the chain stopped
(run 19, 2026-09-29).

Synthetic ledger; run from a temp dir.
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
    "ROUTE_20|44,2": {"48,5": {"n": 7, "to": "SEAFOAM_ISLANDS_1F|3,2", "land": "4,17"},
                      "walk:ROUTE_20|52,2": {"n": 7, "to": "ROUTE_20|52,2", "intra": True}},
    "ROUTE_20|52,2": {"48,5": {"to": "SEAFOAM_ISLANDS_1F|3,2", "n": 0},
                      "walk:ROUTE_20|44,2": {"n": 13, "to": "ROUTE_20|44,2", "intra": True}},
    "SEAFOAM_ISLANDS_1F|3,2": {"4,17": {"to": "ROUTE_20|52,2", "n": 7, "land": "48,6"}},
}
PLAN = {"goal": "Clear the boulder puzzle in the Seafoam Islands", "subgoals": [
    {"id": "go_route_20", "goal_text": "Surf to Route 20", "done_when": {"map": "ROUTE_20"}},
    {"id": "enter_seafoam", "goal_text": "Enter Seafoam Islands", "done_when": {"map": "SEAFOAM_ISLANDS_1F"}},
    {"id": "exit_far_side", "goal_text": "Exit Seafoam to the far side of Route 20",
     "done_when": {"map": "ROUTE_20", "not_area": ["ROUTE_20|44,2", "ROUTE_20|52,2"]}}]}

d = Path(tempfile.mkdtemp(prefix="farside2_"))
(d / "run").mkdir()
(d / "run/explored.json").write_text(json.dumps({
    "explored": LEDGER, "visits": {"ROUTE_20|44,2": 14, "ROUTE_20|52,2": 14,
                                   "SEAFOAM_ISLANDS_1F|3,2": 8, "ROUTE_15|0,0": 40}}))
(d / "run/obs.json").write_text(json.dumps({"map": {"id": "ROUTE_15", "region": "0,0"}}))
here = os.getcwd()
os.chdir(d)
try:
    A._region_now = lambda *a, **k: "ROUTE_15|0,0"
    A._load_explored = lambda: LEDGER
    probs = [p for p in A.validate(json.loads(json.dumps(PLAN))) if "exit_far_side" in p
             and "ALREADY come out of" in p]
    ck("written from Route 15, the part come out onto by the door gone in through is not called the far side",
       not probs, probs)
    far = json.loads(json.dumps(LEDGER))
    far["SEAFOAM_ISLANDS_1F|3,2"] = {"26,17": {"to": "ROUTE_20|52,2", "n": 2, "land": "58,10"}}
    far["ROUTE_20|52,2"] = {}
    A._load_explored = lambda: far
    probs = [p for p in A.validate(json.loads(json.dumps(PLAN))) if "exit_far_side" in p
             and "ALREADY come out of" in p]
    ck("come out by the OTHER door onto an unjoined part: still named as the far side",
       probs and "ROUTE_20|52,2" in probs[0], probs)
finally:
    os.chdir(here)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
