#!/usr/bin/env python3
"""A booklet line that names another item brings that item's line too.

The Plateau lobby shelf held ULTRA_BALL and GREAT_BALL, whose lines only say
each "performs better than" the last; with no POKE_BALL on the shelf the page
never said a ball catches Pokemon, and the run bought ten Ultra Balls between
Elite Four laps for "high-tier healing" (run 19, 2026-09-30).

Synthetic.
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


t = E.Executor._booklet_words(["ULTRA_BALL", "MAX_POTION"])
ck("the chain reaches the line that says what a ball is for",
   "POKE_BALL: This ball catches Pokemon" in t and "GREAT_BALL:" in t, t)
ck("each item is said once", t.count("POKE_BALL:") == 1 and t.count("ULTRA_BALL:") == 1, t)
t = E.Executor._booklet_words(["MAX_POTION"])
ck("a line naming nothing brings nothing", t.count("; ") == 0 and "MAX_POTION:" in t, t)
ck("no items, no line", E.Executor._booklet_words([]) == "")

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
