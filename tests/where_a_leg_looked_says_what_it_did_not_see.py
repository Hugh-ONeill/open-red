#!/usr/bin/env python3
"""The already-looked line says what of each map is still unseen, and does
not say the thing is on none of them when the looking was partial.

Run 58 (2026-10-17): "ROUTE_25 (7x) — you are on it now ... What it wants
was not on any of them", while 60 cells of Route 25 had ever been on screen,
its east, north and south sides never, and no sweep made. Bill's house is
at its far end; the model read Routes 24 and 25 as exhausted.

Synthetic.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(name, ok, d=""): checks.append((name, bool(ok), d))

def ex(region_seen, frontier, sides):
    x = object.__new__(E.Executor)
    x._leg_looked = {"CERULEAN_CITY": 59, "ROUTE_25": 8, "BIKE_SHOP": 3}
    x._leg_tries = 9
    x.region_seen = region_seen
    x.frontier = frontier
    x.explored = {"CERULEAN_CITY|20,0": {"north": {"to": "ROUTE_24|4,4"}}}
    x._sides_unseen = sides
    return x._looked_note({"map": {"id": "ROUTE_25"}})

t = ex({"ROUTE_25|10,2": 2}, {"CERULEAN_CITY|20,0": ["north", "south"]},
       {"ROUTE_25": ["east", "north", "south"]})
ck("a map with unseen ground says how much", "ROUTE_25 (8x: 2 spot(s) of its ground never on screen" in t, t)
ck("...and which sides were never on screen", "its east, north, south side(s) never on screen" in t, t)
ck("ways out never taken are counted", "1 way(s) out never taken" in t, t)
ck("a fully seen room says nothing extra", "BIKE_SHOP (3x)" in t, t)
ck("the verdict is not 'on none of them'", "not on any of them" not in t
   and "2 of these still have ground or ways you have not seen" in t, t)
t = ex({}, {}, {})
ck("everything seen: the old verdict stands", t.rstrip().endswith("What it wants was not on any of them."), t)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
