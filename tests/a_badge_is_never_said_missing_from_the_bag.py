#!/usr/bin/env python3
"""A badge is never said to be missing from the bag.

Run 47, Cerulean (2026-10-10), Misty beaten, BOULDERBADGE and CASCADEBADGE
worn: the plan said "Although I have the CASCADEBADGE, I do not have the HM
for CUT in my bag", and the round answered "WORDS ARE NOT THE BAG: your
plan speaks of holding CASCADEBADGE; the bag holds no CASCADEBADGE". Gen
1's item list holds the badges, so the check looked for one in the bag.

Pinned on run 47's sentence: no note for a badge, worn or not; a real item
claimed and not held is still named. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ex = E.Executor.__new__(E.Executor)
O = {"mode": "overworld", "bag": {"POTION": 1}, "badges": ["BOULDERBADGE", "CASCADEBADGE"]}
n = ex._held_claim_note("Although I have the CASCADEBADGE, I do not have the HM for CUT in my bag.", O)
ck("run 47's sentence draws no note", n == "", n)
n = ex._held_claim_note("I have the THUNDERBADGE now.", O)
ck("a badge not yet won is not a bag claim either", n == "", n)
n = ex._held_claim_note("I have the CARD KEY in my bag.", O)
ck("a real item claimed and not held is still named", "CARD_KEY" in n, n)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
