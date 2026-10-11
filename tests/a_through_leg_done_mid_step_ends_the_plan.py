#!/usr/bin/env python3
"""A THROUGH leg whose objective comes true mid-step ends the plan.

Run 48, Mt Moon (2026-10-11): "Navigate Mt. Moon and fight Team Rocket"
was planned down to "exit_b2f" ({"new_map_from": "MT_MOON_B2F"}), which no
B2F ladder could finish — they all go to B1F. The run came out on east
ROUTE_4 by B1F's ladder, the mountain left by its second mouth, and went
back in to hunt the B2F exit (user: "this wouldnt fix it since it wrote
that before it knew it all went to b1f").

Pinned on run 48's record: the two-mouths answer is None at the B2F
checkpoint and names both ROUTE_4 mouths on the live record; the round
loop ends the step on it only when it did not hold at plan start; the plan
loop then skips the remaining steps. Mixed (real records, source pins).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


GOAL = "Navigate Mt. Moon and fight Team Rocket"
FIX = ROOT / "tests" / "fixtures" / "run48_mt_moon"
ck("at the B2F checkpoint the record does not hold it",
   A._through_by_record(GOAL, FIX / "at_b2f.json") is None)
got = A._through_by_record(GOAL, FIX / "on_route4_east.json")
ck("on east ROUTE_4 it names both mouths",
   got and "ROUTE_4|36,2" in got and "ROUTE_4|4,4" in got, got)
src = (ROOT / "planner/executor.py").read_text()
ck("the round loop ends the step when it newly holds",
   "if not getattr(self, \"_thr_at_start\", \"\") \\\n" in src
   and "_thr = self._leg_through_now()" in src
   and 'self.log("leg_through_by_record"' in src)
ck("the plan loop skips the remaining steps",
   "if self._leg_met_by_record:" in src
   and 'self.log("plan_objective_met_by_record"' in src)
ck("the plan start takes the baseline",
   "self._thr_at_start = self._leg_through_now()" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
