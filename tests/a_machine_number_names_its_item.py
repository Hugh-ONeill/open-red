#!/usr/bin/env python3
"""A plan that writes a machine by its number is told that machine's id.

Run 67, 2026-10-27, leg "Retrieve the HM04 from the Safari Zone": the author
wrote {"has_item": {"HM04": 1}}, was told "did you mean HM_FLY, HM_CUT?" (the
nearest spellings), and wrote HM_FLY for STRENGTH; the rewritten leg waited
on the wrong HM.

Pinned: HM04 and TM13 are answered with the ids the game numbers that way;
a number the game does not reach is still a phantom; a plain typo still
gets the near spellings.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

def probs(item):
    return A.validate({"goal": "g", "subgoals": [
        {"id": "x", "goal_text": "t", "done_when": {"has_item": {item: 1}}}]})

p = probs("HM04")
ck("HM04 is named as HM_STRENGTH", p and "HM04 is what the bag calls HM_STRENGTH" in p[0]
   and "HM_FLY" not in p[0], p)
tm13 = A.MACHINE_NUMBER_ITEM.get("TM13")
p = probs("TM13")
ck("TM13 is named as its own id", tm13 and p and f"calls {tm13}" in p[0], (tm13, p))
p = probs("HM08")
ck("a number the game does not reach is still a phantom", p and "there is no HM08" in p[0], p)
p = probs("HM_STRENGHT")
ck("a plain typo still gets the near spellings", p and "did you mean" in p[0]
   and "HM_STRENGTH" in p[0], p)

v = A.validate({"goal": "Retrieve the HM04", "subgoals": [
    {"id": "get_hm04", "goal_text": "Pick up the HM04 (Strength)",
     "done_when": {"has_item": {"HM_FLY": 1}}}]})
ck("words naming HM04 over a condition holding HM_FLY are refused",
   any("your words name HM04 (HM_STRENGTH)" in x and "HM_FLY (HM02)" in x for x in v), v)
v = A.validate({"goal": "g", "subgoals": [
    {"id": "get_hm04", "goal_text": "Pick up the HM04",
     "done_when": {"has_item": {"HM_STRENGTH": 1}}}]})
ck("...and the matching machine stands", not any("your words name" in x for x in v), v)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
