#!/usr/bin/env python3
"""A crossing that rolls you back onto the map you left is not a crossing.

Run 69, 2026-10-31, Route 18. Its north seam is the foot of Cycling Road:
the party crossed onto ROUTE_17, the slope rolled the bike straight back
down across the seam, and it came to rest on ROUTE_18 where it began. cross
said "ok (crossed — now on ROUTE_18 at (10,0) (from ROUTE_18 (10,0), via the
gap at (10,0)))", the seam was never filed, and explore took it again every
round (enter_fuchsia_city r5-r8).

Pinned: every success return of the cross op goes through cross_done, which
reports ending on the starting map as a failure that names the far map it
reached and the cell it came back to.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
LUA = (ROOT / "harness/shim.lua").read_text()
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ck("no success return bypasses the check", "return true, crossed_at()" not in LUA)
i = LUA.index("local function cross_done()")
blk = LUA[i:i + 900]
ck("cross_done compares the end map with the start map",
   "if (ow.map and ow.map.id) == startMap then" in blk)
ck("...and fails, naming the far map and where it came back to",
   "return false, (\"crossed %s onto %s, and the ground there carried you \"" in blk)
ck("...the far map is read before the landing settles",
   blk.index("local far = ow.map and ow.map.id") < blk.index("local msg = crossed_at()"))
ck("the three success paths use it", LUA.count("return cross_done()") == 3)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
