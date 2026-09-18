#!/usr/bin/env python3
"""A row for a floor with ground never on screen names another walked map
whose edge, seen and never crossed, leads onto that floor, with that map's
walked distance to a map goal. Never the printed map: the run holds no
TOWN_MAP.

Run 27, 2026-09-18: ROUTE_21 was walked only at its southern tip, so it held
one way (south); PALLET_TOWN's south edge had been on screen since leg 1,
"to ROUTE_21", never crossed. Nothing joined them, and the run shuttled
Route 20 <-> Cinnabar (user: "its definitly confused where to go next to
get back to viridian").

Pinned: named from a seen, untaken frontier edge whose map is this floor's,
only with a walked route to the goal; silent for a crossed edge, with no
walked route, with no map goal, and never worded as the printed map."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def fake():
    ex = object.__new__(E.Executor)
    ex.explored = {"ROUTE_21|10,88": {"south": {"to": "CINNABAR_ISLAND|10,0"}},
                   "PALLET_TOWN|10,0": {"north": {"to": "ROUTE_1|10,0"}}}
    ex.frontier = {"ROUTE_21|10,88": ["south"],
                   "PALLET_TOWN|10,0": ["12,11", "north", "south"]}
    ex.visits = {"ROUTE_21|10,88": 4, "PALLET_TOWN|10,0": 3, "VIRIDIAN_CITY|0,0": 9}
    ex._route = lambda a, b: (["north", "north"] if (a, b) == ("PALLET_TOWN|10,0", "VIRIDIAN_CITY|0,0") else None)
    return ex


got = fake()._unseen_side_toward_words("ROUTE_21|10,88", "map:VIRIDIAN_CITY")
ck("Pallet's seen south edge onto Route 21 is named, with Pallet's walked distance to Viridian",
   "PALLET_TOWN's south edge, which you have seen lead onto ROUTE_21 and never crossed, is on ground 2 walked leg(s) from VIRIDIAN_CITY" in got, got)
ck("...never as the printed map", "printed map" not in got, got)
ex = fake(); ex.explored["PALLET_TOWN|10,0"]["south"] = {"to": "ROUTE_21|10,0"}
ck("a crossed edge is not named", ex._unseen_side_toward_words("ROUTE_21|10,88", "map:VIRIDIAN_CITY") == "")
ex = fake(); ex._route = lambda a, b: None
ck("no walked route to the goal, nothing", ex._unseen_side_toward_words("ROUTE_21|10,88", "map:VIRIDIAN_CITY") == "")
ck("no map goal, nothing", fake()._unseen_side_toward_words("ROUTE_21|10,88", "item:SECRET_KEY") == "")
src = (ROOT / "planner/executor.py").read_text()
ck("it rides the unseen-ground row", "+ self._unseen_side_toward_words(_m, target)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
