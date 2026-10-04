#!/usr/bin/env python3
"""The world map's trail uses the finest record of each stretch of the run.

tools/worldmap.py draws the run's path for watchers from three records, each
finer than the last: the journal's region-to-region moves (all a run has from
before the others existed), breadcrumbs of the player's cell per observation
(tools/events.py), and every cell stepped on (the shim's run/steps.log).

Pinned: each record covers only the stretch before the next, finer one
starts; anything older than this run's journal (an earlier run's leftovers)
is left out; leg and attempt come from the journal's plan starts; every item
says which record it came from; `until` (the 1x copy's moment) drops anything
later from every record. Synthetic files only: no run, no game.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import worldmap  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


tmp = Path(tempfile.mkdtemp())
journal, crumbs, steps = tmp / "journal.jsonl", tmp / "trail.jsonl", tmp / "steps.log"
T0 = 1_800_000_000
journal.write_text("\n".join(json.dumps(r) for r in [
    {"t": T0, "kind": "plan_start", "plan": "leg_01_pick_a_starter.json"},
    {"t": T0 + 10, "kind": "explored", "frm": "PALLET_TOWN|5,5", "to": "ROUTE_1|10,30"},
    {"t": T0 + 20, "kind": "plan_start", "plan": "leg_02_reach_viridian.json"},
    {"t": T0 + 30, "kind": "explored", "frm": "ROUTE_1|10,10", "to": "VIRIDIAN_CITY|20,30"},
    {"t": T0 + 60, "kind": "explored", "frm": "VIRIDIAN_CITY|20,10", "to": "ROUTE_2|8,60"},
]) + "\n")
crumbs.write_text("\n".join(json.dumps(r) for r in [
    {"t": T0 - 500, "map": "CERULEAN_CITY", "x": 1, "y": 1},     # an earlier run
    {"t": T0 + 40, "map": "VIRIDIAN_CITY", "x": 21, "y": 29},
    {"t": T0 + 70, "map": "ROUTE_2", "x": 8, "y": 59},            # after steps begin
]) + "\n")
steps.write_text("\n".join([
    f"{T0 - 400} PEWTER_CITY 3 3",                                 # an earlier run
    f"{T0 + 50} VIRIDIAN_CITY 20 12",
    f"{T0 + 50} VIRIDIAN_CITY 20 11",
    f"{T0 + 51} VIRIDIAN_CITY 20 10",
]) + "\n")

out = worldmap.trail(journal, crumbs, steps)
kinds = [o[5] for o in out]
ck("region moves cover the stretch before the first breadcrumb",
   [o for o in out if o[5] == "hop"] == [
       (1, 1, "PALLET_TOWN", 5, 5, "hop"), (1, 1, "ROUTE_1", 10, 30, "hop"),
       (2, 2, "ROUTE_1", 10, 10, "hop"), (2, 2, "VIRIDIAN_CITY", 20, 30, "hop")], out)
ck("breadcrumbs cover the stretch before the first recorded step",
   [o[2:5] for o in out if o[5] == "crumb"] == [("VIRIDIAN_CITY", 21, 29)], out)
ck("recorded steps cover the rest, cell by cell",
   [o[2:5] for o in out if o[5] == "step"] == [("VIRIDIAN_CITY", 20, 12), ("VIRIDIAN_CITY", 20, 11),
                                              ("VIRIDIAN_CITY", 20, 10)], out)
ck("the records come in order: region moves, breadcrumbs, steps",
   kinds == sorted(kinds, key=["hop", "crumb", "step"].index), kinds)
ck("an earlier run's breadcrumbs and steps are left out",
   not any(o[2] in ("CERULEAN_CITY", "PEWTER_CITY") for o in out), out)
ck("leg and attempt come from the plan starts",
   out[-1][:2] == (2, 2), out[-1])
cut = worldmap.trail(journal, crumbs, steps, until=T0 + 50)
ck("until: nothing later than the copy's moment, from any record",
   [o[2:5] for o in cut if o[5] == "step"] == [("VIRIDIAN_CITY", 20, 12), ("VIRIDIAN_CITY", 20, 11)]
   and not any(o[2] == "ROUTE_2" for o in cut), cut)
ck("with no breadcrumbs or steps the region moves are the whole trail",
   len(worldmap.trail(journal, tmp / "none", tmp / "none")) == 6)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
