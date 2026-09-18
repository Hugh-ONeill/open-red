#!/usr/bin/env python3
"""A round that moved the party did not come to nothing, so the same
macro is not refused as a repeat afterwards.

Run 27, 2026-09-18, Pokemon Mansion 2F: after the switch was pressed,
explore walked to a cell beside a wall the switch may have moved —
"walk_to(10,5): ok" — and the round was filed as a try that came to
nothing, because the trace held none of the words "moved", "warped",
"crossed" or "map->". The next four explores, each a different step since
explore reads the ledger, were refused without running (user: "it got
interrupted by a battle, is it refusing to do the same thing now?").

Pinned: the party's position before the macro is taken, and a change in it
counts as the round having done something. Source-anchored: the round
runs the game.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


src = (ROOT / "planner/executor.py").read_text()
ck("the position is taken before the round's macro runs",
   "_spot_before = self._spot(self.settle() or obs)\n            ok, trace, clean = self._run_traced(sg, macro," in src)
ck("...and a changed position counts as the round having done something",
   "_did = _did or self._spot(self.settle() or obs) != _spot_before" in src)
ck("...before the spent-macro record is written",
   src.index("_did = _did or self._spot(self.settle() or obs) != _spot_before")
   < src.index('_rec = self._spent_macros.setdefault('))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
