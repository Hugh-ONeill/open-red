#!/usr/bin/env python3
"""A way that turned the run back says when the very same words, said at
another way, have let the run through since.

Run 68, 2026-10-29: Route 7's gate guard ("I'm on guard duty. Gee, I'm
thirsty, though!") stayed on the list as standing; Route 8's guard had said
the same and let the party through once EVENT_GAVE_GUARDS_DRINK fired, and
the run wrote "the direct route via Route 7 is blocked by a guard who wants
FRESH_WATER" and went shopping for water.

Pinned: the sibling cleared after this row was written is named; one
cleared before it is not (that one let you through and this still said
no); different words are not; the clear is timed. Synthetic.
"""
import os, sys, tempfile
from pathlib import Path
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
T = '"I\'m on guard duty. Gee, I\'m thirsty, though!"'
ex = E.Executor.__new__(E.Executor)
ex._toggled_flags = []
ex._mark_now = [3, "a", "b"]
ex._flags_now = ["EVENT_GAVE_GUARDS_DRINK"]
seven = {"where": "ROUTE_7_GATE|0,4", "what": T, "t": 100.0, "cleared": False,
         "mark": [3, "x", "b"], "flags_then": []}
eight = {"where": "ROUTE_8_GATE|0,3", "what": T, "t": 50.0, "cleared": True,
         "cleared_t": 200.0}
ex.blockers = {"ROUTE_7_GATE|0,4|5,3": seven, "ROUTE_8_GATE|0,3|0,3": eight}
w = ex._since_words(seven)
ck("the same words passed elsewhere since are named",
   "the same words turned you back at ROUTE_8_GATE|0,3, and that way has let you through since" in w, w)
eight["cleared_t"] = 90.0
w = ex._since_words(seven)
ck("...not when that way let you through BEFORE this one said no", "same words" not in w, w)
eight["cleared_t"] = 200.0
eight["what"] = '"A sleeping POKeMON blocks the way!"'
ck("...nor different words", "same words" not in ex._since_words(seven))
src = (ROOT / "planner" / "executor.py").read_text()
ck("a clear is timed", 'b["cleared_t"] = round(time.time(), 1)' in src)
bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
sys.exit(1 if bad else 0)
