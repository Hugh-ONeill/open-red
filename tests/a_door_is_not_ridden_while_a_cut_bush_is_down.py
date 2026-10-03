#!/usr/bin/env python3
"""While a bush the party cut is down on this map, no fallback rides a door
off it.

Run 36, 2026-10-03: Celadon's bush at (35,32) opens the way round to the gym
door (12,27) over ground not yet on screen; use_warp(12,27) could not walk
there over SEEN ground, so the recross rode a door used before, out of the
city and back, and the bush grew back. Three cuts, three rides (user: "its
ignoring the newly opened ground after cutting and leaving"). Verified in
game on the run's leg-24 checkpoint: cut, one sweep (144 cells), the door is
reachable and use_warp lands in CELADON_GYM. Synthetic below."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = object.__new__(E.Executor)
ex._where = lambda o: "CELADON_CITY|2,1"
ex._cut_down = {"map": "CELADON_CITY", "xy": ["35,32"]}
obs = {"map": {"id": "CELADON_CITY", "objects": []}}
r = ex._pad_recross_for_target(obs, {"id": "s"}, 12, 27)
ck("with the bush down, no door is ridden", r is None and ex._last_pad_kept_cut == "(35,32)",
   ex._last_pad_kept_cut)
obs2 = {"map": {"id": "CELADON_CITY",
                "objects": [{"name": "CUT_TREE", "x": 35, "y": 32}]}}
ex._recrossing = True        # stop right after the guard: only the guard is under test
ex._pad_recross_for_target(obs2, {"id": "s"}, 12, 27)
ck("a bush standing again on screen does not hold the ride back",
   ex._last_pad_kept_cut == "", ex._last_pad_kept_cut)
del ex._recrossing
ex._cut_down = {"map": "ROUTE_9", "xy": ["5,8"]}
ex._recrossing = True
ex._pad_recross_for_target(obs, {"id": "s"}, 12, 27)
ck("a bush down on another map does not hold this one back", ex._last_pad_kept_cut == "")

src = (ROOT / "planner/executor.py").read_text()
ck("leaving the map forgets the bush (note_transition)",
   "if _bm and _am and _bm != _am:\n                self._cut_down = None" in src)
ck("the cut writes it down", '_down = self._cut_down = {"map": mid, "xy": []}' in src)
ck("the refused ride is said in the round",
   "no door was ridden to try from" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
