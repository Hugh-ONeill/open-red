#!/usr/bin/env python3
"""A map's edge "comes into view" only where a step off it would cross.

Run of record 4, 2026-09-25, Cerulean: a sweep stopped on "came into view:
this map's edge to the south" at (37,31), the city's south-east corner. The
city meets Route 5 along twenty of its forty bottom cells, ten in; the
corner's bottom row leads nowhere. The model sent cross south, was told the
seam could not be reached over seen ground, and wrote that the CUT tree at
(19,28) blocked the way it had already walked past (user: "sweep just
failed weirdly and now it thinks the cut tree is blocking it despite being
on the other side of it").

Pinned: seam_open checks the cell against the neighbour's span at its
offset before landing_ok, which clamps; the sweep's edge sighting and its
"seen before" both use it; nothing else about the report changed.
Source-anchored: the shim runs in the game."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


shim = (ROOT / "harness/shim.lua").read_text()
so = shim[shim.index("local function seam_open(G, d, x, y)"):]
so = so[:so.index("\nend\n") + 5]
ck("seam_open checks the neighbour's span at its offset",
   "local off = (conn.offset or 0) * 2" in so
   and "if along < 0 or along >= span then return false end" in so
   and "(dest.width or 0) * 2" in so and "(dest.height or 0) * 2" in so, so)
ck("...and only then asks landing_ok", so.rstrip().endswith(
   "return landing_ok(G, dirw, x, y)\nend"), so[-120:])
ck("...defined after landing_ok, which it calls",
   shim.index("local function landing_ok(") < shim.index("local function seam_open("))
sw = shim[shim.index("function OPS.sweep(G, c)"):]
sw = sw[:sw.index("\nfunction OPS.", 10)]
for d, cond in (("north", "y == 0"), ("south", "y == H - 1"),
                ("west", "x == 0"), ("east", "x == W - 1")):
    ck(f"the sweep's {d} edge counts only where it crosses",
       f'if {cond} and seam_open(G, "{d}", x, y) then edge.{d} = true end' in sw)
    bcond = cond.replace("x", "bx").replace("y", "by")
    ck(f"...and so does the {d} edge seen before",
       f'if {bcond} and seam_open(G, "{d}", bx, by) then edge_before.{d} = true end' in sw)
ck("no bare edge test is left in the sweep",
   not re.search(r"if (y == 0|y == H - 1|x == 0|x == W - 1) then edge\.", sw))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
