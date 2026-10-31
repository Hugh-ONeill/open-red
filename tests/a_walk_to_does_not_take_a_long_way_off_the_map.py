#!/usr/bin/env python3
"""A walk_to on this map does not take a long way off it unasked.

Run 69, 2026-10-31, Route 12. walk_to(10,63), the cell past SNORLAX, had no
path, so the executor walked to the map's far part (ROUTE_12|0,61) the
only way the record had it: Lavender, Rock Tunnel and Route 9, some twenty
legs, until a bush on Route 9 cut it off; twice. The long-go rule already
says such a walk before it is made. Now a via-region route of six legs or
more that leaves the map is not walked: the trace names the part, the leg
count, and the go that walks it.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
SRC = (ROOT / "planner/executor.py").read_text()
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

i = SRC.index('self.log("walk_to_via_region", subgoal=sg.get("id"),')
blk = SRC[i - 2200:i]
ck("a long off-map route is checked before the walk",
   "if len(_path) >= 6 and self._route_leaves_map(_path, _mid):" in blk)
ck("...is not walked and says so", "NOT \"\n" in blk or "— NOT \"" in blk or "NOT WALKED" in blk)
ck("...names the go that walks it", '","long":true} walks it' in blk)
ck("...and is logged", 'self.log("walk_to_via_region_long"' in blk)
ck("a short or same-map route still walks",
   blk.index("_route_leaves_map(_path, _mid):\n                            trace.append") > 0)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
