#!/usr/bin/env python3
"""A LAST_MAP door is filed in door_dests as LAST_MAP, not by the outdoor
map the shim resolved it to, so a walk through it is not dropped.

Run 62, 2026-10-24: every ROUTE_22_GATE warp is LAST_MAP in the map data;
the shim publishes them by the last outdoor map stood on (ROUTE_22) with
returns=true. door_dests filed the north door (4,0) as ROUTE_22, the walk
through it to ROUTE_23 was dropped (transition_dropped_contradicts_door),
and `go` from Route 23 answered "no walked way ... is known" with the gate's
door two tiles away.

Pinned: a returns warp is filed LAST_MAP; a plain warp keeps its map; the
load-time dropper leaves a LAST_MAP door's edge alone; the recorder's
contradiction check skips LAST_MAP.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

src = (ROOT / "planner" / "executor.py").read_text()
ck("a returns warp is filed LAST_MAP",
   '"LAST_MAP" if _w.get("returns") else str(_w.get("dest")))' in src)
ck("the recorder's contradiction check skips LAST_MAP",
   'str(_known) not in ("LAST_MAP", "UNKNOWN", "None")' in src)

ex = {"ROUTE_22_GATE|4,0": {"4,0": {"to": "ROUTE_23|10,104", "n": 1},
                           "4,7": {"to": "ROUTE_22|8,5", "n": 2}}}
n = E.drop_edges_contradicting_doors(ex, {"ROUTE_22_GATE": {
    "4,0": "LAST_MAP", "5,0": "LAST_MAP", "4,7": "LAST_MAP", "5,7": "LAST_MAP"}})
ck("the load-time dropper leaves a LAST_MAP door's walk alone",
   n == 0 and "4,0" in ex["ROUTE_22_GATE|4,0"], ex)
ex2 = {"ROUTE_22_GATE|4,0": {"4,0": {"to": "ROUTE_23|10,104", "n": 1}}}
n2 = E.drop_edges_contradicting_doors(ex2, {"ROUTE_22_GATE": {"4,0": "ROUTE_22"}})
ck("...while a door filed by a resolved name dropped it (the bug)", n2 == 1)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
