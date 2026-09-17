#!/usr/bin/env python3
"""A lift car and a roof belong to their building, so a place step is not
undone by riding the lift or climbing to the roof.

Run 27, 2026-09-17: buy_fresh_water failed while the party stood in
CELADON_MART_ELEVATOR. The backtrack asks whether the previous place step
(enter_dept_store, map CELADON_MART_1F) is "undone by going deeper into its
building" by comparing map families, and the car's name carries no floor
token, so it read as another building: the party was walked down to 1F to
enter the store again, twice (user: "got pulled down to 1f by the redo of
'enter the celadon department store' goal").

Pinned: map_family strips a lift-car or roof token like a floor token,
wherever it sits. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


for m, fam in (("CELADON_MART_ELEVATOR", "CELADON_MART"),
               ("CELADON_MART_ROOF", "CELADON_MART"),
               ("CELADON_MART_1F", "CELADON_MART"),
               ("SILPH_CO_ELEVATOR", "SILPH_CO"),
               ("CELADON_MANSION_ROOF_HOUSE", "CELADON_MANSION"),
               ("SS_ANNE_B1F_ROOMS", "SS_ANNE"),
               ("MT_MOON_B2F", "MT_MOON"),
               ("CELADON_CITY", "CELADON_CITY"),
               ("ROUTE_9", "ROUTE_9")):
    ck(f"{m} -> {fam}", E.map_family(m) == fam, E.map_family(m))
ck("so a step into the store still holds from the lift car",
   E.map_family("CELADON_MART_1F") == E.map_family("CELADON_MART_ELEVATOR"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
