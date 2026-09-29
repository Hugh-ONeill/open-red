#!/usr/bin/env python3
"""A building the run has never stood in is not a place it has done anything.

"Infiltrate Silph Co. and defeat the rival" was judged done before running,
on "the Silph Scope, which is obtained only after infiltrating Silph Co."
(the Scope comes from the Rocket Hideout), with no SILPH_CO floor ever
visited. The never-stood-in guard knew roads and towns only (run 19,
2026-09-29).

Synthetic.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def ledger(*maps):
    f = Path(tempfile.mkdtemp(prefix="bld_")) / "explored.json"
    f.write_text(json.dumps({"visits": {f"{m}|0,0": 1 for m in maps}}))
    return f


g = "Infiltrate Silph Co. and defeat the rival"
ck("Silph Co. never entered: named", A._never_stood_in(g, ledger("SAFFRON_CITY")) == "SILPH_CO",
   A._never_stood_in(g, ledger("SAFFRON_CITY")))
ck("one floor stood on: not refused", A._never_stood_in(g, ledger("SILPH_CO_1F")) is None)
ck("a building walked through: not refused",
   A._never_stood_in("Clear the Pokemon Tower", ledger("POKEMON_TOWER_3F")) is None)
ck("a zone by its head name",
   A._never_stood_in("Explore the Safari Zone", ledger("FUCHSIA_CITY")) == "SAFARI_ZONE")
ck("...and not once any part of it is walked",
   A._never_stood_in("Explore the Safari Zone", ledger("SAFARI_ZONE_EAST")) is None)
ck("a gym never entered",
   A._never_stood_in("Defeat Blaine at the Cinnabar gym", ledger("CINNABAR_ISLAND")) == "CINNABAR_GYM")
ck("an objective naming no building is untouched",
   A._never_stood_in("every party member is at least level 40", ledger("ROUTE_11")) is None)
ck("the fresh water leg is not refused",
   A._never_stood_in("Give FRESH WATER to the guard on Route 6", ledger("ROUTE_6", "ROUTE_6_GATE")) is None)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
