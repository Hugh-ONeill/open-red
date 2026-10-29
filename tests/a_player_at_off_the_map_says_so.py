#!/usr/bin/env python3
"""A player_at condition that no cell of the current map can meet is said
under DONE_WHEN, from the map's own width and height.

Run 68, 2026-10-29: Vermilion Gym is 10x18; the step was banked as
{"player_at":{"x":12,"y":4,"radius":2}}, the round explored for a cell that
does not exist, and then walked out of the gym "to reset", which reset the
two locks it had just opened.

Pinned: off the map is said with the map's span; on it, or at its edge
within the radius, says nothing; no size or no player_at says nothing; and
the line sits under DONE_WHEN. Synthetic.
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
obs = {"map": {"id": "VERMILION_GYM", "width": 10, "height": 18}}
w = ex._player_at_off_map_note({"player_at": {"x": 12, "y": 4, "radius": 2}}, obs)
ck("off the map is said, with the span",
   "No cell of VERMILION_GYM is within 2 of (12,4): this map runs x 0-9 and y 0-17" in w, w)
ck("...a cell within the radius at the edge is not",
   ex._player_at_off_map_note({"player_at": {"x": 11, "y": 4, "radius": 2}}, obs) == "")
ck("...nor one on the map", ex._player_at_off_map_note({"player_at": {"x": 5, "y": 1, "radius": 1}}, obs) == "")
ck("...the default radius is the predicate's (4)",
   ex._player_at_off_map_note({"player_at": {"x": 13, "y": 4}}, obs) == ""
   and "within 4" in ex._player_at_off_map_note({"player_at": {"x": 14, "y": 4}}, obs))
ck("no size, nothing", ex._player_at_off_map_note({"player_at": {"x": 99, "y": 4}}, {"map": {"id": "X"}}) == "")
ck("no player_at, nothing", ex._player_at_off_map_note({"map": "VERMILION_GYM"}, obs) == "")
src = (ROOT / "planner" / "executor.py").read_text()
ck("it is said under DONE_WHEN", 'f"{self._player_at_off_map_note(done, obs)}"' in src
   and src.index('f"{self._area_ids_note(done, obs)}"') < src.index('f"{self._player_at_off_map_note(done, obs)}"'))
bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
sys.exit(1 if bad else 0)
