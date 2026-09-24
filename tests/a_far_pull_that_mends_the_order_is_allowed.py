#!/usr/bin/env python3
"""A pull further than the cap is allowed when the judge says it puts the
list right.

Run of record, 2026-09-24, stuck on "Reach Celadon City" at 16 with "Reach
Lavender Town" at 27 and the tunnel at 33. The blocker rung's answer named
the Lavender stretch as what comes first — the judge's own reach order
says Lavender opens Celadon — and was refused: "a 17-leg pull: further
than 8". The later rung then tried to push Celadon behind it and the judge
refused that, rightly, because Saffron and Fuchsia sit between. No rung
had a legal move left and the chain stopped.

The cap bounds a guess. A pull that removes a fault the judge names and
adds none is not a guess, whatever its distance.

Pinned: the far pull that mends the reach order is allowed and says what
it mends; a far pull that mends nothing is still refused; one that mends a
fault but adds another is refused; the blocker rung consults it only past
the cap; a pull backwards is nothing. Synthetic."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import outline_gate as G  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


OUTLINE = ["Choose a starter Pokemon",           # 1
           "Defeat Brock for the Boulder Badge",
           "Defeat Misty for the Cascade Badge",
           "Reach Vermilion City",
           "Defeat Lt. Surge for the Thunder Badge",  # 5
           "every party member is at least level 30",
           "Reach Celadon City",                       # 7 (stuck)
           "Visit the Celadon Department Store",
           "Defeat Erika for the Rainbow Badge",
           "Reach Saffron City",                       # 10
           "Defeat Sabrina for the Marsh Badge",
           "every party member is at least level 40",
           "Reach Lavender Town",                      # 13
           "Clear the Pokemon Tower",
           "Reach Fuchsia City",                       # 15
           "Defeat Koga for the Soul Badge",
           "Navigate through the Rock Tunnel",         # 17
           "Reach Cinnabar Island"]


def with_outline(lines):
    d = Path(tempfile.mkdtemp()); (d / "plans").mkdir()
    (d / "plans/outline.txt").write_text("\n".join(lines) + "\n")
    return d / "plans/outline.txt"


p = with_outline(OUTLINE)
ck("the list as drawn has the Celadon-before-Lavender fault",
   any("Celadon is reached before Lavender" in f for f in G.faults(OUTLINE)))
m = A.far_pull_mends(7, 13, p)
ck("pulling Lavender in front of Celadon, twelve legs, is allowed and says what it mends",
   m and all("reach order" in x for x in m) and any("Lavender" in x for x in m), m)
ck("pulling the level leg that far mends nothing, so the cap stands",
   A.far_pull_mends(7, 12, p) == [])
ck("pulling the tunnel alone mends nothing either: Celadon is still before Lavender",
   A.far_pull_mends(7, 17, p) == [])
ck("pulling Fuchsia in front of Celadon would add a fault, so it is refused",
   A.far_pull_mends(7, 15, p) == [])
ck("a pull backwards is nothing", A.far_pull_mends(13, 7, p) == [])
ck("a missing outline is nothing, never an error",
   A.far_pull_mends(7, 13, Path("/nonexistent/outline.txt")) == [])

SRC = (ROOT / "planner/author.py").read_text()
_code = "\n".join(l for l in SRC.splitlines() if not l.lstrip().startswith("#"))
i = _code.index("if gap > PULL_MAX:")
blk = _code[i:i + 900]
ck("the blocker rung consults it only past the cap, and says so when it allows",
   "_mend = far_pull_mends(leg, n)" in blk
   and "allowed: it puts the list right" in blk
   and "further than {PULL_MAX} — the" in blk)
ck("the gate's mend reading is the judge's, faults before minus faults after",
   "faults(before) - faults(after)" in (ROOT / "planner/outline_gate.py").read_text())

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
