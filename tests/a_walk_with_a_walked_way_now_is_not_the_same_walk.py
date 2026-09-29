#!/usr/bin/env python3
"""A walk with a walked way to it now is not the same walk (run 19, 2026-09-29).

Run 19's plans to Celadon failed from Saffron's Route 7 pocket; then the run
crossed Saffron's west edge at (0,17) onto the gate strip and had a walked
way to Celadon again, and both walk refusals went on refusing the walk there,
fifteen rounds, until the ladder pushed the leg. A place the walked graph
now reaches from where the party stands is not counted as a failed walk.

Synthetic.
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


G = "Obtain FRESH WATER from the roof of the Celadon City Department Store"
d = Path(tempfile.mkdtemp(prefix="walkedway_"))
(d / "run").mkdir()
rows = []
for _ in range(2):
    rows += [{"kind": "plan_start", "goal": G},
             {"kind": "escalate_context", "subgoal": "go", "target": "map:CELADON_CITY"},
             {"kind": "escalate_end", "subgoal": "go", "success": False}]
(d / "run/executor_log.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
here = os.getcwd()
os.chdir(d)
try:
    A._region_now = lambda *a, **k: "SAFFRON_CITY|12,0"
    (d / "run/explored.json").write_text(json.dumps({"visits": {"SAFFRON_CITY|12,0": 9, "ROUTE_7|18,12": 4},
        "explored": {"SAFFRON_CITY|12,0": {"west#skip1": {"to": "ROUTE_7|18,12"}}}}))
    ck("no walked way yet: the failed walk still counts",
       A._failed_walk_history(G)[0] == 2 and A._failed_walk_places(G) != [])
    (d / "run/explored.json").write_text(json.dumps({"visits": {"SAFFRON_CITY|12,0": 9, "CELADON_CITY|2,1": 3},
        "explored": {"SAFFRON_CITY|12,0": {"west#skip5": {"to": "ROUTE_7|18,2"}},
                     "ROUTE_7|18,2": {"18,10": {"to": "ROUTE_7_GATE|0,3"}},
                     "ROUTE_7_GATE|0,3": {"0,4": {"to": "ROUTE_7|0,2"}},
                     "ROUTE_7|0,2": {"west": {"to": "CELADON_CITY|2,1"}}}}))
    ck("a walked way there now: it is not the same walk",
       A._failed_walk_places(G) == [] and A._failed_walk_history(G)[0] == 0)
    (d / "run/explored.json").write_text(json.dumps({"visits": {"SAFFRON_CITY|12,0": 9},
        "explored": {"SAFFRON_CITY|12,0": {"west": {"to": "ROUTE_7|18,2", "inferred": True}},
                     "ROUTE_7|18,2": {"18,10": {"to": "ROUTE_7_GATE|0,3"}}}}))
    ck("an inferred edge is not a walked way", A._walked_way_to("ROUTE_7_GATE") is False)
finally:
    os.chdir(here)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
