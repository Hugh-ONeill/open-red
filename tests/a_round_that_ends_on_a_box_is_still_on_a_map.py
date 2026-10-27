#!/usr/bin/env python3
"""A round that ends with a box on screen is charged like any other.

Run 67, 2026-10-27, Safari Zone: "Leaving early?" and the PA's time-up ended
rounds with no map in the snapshot, and the step's spend rules all key on the
map, so those rounds were never spent; navigate_to_secret_house ran 27 rounds
with 7 spent, gate -> park -> time up -> gate.

Pinned: a mapless snapshot takes the map the party last stood on; a snapshot
with a map is unchanged; with no map ever seen it stays None; both round
snapshots go through it.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = E.Executor.__new__(E.Executor)
ex._last_mapped_obs = {"map": {"id": "SAFARI_ZONE_CENTER"}}
boxed = E.Executor._snapshot({"mode": "dialog", "party": [], "flags": [], "bag": {}})
ck("a box on screen reads no map", boxed[0] is None, boxed)
s = ex._boxed_map(boxed)
ck("...and stands on the last map", s[0] == "SAFARI_ZONE_CENTER" and s[1:] == boxed[1:], s)
on = E.Executor._snapshot({"map": {"id": "SAFARI_ZONE_GATE"}, "player": {"x": 3, "y": 2}})
ck("a snapshot with a map is unchanged", ex._boxed_map(on) == on)
ex._last_mapped_obs = None
ck("with no map ever seen it stays None", ex._boxed_map(boxed)[0] is None)
src = (ROOT / "planner/executor.py").read_text()
ck("both round snapshots go through it",
   "sig0 = self._boxed_map(self._snapshot(start))" in src
   and "sig1 = self._boxed_map(self._snapshot(cur))" in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
