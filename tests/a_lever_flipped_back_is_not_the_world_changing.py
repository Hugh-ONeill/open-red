#!/usr/bin/env python3
"""A lever flipped back and forth is not the world changing, for the idle and
dry-leg counts.

Run 67, 2026-10-27, Pokemon Mansion B1F: the switch was pressed and unpressed
round after round; EVENT_MANSION_SWITCH_ON moved the world mark every round,
so the idle streak reset and the dry-leg rule counted each flip as a gain.

Pinned: the progress mark ignores a flag the run has seen switch off again; a
new flag still moves it; the full world mark (strikes, doors) still moves on
the lever; both round comparisons use the progress mark.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = E.Executor.__new__(E.Executor)
ex._toggled_flags = ["EVENT_MANSION_SWITCH_ON"]
on = {"badges": ["A"], "flags": ["EVENT_X", "EVENT_MANSION_SWITCH_ON"], "bag": {"POTION": 1}}
off = {"badges": ["A"], "flags": ["EVENT_X"], "bag": {"POTION": 1}}
new = {"badges": ["A"], "flags": ["EVENT_X", "EVENT_Y"], "bag": {"POTION": 1}}
ck("a lever flip does not move the progress mark", ex._progress_mark(on) == ex._progress_mark(off))
ck("...a new flag still does", ex._progress_mark(new) != ex._progress_mark(off))
ck("...and the full world mark still moves on the lever",
   E.Executor._world_mark(on) != E.Executor._world_mark(off))
src = (ROOT / "planner/executor.py").read_text()
ck("both round comparisons use it",
   "_same_world = (str(self._progress_mark(start))" in src
   and "self._round0_mark = self._progress_mark(start)" in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
