#!/usr/bin/env python3
"""After two failed walks, a plan takes in new ground (run 18, 2026-09-28).

The ticket leg failed walking to Vermilion, and every rewrite reached it by
another road until the ladder pushed the leg, while the one open way was
never crossed (user: "it really loves going back to where it just was but
seems to dislike trying new things"; "we cant just have the harness drive
it"). Nothing is walked for the model and no place is named as the answer:
once two plans for an objective have failed a walk, a plan must include a
step onto a map never stood on (or a new part of one) other than the places
it failed to reach.

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


G = "Retrieve the S.S. Ticket"


def attempt(goal=G):
    return [{"kind": "plan_start", "goal": goal},
            {"kind": "escalate_context", "subgoal": "go", "target": "map:VERMILION_CITY"},
            {"kind": "escalate_end", "subgoal": "go", "success": False}]


def plan(*maps):
    return {"subgoals": [{"id": f"s{i}", "goal_text": "x", "done_when": {"map": m}}
                         for i, m in enumerate(maps)]}


d = Path(tempfile.mkdtemp(prefix="newground_"))
(d / "run").mkdir()
(d / "run/explored.json").write_text(json.dumps({"visits": {"CERULEAN_CITY|20,0": 9, "ROUTE_24|4,4": 5},
                                                 "frontier": {"ROUTE_24|4,4": ["east", "south"]},
                                                 "explored": {"ROUTE_24|4,4": {"south": {"to": "CERULEAN_CITY|20,0"}}}}))
here = os.getcwd()
os.chdir(d)
try:
    def journal(rows):
        (d / "run/executor_log.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    journal(attempt())
    ck("one failed walk: no demand yet", A.new_ground_problems(plan("CERULEAN_CITY"), G) == [])
    journal(attempt() + attempt())
    p = A.new_ground_problems(plan("CERULEAN_CITY", "ROUTE_24"), G)
    ck("two: a plan on walked ground only is refused", p and "has to take in somewhere never stood on" in p[0], p)
    ck("...listing the run's own candidates, Route 24's untaken east side among them",
       p and "ROUTE_24|4,4 (the way east never taken" in p[0], p)
    ck("...and saying the choice is the model's", p and "which, and why, is yours" in p[0])
    ck("a plan through a map never stood on passes, wherever it ends",
       A.new_ground_problems(plan("ROUTE_25", "VERMILION_CITY"), G) == [])
    ck("the failed place itself does not count as new",
       A.new_ground_problems(plan("VERMILION_CITY"), G) != [])
    ck("a new part of a walked map counts",
       A.new_ground_problems({"subgoals": [{"id": "a", "goal_text": "x",
                                            "done_when": {"new_part": "ROUTE_24"}}]}, G) == [])
    journal(attempt() + attempt() + [{"kind": "flag_fired", "flag": "EVENT_GOT_NUGGET"}])
    ck("an event since re-opens it", A.new_ground_problems(plan("CERULEAN_CITY"), G) == [])
    journal(attempt() + [{"kind": "flag_fired", "flag": "EVENT_BEAT_ROUTE_24_TRAINER_3"}] + attempt())
    ck("...but a numbered trainer beaten on the way does not",
       A.new_ground_problems(plan("CERULEAN_CITY"), G) != [])
    journal(attempt("Reach Vermilion City") + attempt())
    ck("another objective's failed walks are not this one's",
       A.new_ground_problems(plan("CERULEAN_CITY"), G) == [])
finally:
    os.chdir(here)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
