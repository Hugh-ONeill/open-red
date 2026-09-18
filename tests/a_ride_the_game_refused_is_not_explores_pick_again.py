#!/usr/bin/env python3
"""A water ride the game refused from a part is not explore's pick again
there, so explore goes on to the untried ways out.

Run 27, 2026-09-18, Seafoam B4F: the currents turn SURF away at the mount
point, the ride failed "SURF was REFUSED BY THE GAME", and explore rode for
the same water frontier every round while a walkable ladder up at (11,7),
never taken, sat beside it (user: "is it still trying to explore/sweep
fruitlessly? theres an untaken ladder right next to it?").

Pinned: a ride whose trace says the game refused it is kept against the
part and the world state; while kept, explore skips the ride (and says so
in the journal) and falls through to the rest of its order. Source-anchored:
the step runs the game.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


src = (ROOT / "planner/executor.py").read_text()
i = src.index('        _fw = _m.get("frontier_water") or []')
blk = src[i:i + 11000]
ck("a refused ride is kept against the part and the world state",
   '_ride_key = (self._where(obs), str(self._world_mark(obs)))' in blk
   and 'if any("REFUSED BY THE GAME" in str(t) for t in tr):' in blk
   and "| {_ride_key})" in blk)
ck("...and while kept, explore does not ride there again",
   "and not _ride_refused" in blk and 'step="ride_refused"' in blk)
ck("...falling through to the rest of its order (stale walls, then the ledger's exits)",
   blk.index("and not _ride_refused") < blk.index('_fs = _m.get("frontier_stale") or []')
   < blk.index("cands = ledger.build(self, obs, target,"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
