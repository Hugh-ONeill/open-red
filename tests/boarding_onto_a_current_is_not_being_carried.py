#!/usr/bin/env python3
"""A step that boards onto a current from the shore is not carried; only a
step taken while riding is, as the engine does it.

Run 62, 2026-10-23: from Seafoam B3F part 1,0 (the landing of B4F's (11,7)
ladder) the water flood reached 209 cells to the walk's 208 and the (25,14)
ladder up read unreachable, with nothing said about the water: the fill
treated every step onto the entry current (15,8) as carried to the south
door, while the engine (OverworldController checkSeafoamCurrent) carries
only a rider whose step ends there. Boarding at (15,7)->(15,8) is not such
a step, and the walker swims on east to (26,8). Run 60 took that way out
because explore still had unseen water there; run 62's was all seen, so
nothing sent it, and it looped two legs. Probed on run 62's 21:40 save:
before, (25,14) had no by_water; after, by_water is True, and
walk_to(26,8, surf) then use_warp(25,14) lands on B2F both times.

Pinned (source; the fill needs the live engine): the forced-cell branch of
warp_reach asks whether the step starts on water, and the engine still
carries only while surfing.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = Path.home() / "Developer/gen1recomp"
checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


shim = (ROOT / "harness/shim.lua").read_text()
i = shim.index("function warp_reach(G, no_ledges, surf, start)")
j = shim.index("\nend\n", i)
fill = shim[i:j]
ck("the forced-cell branch needs the step to start on water",
   "elseif FORCED and FORCED[key(nx, ny)]\n                 and real_water(G, ow.map, cur.x, cur.y) then" in fill)
ck("...and still carries a ridden step to its landing",
   'FORCED[key(nx, ny)] == "carried"' in fill and "seafoam_landing(G, nx, ny)" in fill)
eng = GEN / "src/world/OverworldController.lua"
if eng.exists():
    e = eng.read_text()
    k = e.find("function OverworldState:checkSeafoamCurrent()")
    blk = e[k:k + 2500]
    ck("the engine carries only a surfing player (what this mirrors)",
       k > 0 and "if not p.surfing then return false end" in blk)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
