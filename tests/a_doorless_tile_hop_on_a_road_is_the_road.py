#!/usr/bin/env python3
"""A route hop keyed by a tile with no door, toward a map this map has a road
to, is replayed as that road's crossing.

Run 65, 2026-10-24: ROUTE_24|4,4 held "10,35 -> CERULEAN_CITY|20,0" (a seam
crossing filed under its cell) beside "south"; the walked one was routed and
every go from Route 24 to the Cerulean Center ended "the next leg was 10,35
and this map has no such way out of it any more" (run 63's Route 25 "0,9"
the same).

Pinned: a doorless tile hop whose destination map is one of this map's
edges becomes that direction; the engine edge table names Route 24's south.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

src = (ROOT / "planner" / "executor.py").read_text()
i = src.index("# ...AND A TILE WITH NO DOOR, ON A ROAD THE MAP HAS TO THAT")
blk = src[i:i + 1600]
ck("a doorless tile hop looks up the map's roads to its destination",
   "(MAP_EDGES or {}).get(str(_m.get(\"id\") or \"\"))" in blk and "if str(nb) == _nm]" in blk, blk[:600])
ck("...and one road there becomes the hop", "key = _dirs[0]" in blk and "_has = True" in blk)
ck("Route 24's south road is Cerulean in the edge table",
   (E.MAP_EDGES.get("ROUTE_24") or {}).get("south") == "CERULEAN_CITY", E.MAP_EDGES.get("ROUTE_24"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
