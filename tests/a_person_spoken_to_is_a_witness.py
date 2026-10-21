#!/usr/bin/env python3
"""A person spoken to, by name, can end a step.

Run 60, 2026-10-21: after the Cell Separator the restored Bill
(BILLSHOUSE_BILL1) stood unspoken-to; check-done refused "Help Bill in the
house on Route 25" on that, and the author then had nothing to end a plan
on: every flag it reached for (EVENT_MET_BILL, EVENT_USED_CELL_SEPARATOR_ON_
BILL, EVENT_MET_BILL_2) had fired and every map had been stood on. Fifteen
rounds were refused and the leg was pushed behind "Reach Vermilion City",
which the guard Bill's ticket moves holds shut.

Pinned: {"spoke_to": NAME} holds once the run's touch ledger has the name
(a list needs every one); the author takes it, refuses a name never seen,
counts a talk already had as true before the plan starts, offers it in the
already-holds refusal, and says it beside the unspoken-to names.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


# --- the executor reads its own ledger
ex = object.__new__(E.Executor)
ex._tried_objs = {"BILLS_HOUSE|0,2": {"POKEMON_BILLS_HOUSE_6_5"}}
E._WALKED_REF[0] = ex
OBS = {"mode": "overworld", "map": {"id": "BILLS_HOUSE"}}
ck("a person never spoken to is not a witness yet",
   not E.pred_holds({"spoke_to": "BILLSHOUSE_BILL1"}, OBS))
ex._tried_objs["BILLS_HOUSE|0,2"].add("BILLSHOUSE_BILL1")
ck("...and is once the talk is in the ledger",
   E.pred_holds({"spoke_to": "BILLSHOUSE_BILL1"}, OBS))
ck("a list needs every one of them",
   not E.pred_holds({"spoke_to": ["BILLSHOUSE_BILL1", "BILLSHOUSE_BILL2"]}, OBS)
   and E.pred_holds({"spoke_to": ["BILLSHOUSE_BILL1", "POKEMON_BILLS_HOUSE_6_5"]}, OBS))
ck("a malformed value holds nothing", not E.pred_holds({"spoke_to": 3}, OBS))

# --- the author, on a ledger of its own (never the live run's)
tmp = tempfile.mkdtemp()
os.chdir(tmp)
Path("run").mkdir()
Path("run/explored.json").write_text(json.dumps({
    "sightings": {"BILLS_HOUSE|0,2": ["POKEMON_BILLS_HOUSE_6_5", "BILLSHOUSE_BILL1"]},
    "touched": {"BILLS_HOUSE|0,2": ["POKEMON_BILLS_HOUSE_6_5"]}}))

ck("the author knows the word", "spoke_to" in A.VALID_KEYS)
p = []
A._check_pred_shapes({"spoke_to": "BILLSHOUSE_BILL1"}, "subgoal[0]", "talk", p)
ck("a seen name passes", p == [], p)
p = []
A._check_pred_shapes({"spoke_to": "BILLSHOUSE_BILL9"}, "subgoal[0]", "talk", p)
ck("a name never seen is refused", p and "not a name this run has seen" in p[0], p)
p = []
A._check_pred_shapes({"spoke_to": []}, "subgoal[0]", "talk", p)
ck("an empty list is refused", p and "needs a name" in p[0], p)

PLAN = {"subgoals": [{"id": "talk", "done_when": {"spoke_to": "POKEMON_BILLS_HOUSE_6_5"}}]}
r = A.witness_already_true_problems(PLAN, obs=dict(OBS, bag={}, flags=["X"], badges=["Y"]))
ck("a talk already had holds before the plan starts", r and "ALREADY HOLDS" in r[0], r)
PLAN2 = {"subgoals": [{"id": "talk", "done_when": {"spoke_to": "BILLSHOUSE_BILL1"}}]}
r = A.witness_already_true_problems(PLAN2, obs=dict(OBS, bag={}, flags=["X"], badges=["Y"]))
ck("...one not yet had does not", r == [], r)
PLAN3 = {"subgoals": [{"id": "talk", "done_when": {"flag": "X"}}]}
r = A.witness_already_true_problems(PLAN3, obs=dict(OBS, bag={}, flags=["X"], badges=["Y"]))
ck("the already-holds refusal offers it", r and "(spoke_to)" in r[0], r)
ck("the unspoken-to names say it",
   "spoke_to" in A.untouched_named_text("Help Bill in the house on Route 25"),
   A.untouched_named_text("Help Bill in the house on Route 25"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
