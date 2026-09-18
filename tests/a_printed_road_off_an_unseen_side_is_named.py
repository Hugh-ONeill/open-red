#!/usr/bin/env python3
"""A row for a floor with ground never on screen names a printed road off a
side never on screen when the printed map sends it toward the goal.

Run 27, 2026-09-18: ROUTE_21 was walked only at its southern tip, so under
the footprint it held one way (south); the page said Route 20's east edge
led AWAY from VIRIDIAN_CITY and nothing about Route 21's road north to
PALLET_TOWN, and the run shuttled Route 20 <-> Cinnabar (user: "its
definitly confused where to go next to get back to viridian").

Pinned: named for a printed edge no part of the map has listed, only when
it leads toward a map goal; silent for a known edge, for an edge away from
the goal, and with no map goal. Synthetic."""
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
    ex.explored = {"ROUTE_21|10,88": {"south": {"to": "CINNABAR_ISLAND|10,0"}}}
    ex.frontier = {"ROUTE_21|10,88": ["south"]}
    ex.visits = {"ROUTE_21|10,88": 4, "CINNABAR_ISLAND|10,0": 38}
    return ex


got = fake()._unseen_side_toward_words("ROUTE_21|10,88", "map:VIRIDIAN_CITY")
ck("Route 21's north road is named toward Viridian",
   "its north side has never been on screen, and on the printed map that side is the road to PALLET_TOWN, toward VIRIDIAN_CITY" in got, got)
ck("...and the south edge, already known, is not", "south side" not in got, got)
ex = fake(); ex.frontier["ROUTE_21|10,88"] = ["north", "south"]
ck("a printed edge already listed is not named", ex._unseen_side_toward_words("ROUTE_21|10,88", "map:VIRIDIAN_CITY") == "")
ck("an edge away from the goal is not named",
   fake()._unseen_side_toward_words("ROUTE_21|10,88", "map:CINNABAR_GYM") == "")
ck("no map goal, nothing", fake()._unseen_side_toward_words("ROUTE_21|10,88", "item:SECRET_KEY") == "")
src = (ROOT / "planner/executor.py").read_text()
ck("it rides the unseen-ground row", "+ self._unseen_side_toward_words(_m, target)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
