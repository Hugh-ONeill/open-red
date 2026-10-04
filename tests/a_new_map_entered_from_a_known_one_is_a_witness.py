#!/usr/bin/env python3
"""{"new_map_from": MAP}: a map never stood on when the step began, entered
straight from MAP. The model names the place it goes in from; the place it
arrives in is whatever the game calls it.

Run 36, 2026-10-03: the model's first idea for "Infiltrate the Team Rocket
secret base" was the Game Corner, but no end for it could be written (the
hideout's name is on no page; "ROCKET_GAME_CORNER" refused), and the only
plan that passed was a wrong one up the Celadon Mansion (user: "a bare ask
to gemma about where the rocket secret base gets the correct answer").

Pinned: the validator takes it and refuses a made-up map; the step freezes
the maps stood on at entry; it holds only on a new map entered from MAP;
unfrozen it is not done; it is a waypoint."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A     # noqa: E402
import executor as E   # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

plan = {"goal": "Infiltrate the Team Rocket secret base in Celadon City", "subgoals": [
    {"id": "go", "goal_text": "Walk to the Game Corner", "done_when": {"map": "GAME_CORNER"}},
    {"id": "down", "goal_text": "Find the way in under it",
     "done_when": {"new_map_from": "GAME_CORNER"}}]}
ck("the validator takes the plan the model wanted", A.validate(plan) == [], A.validate(plan))
bad = {"goal": "g", "subgoals": [{"id": "x", "goal_text": "t",
                                  "done_when": {"new_map_from": "ROCKET_GAME_CORNER"}}]}
ck("...and refuses a place the game does not have",
   any("ROCKET_GAME_CORNER" in p for p in A.validate(bad)))

ex = object.__new__(E.Executor)
ex.visits = {"CELADON_CITY|2,1": 9, "GAME_CORNER|8,5": 2}
ex.plan_path = None
ex.log = lambda *a, **k: None
sg = {"id": "down", "done_when": {"new_map_from": "GAME_CORNER"}}
ck("unfrozen, it is not begun, so not done",
   not E.pred_holds(sg["done_when"], {"map": {"id": "ROCKET_HIDEOUT_B1F"},
                                      "came_from": "GAME_CORNER"}))
ex._freeze_new_part(sg)
ck("at step entry the maps stood on are frozen in",
   sg["done_when"].get("not_maps") == ["CELADON_CITY", "GAME_CORNER"], sg["done_when"])

import bridge as B  # noqa: E402
_br = object.__new__(B.Bridge)
def see(mid):
    return _br._came_from_stamp({"map": {"id": mid}, "party": [], "bag": {}})
see("CELADON_CITY"); o1 = see("GAME_CORNER")
ck("standing in the Game Corner is not it", not E.pred_holds(sg["done_when"], o1))
o2 = see("ROCKET_HIDEOUT_B1F")
ck("the new map below, entered from the Game Corner, is it",
   o2.get("came_from") == "GAME_CORNER" and E.pred_holds(sg["done_when"], o2), o2.get("came_from"))
o3 = see("CELADON_CITY")
ck("a map stood on before the step is never it", not E.pred_holds(sg["done_when"], o3))
ck("a new map entered from somewhere else is not it",
   not E.pred_holds(sg["done_when"], {"map": {"id": "ROUTE_17"}, "came_from": "CELADON_CITY"}))
ck("it is a place to pass through like any other",
   {"new_map_from", "not_maps"} <= set(E.Executor.WAYPOINT_KEYS))
ck("the page explains it", "new_map_from" in A.PREDICATES and "GAME_CORNER" in A.PREDICATES["new_map_from"])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)

