#!/usr/bin/env python3
"""A far side the plan itself reaches first is frozen when its step begins.

With the printed map on the page the author wrote Route 9 -> Route 10 ->
Rock Tunnel -> {"new_part": "ROUTE_10"} -> Lavender five times out of five,
and every one was refused (author_ab lavender, 2026-09-28): the run had
never stood on Route 10, so new_part froze to a bare {"map": "ROUTE_10"},
and the exit rule then refused that because an earlier step of the plan
already ends on ROUTE_10, telling the author to write new_part. Now the
author leaves it unfrozen in exactly that case, the executor reads it as not
yet done, and freezes it to the parts stood on as the step becomes current,
written into the plan file so a resume keeps it.

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
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def plan(exit_dw):
    return {"goal": "Reach Lavender Town", "subgoals": [
        {"id": "r9", "goal_text": "Go east to Route 9.", "done_when": {"map": "ROUTE_9"}},
        {"id": "r10", "goal_text": "Go on to Route 10.", "done_when": {"map": "ROUTE_10"}},
        {"id": "in", "goal_text": "Enter Rock Tunnel.", "done_when": {"map": "ROCK_TUNNEL_1F"}},
        {"id": "exit_rock_tunnel", "goal_text": "Go through Rock Tunnel and exit to the south side of Route 10.",
         "done_when": exit_dw},
        {"id": "lav", "goal_text": "Reach Lavender Town.", "done_when": {"map": "LAVENDER_TOWN"}}]}


d = Path(tempfile.mkdtemp(prefix="farside_"))
(d / "run").mkdir()
here = os.getcwd()
os.chdir(d)
try:
    (d / "run/explored.json").write_text(json.dumps({"visits": {"CERULEAN_CITY|0,0": 3}}))
    p = plan({"new_part": "ROUTE_10"})
    A.freeze_new_parts(p)
    ck("never stood on, and the plan reaches it first: left for the run to freeze",
       p["subgoals"][3]["done_when"] == {"new_part": "ROUTE_10"}, p["subgoals"][3]["done_when"])
    probs = A.validate(plan({"new_part": "ROUTE_10"}))
    ck("...and the plan is not refused for it",
       not any("exit_rock_tunnel" in x for x in probs), probs)
    probs = A.validate(plan({"map": "ROUTE_10"}))
    ck("a bare map for the exit is still refused, and told new_part",
       any("exit_rock_tunnel" in x and "new_part" in x for x in probs))
    p = {"goal": "g", "subgoals": [{"id": "x", "goal_text": "Exit to Route 10.",
                                    "done_when": {"new_part": "ROUTE_10"}}]}
    A.freeze_new_parts(p)
    ck("no earlier step reaches it: frozen now, as before",
       p["subgoals"][0]["done_when"] == {"map": "ROUTE_10"})
    (d / "run/explored.json").write_text(json.dumps({"visits": {"ROUTE_10|5,8": 2}}))
    p = plan({"new_part": "ROUTE_10"})
    A.freeze_new_parts(p)
    ck("stood on already: frozen now with the parts known",
       p["subgoals"][3]["done_when"] == {"map": "ROUTE_10", "not_area": ["ROUTE_10|5,8"]})
finally:
    os.chdir(here)

obs = {"mode": "overworld", "map": {"id": "ROUTE_10", "region": "5,8"}}
ck("unfrozen, it is not yet done even standing on the map",
   E.pred_holds({"new_part": "ROUTE_10"}, obs) is False)

x = object.__new__(E.Executor)
x.visits = {"ROUTE_10|5,8": 1, "ROUTE_9|0,0": 2}
logged = []
x.log = lambda kind, **kw: logged.append((kind, kw))
x.plan = plan({"new_part": "ROUTE_10"})
x.plan_path = d / "plan.json"
sg = x.plan["subgoals"][3]
x._freeze_new_part(sg)
ck("as the step begins it is frozen to the parts stood on then",
   sg["done_when"] == {"map": "ROUTE_10", "not_area": ["ROUTE_10|5,8"]}, sg["done_when"])
ck("...logged", logged and logged[0][0] == "new_part_frozen"
   and logged[0][1]["not_area"] == ["ROUTE_10|5,8"])
ck("...and written into the plan file, so a resume keeps it",
   json.loads((d / "plan.json").read_text())["subgoals"][3]["done_when"]
   == {"map": "ROUTE_10", "not_area": ["ROUTE_10|5,8"]})
ck("the far side then holds, the near side does not",
   E.pred_holds(sg["done_when"], {"map": {"id": "ROUTE_10", "region": "9,50"}})
   and not E.pred_holds(sg["done_when"], obs))
x._freeze_new_part(sg)
ck("freezing again changes nothing", len(logged) == 1)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
