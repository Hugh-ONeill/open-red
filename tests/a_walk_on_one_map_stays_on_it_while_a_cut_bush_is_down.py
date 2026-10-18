#!/usr/bin/env python3
"""While a bush the party cut is down, a walk to another part of the same
map does not go there by way of another map; and `go` says the cell it ends
on, not only the area's name.

Run 58, 2026-10-18, Route 16: the run cut the bush at (34,9) and asked to
walk beside SNORLAX. No path; the walk tried the map's other part, which is
reached through the gate, so it left Route 16, the bush grew back, and the
flute was played from (17,5) at nothing. A round before, "go ... now at
ROUTE_16|27,10" was read as standing on (27,10) beside SNORLAX at (26,10);
the party was at (24,4) (user: "its playing kind of stupid around the cut
bush and snorlax"). The pad ride already kept to the map
(a_door_is_not_ridden_while_a_cut_bush_is_down). Synthetic.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = object.__new__(E.Executor)
ex._cut_down = {"map": "ROUTE_16", "xy": ["34,9"]}
obs = {"map": {"id": "ROUTE_16", "objects": []}}
ck("a bush cut on this map and not standing on screen is still down",
   ex._cut_still_down(obs, "ROUTE_16") == "(34,9)", ex._cut_still_down(obs, "ROUTE_16"))
obs2 = {"map": {"id": "ROUTE_16", "objects": [{"name": "CUT_TREE", "x": 34, "y": 9}]}}
ck("...not when it stands on screen again", ex._cut_still_down(obs2, "ROUTE_16") == "")
ck("...nor for another map", ex._cut_still_down(obs, "CELADON_CITY") == "")
through_gate = [("7,3", "ROUTE_16_GATE_1F|0,2"), ("0,3", "ROUTE_16|1,2")]
on_map = [("walk:ROUTE_16|1,2", "ROUTE_16|1,2")]
ck("a route through the gate leaves the map",
   E.Executor._route_leaves_map(through_gate, "ROUTE_16"))
ck("a walk across the map does not", not E.Executor._route_leaves_map(on_map, "ROUTE_16"))

src = (ROOT / "planner/executor.py").read_text()
ck("walk_to's other-part detour keeps to the map while a bush is down",
   "if _kept_cut and self._route_leaves_map(_path, _mid):" in src)
ck("...and says so when it fails",
   "the way there leaves {_mid} and the bush you" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
