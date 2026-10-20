#!/usr/bin/env python3
"""A world state the step has already been in is not "something changed".

Run 59, 2026-10-20, Pokemon Mansion: each statue press flipped
EVENT_MANSION_SWITCH_ON, so every repeat of the same plan was echoed
"-> something changed" for hours (user: "its also not getting that its
done exactly what its planning to do for the past however many hours with
no changes except the switch state"). Source pins.
"""
from pathlib import Path
src = (Path(__file__).resolve().parents[1] / "planner/executor.py").read_text()
checks = [
    ("each subgoal keeps the fingerprints it has been in", "self._fp_seen = set()" in src),
    ("only one not seen before this subgoal is a move",
     "_new_fp = _fp != self._stale_fp and _fp not in _fps" in src
     and "_moved_world = bool(_fresh_ground or _looked or _new_fp)" in src),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
