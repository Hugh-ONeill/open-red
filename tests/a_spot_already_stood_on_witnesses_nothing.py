#!/usr/bin/env python3
"""An objective ending on the spot the run already stands on is refused.

Run 60, 2026-10-21: "Speak to Bill in Cerulean City" ended both steps on
{"player_at": {"x": 0, "y": 3, "radius": 2}}, where the party stood in the
Pokemon Center; the author could not read player_at, so the plan passed,
"completed" without a step, and the leg was counted.

Pinned: witness_holds_now reads player_at the way pred_holds does (radius 4
when unsaid), and an unreadable screen or shape stays unknown.
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


OBS = {"mode": "overworld", "map": {"id": "CERULEAN_POKECENTER"},
       "player": {"x": 1, "y": 3}, "bag": {}, "flags": ["X"], "badges": ["Y"]}
ck("the spot stood on holds now",
   A.witness_holds_now({"player_at": {"x": 0, "y": 3, "radius": 2}}, OBS) is True)
ck("a far spot does not",
   A.witness_holds_now({"player_at": {"x": 9, "y": 3, "radius": 2}}, OBS) is False)
ck("radius 4 when unsaid, as pred_holds",
   A.witness_holds_now({"player_at": {"x": 5, "y": 3}}, OBS) is True)
ck("a menu up is unknown",
   A.witness_holds_now({"player_at": {"x": 0, "y": 3}}, dict(OBS, mode="ui")) is None)
ck("a bad shape is unknown", A.witness_holds_now({"player_at": [0, 3]}, OBS) is None)
PLAN = {"subgoals": [{"id": "talk_to_gentleman",
                      "done_when": {"player_at": {"x": 0, "y": 3, "radius": 2}}}]}
r = A.witness_already_true_problems(PLAN, obs=OBS)
ck("the plan is refused as already holding", r and "ALREADY HOLDS" in r[0], r)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
