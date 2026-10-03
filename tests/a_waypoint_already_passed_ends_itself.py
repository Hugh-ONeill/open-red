#!/usr/bin/env python3
"""A step that asks only to be on a map ends itself when a later step of
the plan already holds, if every step between is a waypoint too.

Run 27, 2026-09-18: plan 14 of the Indigo leg ran 3F -> 2F -> 1F -> ROUTE_23
-> INDIGO_PLATEAU; 2F's (29,7) door let the party out on Route 23's Plateau
side, the page said twice that the ROUTE_23 step already held, and the run
kept trying to get back into Victory Road for the 1F step (user: "it wants
to backtrack but its on rt23 indigo plateau side").

Pinned: a map/area-only step with a later step true is passed; a step that
checks anything else is not; a non-waypoint step in between stops it; the
plan's last step is never passed this way; the check runs at step entry,
before a replay, and at the top of each escalation round. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def ex_with(subs):
    ex = object.__new__(E.Executor)
    ex.plan = {"subgoals": subs}
    return ex


obs = {"mode": "overworld", "map": {"id": "ROUTE_23"}, "player": {"x": 9, "y": 5},
       "bag": {}, "party": [], "badges": []}
subs = [{"id": "leave_2f", "done_when": {"map": "VICTORY_ROAD_1F"}},
        {"id": "leave_1f", "done_when": {"map": "ROUTE_23"}},
        {"id": "reach_plateau", "done_when": {"map": "INDIGO_PLATEAU"}}]
ex = ex_with(subs)
ck("a map-only step with a later step true is passed", ex._waypoint_passed(subs[0], obs) == "leave_1f",
   ex._waypoint_passed(subs[0], obs))
subs2 = [{"id": "buy", "done_when": {"has_item": {"POTION": 1}}},
         {"id": "leave_1f", "done_when": {"map": "ROUTE_23"}},
         {"id": "reach_plateau", "done_when": {"map": "INDIGO_PLATEAU"}}]
ck("a step that checks anything else is not", ex_with(subs2)._waypoint_passed(subs2[0], obs) is None)
subs3 = [{"id": "leave_2f", "done_when": {"map": "VICTORY_ROAD_1F"}},
         {"id": "heal", "done_when": {"party_healthy": True}},
         {"id": "leave_1f", "done_when": {"map": "ROUTE_23"}},
         {"id": "reach_plateau", "done_when": {"map": "INDIGO_PLATEAU"}}]
ck("a non-waypoint step in between stops it", ex_with(subs3)._waypoint_passed(subs3[0], obs) is None)
ck("the plan's last step is never passed this way",
   ex._waypoint_passed(subs[2], obs) is None)
obs4 = dict(obs, map={"id": "ROUTE_4"})
subs4 = [{"id": "explore_route_3_north",
          "done_when": {"map": "ROUTE_3", "not_area": ["ROUTE_3|18,8", "ROUTE_3|57,0"]}},
         {"id": "travel_to_route_4", "done_when": {"map": "ROUTE_4"}},
         {"id": "enter_mt_moon", "done_when": {"map": "MT_MOON_1F"}}]
ck("a new-part step (map + not_area) is a waypoint too",
   ex_with(subs4)._waypoint_passed(subs4[0], obs4) == "travel_to_route_4")
src = (ROOT / "planner/executor.py").read_text()
ck("it runs at step entry", 'via="entry")' in src)
ck("...before a replay", 'later=_past, at=self._where(obs), via="pre-check")' in src)
ck("...and at the top of each escalation round", 'later=_past, at=self._where(cur))' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
