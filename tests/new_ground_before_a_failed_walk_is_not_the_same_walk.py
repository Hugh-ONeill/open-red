#!/usr/bin/env python3
"""New ground before a failed walk is not the same walk (run 19, 2026-09-29).

Inside Rock Tunnel, "come out onto the far part of Route 10, then Lavender"
was refused five rounds as the same walk ("every step before it is only
travel"), because the last plan had failed walking to Lavender from
Cerulean. A step onto a part never stood on (new_part, frozen to not_area),
or a map never stood on other than the failed places, now counts as doing
something first.

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


G = "Reach Lavender Town"
d = Path(tempfile.mkdtemp(prefix="sameground_"))
(d / "run").mkdir()
(d / "run/explored.json").write_text(json.dumps({"visits": {"ROUTE_10|0,4": 3, "ROCK_TUNNEL_B1F|15,9": 1,
                                                            "CERULEAN_CITY|20,0": 9}}))
(d / "run/executor_log.jsonl").write_text("\n".join(json.dumps(r) for r in [
    {"kind": "plan_start", "goal": G},
    {"kind": "escalate_context", "subgoal": "go", "target": "map:LAVENDER_TOWN"},
    {"kind": "escalate_end", "subgoal": "go", "success": False}]) + "\n")
here = os.getcwd()
os.chdir(d)
try:
    def plan(first):
        return {"subgoals": [{"id": "out", "goal_text": "Come out of the tunnel to the south part of Route 10.",
                              "done_when": first},
                             {"id": "lav", "goal_text": "Reach Lavender.", "done_when": {"map": "LAVENDER_TOWN"}}]}
    ck("a bare walk on known ground is still the same walk",
       A.same_failed_walk_problems(plan({"map": "CERULEAN_CITY"}), G) != [])
    ck("coming out onto a part never stood on first is not",
       A.same_failed_walk_problems(plan({"map": "ROUTE_10", "not_area": ["ROUTE_10|0,4"]}), G) == [])
    ck("...nor is new_part before it is frozen",
       A.same_failed_walk_problems(plan({"new_part": "ROUTE_10"}), G) == [])
    ck("...nor a map never stood on",
       A.same_failed_walk_problems(plan({"map": "ROUTE_8"}), G) == [])
finally:
    os.chdir(here)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
