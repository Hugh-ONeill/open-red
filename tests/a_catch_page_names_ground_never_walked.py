#!/usr/bin/env python3
"""A catch step's page names the ground the run has never set foot on: the
edges and doors of maps it has walked that it has never taken.

The catch page said "the answer is different ground" and named only ground
already tried: where the party stood, the maps it had fought on, the maps
it had walked through. Run 28's leg 5 (a WATER or GRASS type, CHARMANDER in
hand) searched Route 2 and Viridian Forest four plans running, while the
west edge of VIRIDIAN_CITY, never crossed on the run's own record, went
unmentioned (user, 2026-09-19: "what if rt22 did have a grass pokemon itd
still be getting ignored because it hasnt tried to look there").

Pinned: edges and doors never taken come from the one definition
(_frontier_left); they are named by region, the way the rest of the page
names places; edges and doors are two lists, each nearest first by walked
route; a route that is not known is said; the floor underfoot is left to
its own ways-out list; no destination is named; nothing untaken, no line;
the catch branch carries the line wherever the party stands. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


class Ex(E.Executor):
    """A map record and routes, nothing else."""

    def __init__(self, left, hops, here="VIRIDIAN_FOREST|1,0"):
        self.explored = {r: {} for r in left}
        self.frontier = {r: list(v) for r, v in left.items()}
        self._left, self._hops, self._here = left, hops, here

    def _where(self, obs):
        return self._here

    def _frontier_left(self, region):
        return list(self._left.get(region) or [])

    def _route(self, frm, to, avoid=None):
        h = self._hops.get(to)
        return None if h is None else ["x"] * h


LEFT = {"VIRIDIAN_CITY|17,0": ["west", "23,25"],
        "PALLET_TOWN|10,0": ["south"],
        "PEWTER_CITY|4,2": ["east", "13,25", "16,17"],
        "ROUTE_2|3,43": ["north"],
        "VIRIDIAN_FOREST|1,0": ["south", "2,1"],
        "ROUTE_1|10,0": []}
HOPS = {"VIRIDIAN_CITY|17,0": 3, "PALLET_TOWN|10,0": 5,
        "PEWTER_CITY|4,2": 2}
ex = Ex(LEFT, HOPS)
w = ex._never_walked_note({"map": {"id": "VIRIDIAN_FOREST"}})
ck("the line is there, and says what it is",
   w.startswith("GROUND YOU HAVE NEVER SET FOOT ON, on maps you have walked"), w)
ck("an edge never crossed is named by its region",
   "the west edge of VIRIDIAN_CITY|17,0 (never crossed, 3 walked leg(s) away)"
   in w, w)
ck("edges come nearest first",
   w.index("east edge of PEWTER_CITY") < w.index("west edge of VIRIDIAN_CITY")
   < w.index("south edge of PALLET_TOWN"), w)
ck("a route that is not known is said",
   "the north edge of ROUTE_2|3,43 (never crossed, no walked route from here "
   "is known)" in w, w)
ck("doors are their own list, nearest first",
   "Doors never taken: a door at (13,25) in PEWTER_CITY|4,2" in w
   and w.index("Map edges never crossed") < w.index("Doors never taken"), w)
ck("the floor underfoot is left to its own ways-out list",
   "VIRIDIAN_FOREST|1,0" not in w)
ck("a region with nothing left says nothing", "ROUTE_1" not in w)
ck("no destination is named",
   not any(d in w for d in ("ROUTE_22", "ROUTE_21", "ROUTE_3", "->")))
ck("the choice is left to the model", "which is worth the walk is yours to read" in w)
ck("nothing untaken, no line",
   Ex({"ROUTE_1|10,0": []}, {})._never_walked_note({"map": {}}) == "")

many = {f"ROUTE_{i}|0,0": ["north"] for i in range(10)}
wm = Ex(many, {f"ROUTE_{i}|0,0": i + 1 for i in range(10)}
        )._never_walked_note({"map": {}})
ck("a long list is cut, and says how many more", "; and 4 more" in wm, wm)

src = (ROOT / "planner/executor.py").read_text()
blk = src[src.index("    def _never_walked_note"):
          src.index("    def _wild_elsewhere_fought_note")]
ck("it reads the one definition of an exit never taken",
   "self._frontier_left(r)" in blk)
ck("the catch branch carries it wherever the party stands",
   "_nw = self._never_walked_note(obs)\n            if _nw:\n"
   "                lines.append(_nw)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
