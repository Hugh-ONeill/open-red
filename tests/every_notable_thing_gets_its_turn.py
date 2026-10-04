#!/usr/bin/env python3
"""The NOTABLE section rotates: a thing two voices said is not cut for good
behind every thing three voices said.

Run 36, 2026-10-03: sorted by voices and cut at eight, GAME CORNER (the
sailor's "There's no secret switch behind it!", the Diner's "basement under
the GAME CORNER") never reached the section while COIN CASE always did (user:
"there should directly be a quote that says full on theres a secret switch
behind the poster"). Replayed on a copy of the run: it now shows every second
round. Source pins."""
from pathlib import Path
src = (Path(__file__).resolve().parents[1] / "planner/executor.py").read_text()
checks = [
    ("groups go least-shown first, voices breaking ties",
     "rows.sort(key=lambda r: (_ns.get(r[0], 0), -len(r[2]), r[0]))" in src),
    ("showing a group counts it", "_ns[r[0]] = _ns.get(r[0], 0) + 1" in src),
    ("still eight at a time", "rows = rows[:8]" in src),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
