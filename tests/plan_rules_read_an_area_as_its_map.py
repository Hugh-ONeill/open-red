#!/usr/bin/env python3
"""The prize-room and emptied-floor plan rules read an area condition as
its map (run 68 leg 35: GAME_CORNER_PRIZE_ROOM|0,3 slipped past both).
Source pins."""
from pathlib import Path
src = (Path(__file__).resolve().parents[1] / "planner/author.py").read_text()
checks = [
    ("the prize-room rule", 'if not _m2 and isinstance(_dw2, dict) and isinstance(_dw2.get("area"), str):' in src),
    ("the emptied-floor rule", 'elif isinstance(_dw4.get("area"), str):' in src),
    ("...inside any_of too", 'elif isinstance(_alt, dict) and isinstance(_alt.get("area"), str):' in src),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
