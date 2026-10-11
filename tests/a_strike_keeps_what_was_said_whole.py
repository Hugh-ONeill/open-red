#!/usr/bin/env python3
"""A strike's reason keeps what was said whole.

Pewter's guide boy turned the east cross back three times before Brock,
and the refusal that followed quoted him as "You're a" — cut at 160
characters. "BROCK's looking for new challengers! Follow me!" never
reached a page again, and the model hunted the town for a way round two
NPCs (run 45, 2026-10-10). Run 45's own failure line. Synthetic.
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


DET = ("couldn't reach east edge gap (39,17), stuck at (29,18) — 11 cell(s) of walking "
       "still to do — during this walk someone spoke and the walk ended short: \"You're a "
       "trainer right? BROCK's looking for new challengers! Follow me!\" — and while it "
       "spoke you were walked back: from within 3 cell(s) of the gap to 34 away")
w = E.Executor._strike_why(DET)
ck("the boy's whole line is kept", w.endswith("Follow me!\""), w)
ck("...and nothing after it", "walked back" not in w)
ck("a reason with no speech is cut as before",
   E.Executor._strike_why("x" * 300) == "x" * 160)
ck("a quote that starts late is cut as before",
   E.Executor._strike_why("y" * 310 + ' "hi"') == "y" * 160)
src = (ROOT / "planner/executor.py").read_text()
ck("every strike reason goes through it",
   'self._dead_why[sig] = str(det or "")[:160]' not in src
   and src.count("self._dead_why[sig] = self._strike_why(det)") == 3)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
