#!/usr/bin/env python3
"""A one-off fight the game has recorded as over is said beside a plan that
names it.

Run 67, 2026-10-28: both Snorlax beaten (EVENT_BEAT_ROUTE12_SNORLAX,
EVENT_BEAT_ROUTE16_SNORLAX), and the run wrote "the path south from Route 16
is blocked by Snorlax ... I will use the Poke Flute" round after round; the
hints said he was gone, far from the plan.

Pinned: named by its last word, the fired flag is said; trainer flags
(a number last) and an unnamed fight are not. Synthetic.
"""
import os, sys, tempfile
from pathlib import Path
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
ex = E.Executor.__new__(E.Executor)
o = {"flags": ["EVENT_BEAT_ROUTE16_SNORLAX", "EVENT_BEAT_ROUTE_9_TRAINER_2"]}
n = ex._beaten_named_note("Route 16 is blocked by Snorlax; I will wake him", o)
ck("a named one-off fight is said over", "ROUTE16_SNORLAX" in n and "has fired" in n, n)
ck("...trainer flags are not", "TRAINER" not in n, n)
ck("a plan that names none says nothing",
   ex._beaten_named_note("I will walk to Cinnabar Island", o) == "")
src = (ROOT / "planner" / "executor.py").read_text()
ck("it rides the round's results",
   "_gonen = self._beaten_named_note(self._plan_said, self.settle() or obs)" in src)
bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
sys.exit(1 if bad else 0)
