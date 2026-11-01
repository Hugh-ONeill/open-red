#!/usr/bin/env python3
"""A step that asks only to be standing at a spot ends itself when a later
step already holds, exactly as a map-only step does.

Run 69, leg 57 (2026-11-01): reach_indigo_plateau_entrance was
{"player_at": {"x": 3, "y": 33, "radius": 5}}, the model's own guess at "the
entrance" (it is the Victory Road gate sign, on Route 23's far part). The
party came out of 2F's (29,7) door on the Plateau side and crossed north onto
INDIGO_PLATEAU, which the NEXT step asked for; the spot step did not pass, so
the run spent 15 rounds and a backtrack into Victory Road trying to walk back
to (3,33), and run 69 stopped standing in the lobby with Lorelei never fought.
player_at is travel (the author files it so, next150): a plan past it has
passed it.

Pinned: a player_at-only step with a later map step true is passed; a spot
step mixed with a deed is not; the plan's last spot step is never passed."""
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


on_plateau = {"mode": "overworld", "map": {"id": "INDIGO_PLATEAU"},
              "player": {"x": 10, "y": 17}, "bag": {}, "party": [], "badges": [],
              "flags": []}
subs = [{"id": "navigate_victory_road_3f",
         "done_when": {"map": "ROUTE_23", "not_area": ["ROUTE_23|4,31"]}},
        {"id": "reach_indigo_plateau_entrance",
         "done_when": {"player_at": {"x": 3, "y": 33, "radius": 5}}},
        {"id": "enter_indigo_plateau", "done_when": {"map": "INDIGO_PLATEAU"}},
        {"id": "defeat_elite_four", "done_when": {"hall_of_fame": True}}]
ex = ex_with(subs)
ck("a spot step with a later map step true is passed (run 69's leg 57)",
   ex._waypoint_passed(subs[1], on_plateau) == "enter_indigo_plateau",
   ex._waypoint_passed(subs[1], on_plateau))
ck("...and the map step before it, through the spot step",
   ex._waypoint_passed(subs[0], on_plateau) == "enter_indigo_plateau",
   ex._waypoint_passed(subs[0], on_plateau))
on_route = dict(on_plateau, map={"id": "ROUTE_23"}, player={"x": 10, "y": 0})
ck("standing short of the later step, the spot step stays",
   ex._waypoint_passed(subs[1], on_route) is None)
subs2 = [{"id": "stand_on_switch",
          "done_when": {"player_at": {"x": 5, "y": 5}, "flag": "EVENT_SWITCH"}},
         {"id": "leave", "done_when": {"map": "VICTORY_ROAD_2F"}},
         {"id": "out", "done_when": {"map": "ROUTE_23"}}]
ck("a spot step that also asks for a deed is not a waypoint",
   ex_with(subs2)._waypoint_passed(subs2[0], on_route) is None)
subs3 = [{"id": "go", "done_when": {"map": "ROUTE_23"}},
         {"id": "stand", "done_when": {"player_at": {"x": 3, "y": 33, "radius": 5}}}]
ck("the plan's last step is never passed this way",
   ex_with(subs3)._waypoint_passed(subs3[1], on_plateau) is None)
ck("player_at is a waypoint key", "player_at" in E.Executor.WAYPOINT_KEYS)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
