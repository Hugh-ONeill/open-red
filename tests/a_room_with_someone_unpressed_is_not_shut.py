#!/usr/bin/env python3
"""A room is not "shut" to new_map_from while someone in it has never been
pressed.

Run 67, 2026-10-26: "enter the Rocket base" as new_map_from GAME_CORNER was
refused on the room's two front doors, with the Rocket by the poster, nine
gamblers and a clerk never spoken to; the stairs down are behind the poster.
The leg failed and the outline pulled a Secret Key leg in front of it.

Pinned: with an unpressed person on record the step is not refused; with only
signs, slot machines, items and beaten trainers left (Mt Moon's case) it is.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

def rec(sightings, touched=(), beaten=()):
    p = Path(tempfile.mkdtemp(prefix="shut_")) / "explored.json"
    p.write_text(json.dumps({
        "map_doors": {"GAME_CORNER": ["15,17", "16,17"]},
        "door_dests": {"GAME_CORNER": {"15,17": "LAST_MAP", "16,17": "LAST_MAP"}},
        "explored": {"GAME_CORNER|8,5": {"15,17": {"to": "CELADON_CITY|2,1"}}},
        "frontier_here": {"GAME_CORNER|8,5": 0},
        "visits": {"GAME_CORNER|8,5": 3, "CELADON_CITY|2,1": 9},
        "sightings": {"GAME_CORNER|8,5": list(sightings)},
        "touched": {"GAME_CORNER|8,5": list(touched)},
        "beaten_seen": list(beaten)}))
    return str(p)

why = A._new_map_from_shut("GAME_CORNER", rec(
    ["GAMECORNER_ROCKET", "GAMECORNER_CLERK1", "SLOT_MACHINE_1"], touched=["GAMECORNER_CLERK1"]))
ck("an unpressed Rocket keeps the room open", why == "", why)
why = A._new_map_from_shut("GAME_CORNER", rec(
    ["GAMECORNER_ROCKET", "SIGN_GAME_CORNER_1", "SLOT_MACHINE_1"], beaten=["GAMECORNER_ROCKET"]))
ck("only signs, slots and a beaten trainer left: still judged shut", bool(why), why)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
