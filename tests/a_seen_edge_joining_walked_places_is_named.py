#!/usr/bin/env python3
"""A way seen and never crossed that joins two walked places is named when
the walked legs through it beat the walked way to the goal already known.
Never the printed map: the run holds no TOWN_MAP.

Run 27, 2026-09-18: ROUTE_21 was walked only at its southern tip, and
PALLET_TOWN's south edge had been on screen since leg 1, "to ROUTE_21",
never crossed. Nothing joined them; the only walked way from Cinnabar to
Viridian was 15 legs back through Seafoam, and the run shuttled Route 20 <->
Cinnabar (user: "its definitly confused where to go next to get back to
viridian").

Pinned: named from a seen, untaken frontier edge onto a walked map, with
walked legs from here and to the goal; silent when it is no shorter than the
known way, for a crossed edge, onto a map never walked, and never worded as
the printed map; rides the page beside the route line. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ROUTES = {("CINNABAR_ISLAND|10,0", "VIRIDIAN_CITY|0,0"): 15,
          ("PALLET_TOWN|10,0", "VIRIDIAN_CITY|0,0"): 2,
          ("CINNABAR_ISLAND|10,0", "ROUTE_21|10,88"): 1}


def fake(routes=ROUTES):
    ex = object.__new__(E.Executor)
    ex.explored = {"ROUTE_21|10,88": {"south": {"to": "CINNABAR_ISLAND|10,0"}},
                   "PALLET_TOWN|10,0": {"north": {"to": "ROUTE_1|10,0"}},
                   "CINNABAR_ISLAND|10,0": {"north": {"to": "ROUTE_21|10,88"}}}
    ex.frontier = {"ROUTE_21|10,88": ["south"],
                   "PALLET_TOWN|10,0": ["12,11", "north", "south"],
                   "CINNABAR_ISLAND|10,0": ["north", "east"]}
    ex.visits = {"ROUTE_21|10,88": 4, "PALLET_TOWN|10,0": 3,
                 "VIRIDIAN_CITY|0,0": 9, "CINNABAR_ISLAND|10,0": 38}
    ex._route = lambda a, b: (["x"] * routes[(a, b)] if (a, b) in routes else None)
    return ex


got = fake()._seen_edge_joins_line("CINNABAR_ISLAND|10,0", "VIRIDIAN_CITY")
ck("Pallet's seen south edge onto Route 21 is named with the walked legs on both sides",
   "PALLET_TOWN's south edge leads onto ROUTE_21 (you saw it from PALLET_TOWN). ROUTE_21 is 1 walked leg(s) from here, and PALLET_TOWN is 2 walked leg(s) from VIRIDIAN_CITY; the walked way to VIRIDIAN_CITY you do know is 15 leg(s)." in got, got)
ck("...and says whether the walked ground reaches the edge is not known",
   "Whether the ground of ROUTE_21 you have walked reaches that edge is not known" in got, got)
ck("...never as the printed map", "printed map" not in got, got)
r2 = dict(ROUTES); r2[("CINNABAR_ISLAND|10,0", "VIRIDIAN_CITY|0,0")] = 4
ck("no shorter than the walked way known, nothing",
   fake(r2)._seen_edge_joins_line("CINNABAR_ISLAND|10,0", "VIRIDIAN_CITY") == "")
ex = fake(); ex.explored["PALLET_TOWN|10,0"]["south"] = {"to": "ROUTE_21|10,0"}
ck("a crossed edge is not named", ex._seen_edge_joins_line("CINNABAR_ISLAND|10,0", "VIRIDIAN_CITY") == "")
ex = fake(); del ex.visits["ROUTE_21|10,88"]
ck("an edge onto a map never walked is not named",
   ex._seen_edge_joins_line("CINNABAR_ISLAND|10,0", "VIRIDIAN_CITY") == "")
ck("standing on the goal, nothing", fake()._seen_edge_joins_line("VIRIDIAN_CITY|0,0", "VIRIDIAN_CITY") == "")
src = (ROOT / "planner/executor.py").read_text()
ck("it rides the page beside the route line",
   "+ self._ways_off_known_line(obs, want_map, here)\n                    + self._seen_edge_joins_line(here, want_map)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
