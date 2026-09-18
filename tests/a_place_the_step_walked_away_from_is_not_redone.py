#!/usr/bin/env python3
"""A place step that held when the next step began, and that the next
step's own rounds walked away from, is not re-opened by the backtrack.

Run 27, 2026-09-18: exit_mansion (map CINNABAR_ISLAND) held when
enter_cinnabar_gym began; the gym was locked, the step's rounds walked
down into the Pokemon Mansion after the key, the step failed, and the
backtrack re-opened exit_mansion, which walked the party straight back
out — three times (user: "its in an outrageous loop ... it happily routes
itself out the other exit on the 1st floor forgetting how much effort it
spent getting itself to that point in the first place").

Pinned: the earlier pure place steps that hold are noted before each step
runs; a candidate among them that no longer holds ends the scan with no
backtrack (the plan is rewritten from where the party stands), logged as
left on purpose; the building rule and the relocate mode are untouched.
Source-anchored: the plan runner drives the game.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


src = (ROOT / "planner/executor.py").read_text()
i = src.index("            # WHICH EARLIER PLACE STEPS HELD WHEN THIS ONE BEGAN")
ck("the earlier place steps that hold are noted before the step runs",
   i < src.index("            ok = self._attempt(sg)\n            _ran_any = True")
   and "_held_at_start = {" in src[i:i + 900]
   and 'set(s0.get("done_when") or {}) <= {"map", "area", "not_area"}' in src[i:i + 900])
loop = src[src.index("for back in range(idx - 1, max(-1, idx - 5), -1):"):][:7000]
ck("a candidate that held then and was walked away from ends the scan",
   'if c.get("id") in _held_at_start:' in loop
   and 'cand = None\n                            break' in loop.split('if c.get("id") in _held_at_start:', 1)[1][:400])
ck("...logged as left on purpose", '"backtrack_place_left_on_purpose"' in loop)
ck("...after the building rule, which still runs first",
   loop.index('"backtrack_place_held"') < loop.index('"backtrack_place_left_on_purpose"'))
ck("the relocate mode for a step that still holds is untouched",
   "cand, holds, elsewhere = c, True, elw" in loop)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
