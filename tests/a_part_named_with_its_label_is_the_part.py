#!/usr/bin/env python3
"""An area written with the page's label is the part it names.

The page labels parts ("ROUTE_20|44,2 (the west part of ROUTE_20)") and the
author copied one whole into a condition: leg 46's
{"area": "SEAFOAM_ISLANDS_B4F|2,0 (the west part of SEAFOAM_ISLANDS_B4F)"}
equals no region and was carried past as NOT achieved (run 19, 2026-09-29).

Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def plan():
    return {"goal": "g", "subgoals": [
        {"id": "a", "goal_text": "west part", "done_when":
         {"area": "SEAFOAM_ISLANDS_B4F|2,0 (the west part of SEAFOAM_ISLANDS_B4F)"}},
        {"id": "b", "goal_text": "far side", "done_when":
         {"map": "ROUTE_20", "not_area": ["ROUTE_20|44,2 (the west part)", "ROUTE_20|52,2"]}},
        {"id": "c", "goal_text": "either", "done_when":
         {"any": [{"area": "X_MAP|1,2 (the north part)"}, {"map": "Y"}]}},
        {"id": "d", "goal_text": "a word", "done_when": {"area": "not a part (at all)"}}]}


p = plan()
A.validate(p)
dws = [s["done_when"] for s in p["subgoals"]]
ck("the author's check leaves the bare part", dws[0] == {"area": "SEAFOAM_ISLANDS_B4F|2,0"}, dws[0])
ck("...in not_area lists too", dws[1]["not_area"] == ["ROUTE_20|44,2", "ROUTE_20|52,2"], dws[1])
ck("...and inside any-alternatives", dws[2]["any"][0] == {"area": "X_MAP|1,2"}, dws[2])
ck("something that is not a part is left for the validator", dws[3] == {"area": "not a part (at all)"}, dws[3])

p = plan()
x = E.Executor(None, plan=p)
ck("a plan written before the fix is cleaned when the executor takes it",
   x.plan["subgoals"][0]["done_when"] == {"area": "SEAFOAM_ISLANDS_B4F|2,0"})
ck("...and then holds standing there",
   E.pred_holds(x.plan["subgoals"][0]["done_when"],
                {"map": {"id": "SEAFOAM_ISLANDS_B4F", "region": "2,0"}}))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
