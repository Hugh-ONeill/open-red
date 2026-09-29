#!/usr/bin/env python3
"""A person seen and never spoken to has not been helped (2026-09-28).

The leg's own judge (check_done) lacked the refusal the sweep over other
legs had: "Help Bill at Sea Cottage" stopped at the door with Bill on
screen, was judged NOT done, and a minute later "done: the player is
currently inside Bill's house". The ticket leg then set off for Vermilion.

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


d = Path(tempfile.mkdtemp(prefix="bill_"))
ex = d / "explored.json"
ex.write_text(json.dumps({"visits": {"BILLS_HOUSE|0,2": 1},
                          "sightings": {"BILLS_HOUSE|0,2": ["BILLSHOUSE_BILL_POKEMON", "CELL_SEPARATION_SYSTEM"]},
                          "touched": {}}))
called = []
A.brock_probe.chat = lambda *a, **k: called.append(1) or '{"done": true, "why": "inside the house"}'
ck("the leg's own judge refuses before asking the model",
   A.check_done("Help Bill at Sea Cottage", "standing in BILLS_HOUSE", "m", observed=str(ex)) is False
   and not called)
# ...but a trainer class is not a person (run 18, 2026-09-28): a beaten
# leader and an optional grunt were read as unspoken to.
ex2 = d / "explored2.json"
ex2.write_text(json.dumps({"visits": {"CERULEAN_GYM|0,1": 3, "MT_MOON_B2F|20,5": 1},
                           "sightings": {"CERULEAN_GYM|0,1": ["CERULEANGYM_MISTY"],
                                         "MT_MOON_B2F|20,5": ["MTMOONB2F_ROCKET1", "MTMOONB2F_SUPER_NERD"]},
                           "touched": {}}))
ck("a gym leader fought, never pressed, does not block 'Defeat Misty'",
   A.untouched_named("Defeat Misty for the Cascade Badge", ex2) == [])
ck("an optional grunt does not block 'fight Team Rocket'",
   A.untouched_named("Navigate Mt. Moon and fight Team Rocket", ex2) == [])
ck("...while Bill still does", A.untouched_named("Help Bill at Sea Cottage", str(ex)) != [])
# ...only the person's own words, not the map's (2026-09-29): "roof" is
# a map word of CELADONMANSION_ROOF_HOUSE_HIKER, and a Cerulean guard is not
# "the guard on Route 6".
ex3 = d / "explored3.json"
ex3.write_text(json.dumps({"visits": {"CELADON_MANSION_ROOF_HOUSE|0,1": 1, "CERULEAN_CITY|26,7": 2},
                           "sightings": {"CELADON_MANSION_ROOF_HOUSE|0,1": ["CELADONMANSION_ROOF_HOUSE_HIKER"],
                                         "CERULEAN_CITY|26,7": ["CERULEANCITY_GUARD1"]},
                           "touched": {}}))
ck("a map word in an object's name is not the person",
   A.untouched_named("Obtain FRESH WATER from the roof of the Celadon City Department Store", ex3) == [])
ck("a guard in another town is not the guard on Route 6",
   A.untouched_named("Give FRESH WATER to the guard on Route 6", ex3) == [])
src = (ROOT / "planner/author.py").read_text()
n = src.index("def check_done")
ck("check_done carries the same refusal the sweep has",
   "_un = untouched_named(goal, observed)" in src[n:n + 6000])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
