#!/usr/bin/env python3
"""A person beside a door in a room the walk cannot reach is not "in the way".

Run 67, 2026-10-27, Saffron Gym after Sabrina: the run stood in a pad cell
walled off from the entrance room, and use_warp(11,15) -- a pad in the
entrance room -- came back "somebody is standing by it: SAFFRONGYM_GYM_GUIDE
at (10,15)". The guide was beside the pad but nowhere near the run; the model
spent rounds pressing trainers "to clear the path" of him.

Pinned (source shape; the walker runs only in the game): the failed walk keeps
the ground it reached, matched to the map and the tile it started from; a
person is named only if they stand on or beside that ground; with no matching
walk the old rule stands.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
lua = (ROOT / "harness" / "shim.lua").read_text()
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ck("the failed walk keeps what it reached, keyed to map and start tile",
   "LAST_BFS = { map = (ow.map or {}).id, x = p.cellX, y = p.cellY, seen = seen }" in lua)
ck("...as a global, the main chunk being at the local limit",
   "\nLAST_BFS = nil\n" in lua and "local LAST_BFS" not in lua)
ck("a blocker must border that ground",
   "and borders_walk(npc) then" in lua
   and "if _lb.seen[(nx + d[1]) .. \",\" .. (ny + d[2])] then return true end" in lua)
ck("a walk from elsewhere is not used",
   "_lb.x == _pl.cellX and _lb.y == _pl.cellY" in lua)
ck("with no matching walk, the old rule stands", "if not _lb then return true end" in lua)
ck("the run's case is on record", "SAFFRONGYM" not in lua or "GYM_GUIDE beside the pad" in lua)

bad = [c for c in checks if not c[1]]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok else f"\n      {str(d)[:300]}"))
print(f"{len(checks) - len(bad)}/{len(checks)} checks pass")
sys.exit(1 if bad else 0)
