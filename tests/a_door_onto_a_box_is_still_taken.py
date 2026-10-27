#!/usr/bin/env python3
"""A door that opens onto a box is counted as taken, not left "untried".

Run 67, 2026-10-27: SAFARI_ZONE_CENTER's (14,25) opens on the gate's
"Leaving early?", read with no map, so note_transition dropped it as
transition_dropped_no_region every time and the page kept calling it "the
only untried exit"; the model took it round after round.

Pinned: such a door is booked as a try that left no evidence; twice in one
world it is spent (so not untried); a seam or a box on the way IN books
nothing; an ordinary door still writes its edge.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = E.Executor.__new__(E.Executor)
ex._exit_tries = {}
ex._cut_down = None
ex.log = lambda *a, **k: None
ex._world_mark = lambda o: ("m",)
ex._mark_now = ("m",)
ex._where = lambda o: (f"{(o.get('map') or {}).get('id')}|22,10"
                       if (o or {}).get("map") else "None|None")
CEN = {"map": {"id": "SAFARI_ZONE_CENTER"}, "player": {"x": 14, "y": 24}}
BOX = {"mode": "dialog"}
step = {"op": "use_warp", "x": 14, "y": 25}

ex.note_transition(CEN, step, BOX)
ck("one try onto the box is booked", ex._exit_tries["SAFARI_ZONE_CENTER|22,10"]["14,25"]["n"] == 1,
   ex._exit_tries)
ex.note_transition(CEN, step, BOX)
ck("...twice in one world, it is spent", "14,25" in ex._spent_exits("SAFARI_ZONE_CENTER|22,10"))
ex._mark_now = ("a pickup later",)
ck("...and stays spent when a pickup moves the world mark",
   "14,25" in ex._spent_exits("SAFARI_ZONE_CENTER|22,10"))
ex2 = E.Executor.__new__(E.Executor)
ex2.__dict__.update({k: v for k, v in ex.__dict__.items()
                     if k not in ("_exit_tries", "_boxed_doors")})
ex2._exit_tries = {}
ex2.note_transition(CEN, {"op": "cross", "dir": "north"}, BOX)
ck("a seam onto a box books nothing", ex2._exit_tries == {}, ex2._exit_tries)
ex2.note_transition(BOX, step, CEN)
ck("a box on the way in books nothing", ex2._exit_tries == {}, ex2._exit_tries)

src = (ROOT / "planner/executor.py").read_text() + (ROOT / "planner/ledger.py").read_text()
ck("a boxed door is not said to stop you before the doorway",
   src.count("time a box opened on screen before any map") == 2)

ck("the boxed doors are saved and loaded",
   '"boxed_doors": getattr(self, "_boxed_doors", None) or {},' in src
   and 'self._boxed_doors = data.get("boxed_doors") or {}' in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
