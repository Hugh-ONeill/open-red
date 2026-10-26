#!/usr/bin/env python3
"""A middle step that ends on pressing something already pressed is refused.

Run 66, 2026-10-25, leg 30 "Defeat the rival inside Silph Co.": the plan's
unlock_rival_door step ended on {"spoke_to": "DOOR_SILPH_CO_10F_10_8"}, a
door the run had pressed ("Darn! It needs a CARD KEY!") before the plan was
written. The step read done on entry and the plan went on to the rival with
the door shut and no CARD_KEY.

Pinned: such a step is refused naming the press; a step ending on someone
not yet pressed, or on a press plus something else, is not.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

d = Path(tempfile.mkdtemp(prefix="pressed_"))
(d / "run").mkdir()
(d / "run/explored.json").write_text(json.dumps(
    {"touched": {"SILPH_CO_10F|8,0": ["DOOR_SILPH_CO_10F_10_8", "SILPHCO10F_ROCKET"]}}))
OBS = {"mode": "overworld", "map": {"id": "SILPH_CO_ELEVATOR"}, "bag": {"LIFT_KEY": 1},
       "flags": [], "badges": []}

def plan(mid):
    return {"goal": "Defeat the rival inside Silph Co.", "subgoals": [
        {"id": "get_key", "done_when": {"has_item": {"CARD_KEY": 1}}},
        {"id": "unlock", "done_when": mid},
        {"id": "beat", "done_when": {"has_item": {"MASTER_BALL": 1}}}]}

here = os.getcwd()
os.chdir(d)
try:
    p = A.witness_already_true_problems(plan({"spoke_to": "DOOR_SILPH_CO_10F_10_8"}), OBS)
    ck("a step on a door already pressed is refused",
       p and "ALREADY HOLDS" in p[0] and "DOOR_SILPH_CO_10F_10_8" in p[0], p)
    p = A.witness_already_true_problems(plan({"spoke_to": "DOOR_SILPH_CO_10F_9_12"}), OBS)
    ck("a door never pressed stands", p == [], p)
    p = A.witness_already_true_problems(
        plan({"spoke_to": "DOOR_SILPH_CO_10F_10_8", "map": "SILPH_CO_11F"}), OBS)
    ck("a press with another condition is left to the rest", p == [], p)
    p = A.witness_already_true_problems(
        plan({"spoke_to": ["SILPHCO10F_ROCKET", "SILPHCO10F_SCIENTIST"]}), OBS)
    ck("a list with someone not yet pressed stands", p == [], p)
finally:
    os.chdir(here)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
