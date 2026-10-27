#!/usr/bin/env python3
"""A door answered by a box on screen does not say "map->None".

Run 67, 2026-10-27, Safari Zone: use_warp(14,25) in SAFARI_ZONE_CENTER put
the party at the gate's "Leaving early?", read with no map, and the round
said "ok (map->None, moved, warped) — that was the door you came in by ...
you are back on None|None, where you came from". The model took the same
door four times "to enter the main Safari Zone area".

Pinned (source shape; the path runs inside the round loop): a None map is
said as a box on screen, not as a map; the came-in-by line names where you
came from instead of None.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner" / "executor.py").read_text()
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ck("a None map is said as a box on screen",
   'if before[0] != after[0] and after[0] is None:' in src
   and '"a box is open on screen, so the map you are "' in src)
ck("...and a real map change still reads map->X",
   'elif before[0] != after[0]:\n                    chg.append(f"map->{after[0]}")' in src)
ck("the came-in-by line never lands on None",
   'if _land.startswith("None"):' in src and '_land = str(_arr_snap[1] or _land)' in src)

bad = [c for c in checks if not c[1]]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok else f"\n      {str(d)[:300]}"))
print(f"{len(checks) - len(bad)}/{len(checks)} checks pass")
sys.exit(1 if bad else 0)
