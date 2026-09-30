#!/usr/bin/env python3
"""A doorway that is a wall in the map's current state is said to be one.

Mansion 1F's east doorway became a gate block when a statue was pressed; the
shim said "nothing can stand ON 26,27 ... Walk to (26,26) and act from
there", then the same of the twin tile, for fifteen rounds (run 19,
2026-09-30). A door fires only from standing on it.

Source checks (harness/shim.lua).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


sh = (ROOT / "harness/shim.lua").read_text()
uw = sh[sh.index("function OPS.use_warp("):]
uw = uw[:uw.index("\nfunction ", 10)]
ck("use_warp refuses a doorway the live grid calls a wall, before walking",
   "not m0:isWalkableCell(c.x, c.y)" in uw and "is a WALL right now" in uw)
ck("...unless the party is surfing onto water",
   "not (p.surfing and m0.isWaterCell and m0:isWaterCell(c.x, c.y))" in uw)
ck("...and says a door fires only from ON it", "A door fires only from standing ON it" in uw)
ck("...naming no switch and no other way out",
   "switch" not in uw[uw.index("is a WALL right now") - 400:uw.index("is a WALL right now") + 300].lower())
bf = sh[sh.index("local function bfs_dir_pass("):]
bf = bf[:bf.index("\nlocal function ", 10)]
ck("the no-path message tells a walled doorway apart from a person or sign",
   "ow.map:warpAtCell(tx, ty)" in bf and "is a WALL right" in bf and "and act from there" in bf)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
