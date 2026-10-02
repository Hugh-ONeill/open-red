#!/usr/bin/env python3
"""A step that ends on {"mode": "overworld"} alone is refused: it is true
wherever no box, menu or fight is up, which is where a plan starts.

Run 26 (2026-10-02): "Battle the rival for the first time" was planned twice
as exit_oaks_lab + battle_rival {"mode": "overworld"}; both "completed" in Oak's
Lab with no fight, and check-done had to refuse them. User: "it judged 'beat the
rival for the first time' done without facing the rival".
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


plan = {"goal": "Battle the rival for the first time", "subgoals": [
    {"id": "exit_oaks_lab", "goal_text": "Leave the lab", "done_when": {"map": "PALLET_TOWN"}},
    {"id": "battle_rival", "goal_text": "Battle the rival", "done_when": {"mode": "overworld"}}]}
p = A.validate(plan)
ck("mode overworld alone is refused", any("marks nothing" in x and "overworld" in x for x in p), p)
plan["subgoals"][1]["done_when"] = {"flag": "EVENT_BATTLED_RIVAL_IN_OAKS_LAB"}
p2 = [x for x in A.validate(plan) if "overworld" in x]
ck("a step ending on what the fight fires is not", p2 == [], p2)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
