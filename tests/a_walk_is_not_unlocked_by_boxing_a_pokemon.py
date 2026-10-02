#!/usr/bin/env python3
"""Putting a Pokemon in the PC is not a deed that unlocks a refused walk, and
a plan does not box a party member unless its objective is about the PC.

Run 24 (2026-10-02): inside Mt Moon, "Reach Cerulean City" was refused five
rounds as the same failed walk; the author added "heal_at_mt_moon_center"
and "visit_mt_moon_pc: pc_holds 1" to get past it, and the executor deposited
Geodude, its Mega Punch user, "to satisfy the goal".
"""
import json
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


plan = {"subgoals": [
    {"id": "heal_at_mt_moon_center", "done_when": {"party_healthy": True}},
    {"id": "visit_mt_moon_pc", "done_when": {"pc_holds": 1}},
    {"id": "walk_to_cerulean_city", "done_when": {"map": "CERULEAN_CITY"}}]}
p = A.pc_step_problems(plan, goal="Reach Cerulean City")
ck("a PC step in a plan whose objective says nothing of the PC is refused",
   p and "visit_mt_moon_pc" in p[0] and "Remove this step" in p[0], p)
ck("...but kept when the objective is about the PC",
   A.pc_step_problems(plan, goal="Deposit a Pokemon in the PC to make room") == [])

A._failed_walk_places = lambda goal, run: [("walk_to_cerulean_city", "CERULEAN_CITY")]
A.untried_leads = lambda *a, **k: []
r = A.same_failed_walk_problems(plan, goal="Reach Cerulean City")
ck("boxing a Pokemon does not count as doing something before the same walk",
   r and "this is the same walk" in r[0], r)
ck("...and the refusal says ground never stood on counts, and healing or the PC does not",
   r and "new_part" in r[0] and "Healing or putting a Pokemon in the PC does not" in r[0], r)
deed = {"subgoals": [{"id": "get_cut", "done_when": {"has_item": {"HM_CUT": 1}}},
                     {"id": "walk", "done_when": {"map": "CERULEAN_CITY"}}]}
ck("a real deed first still lets the walk follow",
   A.same_failed_walk_problems(deed, goal="Reach Cerulean City") == [])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
