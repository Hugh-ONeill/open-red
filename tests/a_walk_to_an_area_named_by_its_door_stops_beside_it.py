#!/usr/bin/env python3
"""A walk hop to an area named after a doorway stops beside the door.

Run 36, 2026-10-05: Route 23's north part is ROUTE_23|4,31, named after
the first cell the party stood on there, the Victory Road door it had
just come out of. Every walk to it stepped onto (4,31), went into the
cave, and the next hop was abandoned from VICTORY_ROAD_1F.

Pinned: the cell beside the door most stood on (steps.log, this map only)
is chosen; another doorway is never chosen; with no record, the cell
below; a door with doors on every side gives nothing; the walk hop uses it
when the name-cell is a door on the current map. Synthetic."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_tmp = tempfile.mkdtemp()
os.environ["RED_BRIDGE_DIR"] = _tmp
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


log = Path(E.RUN) / "steps.log"
rows = ([("ROUTE_23", 5, 31)] * 2 + [("ROUTE_23", 4, 32)] * 5
        + [("VICTORY_ROAD_1F", 4, 30)] * 9)
log.write_text("".join(f"1.0 {m} {x} {y}\n" for m, x, y in rows))
b = E.Executor._beside_door
ck("the side most stood on, this map only", b("ROUTE_23", 4, 31, {"4,31"}) == (4, 32),
   b("ROUTE_23", 4, 31, {"4,31"}))
ck("never another doorway", b("ROUTE_23", 4, 31, {"4,31", "4,32"}) == (5, 31),
   b("ROUTE_23", 4, 31, {"4,31", "4,32"}))
ck("no record, the cell below", b("CERULEAN_CITY", 10, 10, {"10,10"}) == (10, 11))
ck("doors all round, nothing",
   b("ROUTE_23", 4, 31, {"4,31", "4,32", "4,30", "5,31", "3,31"}) is None)

src = (ROOT / "planner/executor.py").read_text()
ck("the walk hop aims beside a name-cell that is a door here",
   'if f"{_ax},{_ay}" in _doors_here:' in src
   and "_side = self._beside_door(_mid, _ax, _ay, _doors_here)" in src
   and "_ax, _ay = _side" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
