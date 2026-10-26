#!/usr/bin/env python3
"""A refused event kept as the objective's witness must share a word that is
not a place's, and "no event begins with" is said only when none does.

Run 66, 2026-10-25, leg "Defeat Giovanni in the Silph Co. building": a draft
ended on EVENT_SILPH_CO_9_UNLOCKED_DOOR4 (already fired), which shared SILPH
with the objective and was kept as its own witness; the judge read it and
crossed the leg off with Giovanni unfought. In the same rounds the author was
told "No event in this game's list begins with EVENT_BEAT_GIOVANNI" (it is
one) and "...begins with EVENT_SILPH_CO" (eleven door events do).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

G = "Defeat Giovanni in the Silph Co. building"
ck("a door of the building is not Giovanni's witness",
   not A._flag_shares_a_word("EVENT_SILPH_CO_9_UNLOCKED_DOOR4", G))
ck("Giovanni's own event still is", A._flag_shares_a_word("EVENT_BEAT_SILPH_CO_GIOVANNI", G))
ck("the drink still shares GUARD",
   A._flag_shares_a_word("EVENT_GAVE_GUARDS_DRINK", "Give FRESH WATER to the guard on Route 6"))
ck("the rival still shares RIVAL",
   A._flag_shares_a_word("EVENT_BEAT_SILPH_CO_RIVAL", "Defeat the rival inside Silph Co."))

for guess, stem in (("EVENT_BEAT_GIOVANNI_SILPH", "EVENT_BEAT_GIOVANNI"),
                    ("EVENT_SILPH_CO_BOSS_DEFEATED", "EVENT_SILPH_CO")):
    plan = {"goal": G, "subgoals": [
        {"id": "go", "done_when": {"map": "SILPH_CO_11F"}},
        {"id": "beat", "done_when": {"flag": guess}}]}
    p = " ".join(A.validate(plan) or [])
    ck(f"{guess}: refused", "is not an event this game defines" in p, p[:300])
    ck(f"...without claiming none begins with {stem}",
       f"No event in this game's list begins with {stem}," not in p, p[:600])
p = " ".join(A.validate({"goal": "Cut the tree", "subgoals": [
    {"id": "cut", "done_when": {"flag": "EVENT_CUT_VERMILION_GYM_TREE"}},
    {"id": "in", "done_when": {"map": "VERMILION_GYM"}}]}) or [])
ck("a stem no event has still says so",
   "No event in this game's list begins with EVENT_CUT_VERMILION" in p, p[:600])

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
