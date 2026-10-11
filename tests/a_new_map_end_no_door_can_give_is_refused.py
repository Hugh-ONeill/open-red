#!/usr/bin/env python3
"""A new_map_from end that no door of its map can give is refused.

Run 48, Mt Moon (2026-10-11): leg 8's plan ended "exit_b2f" on
{"new_map_from": "MT_MOON_B2F"} — a map never stood on, entered from B2F.
All four of B2F's ladders lead to MT_MOON_B1F, already stood on. The run
reached east ROUTE_4, the leg's real end, and went back down to hunt a B2F
exit that is not there (user: "new goal text is unachievable").

Pinned on run 48's record: every recorded door of B2F leading to stood-on
maps refuses it; a map whose doors are not all recorded, one with a road
edge, and one with a door to a map never stood on pass; validate says it.
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


REC = {
    "visits": {"MT_MOON_B1F|4,4": 3, "MT_MOON_B2F|20,5": 2, "ROUTE_4|4,4": 5,
               "PEWTER_CITY|4,2": 9, "GAME_CORNER|1,1": 1},
    "map_doors": {"MT_MOON_B2F": ["15,27", "21,17", "25,9", "5,7"],
                  "GAME_CORNER": ["15,17", "17,4"],
                  "PEWTER_CITY": ["16,17"]},
    "door_dests": {"MT_MOON_B2F": {"15,27": "MT_MOON_B1F", "21,17": "MT_MOON_B1F",
                                   "25,9": "MT_MOON_B1F", "5,7": "MT_MOON_B1F"},
                   "GAME_CORNER": {"15,17": "CELADON_CITY", "17,4": "ROCKET_HIDEOUT_B1F"},
                   "PEWTER_CITY": {"16,17": "PEWTER_GYM"}},
    "explored": {"PEWTER_CITY|4,2": {"east": {"to": "ROUTE_3|0,0"}}},
}
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
    json.dump(REC, f)
    P = f.name

w = A._new_map_from_shut("MT_MOON_B2F", P)
ck("B2F, every ladder to B1F already stood on: refused", "MT_MOON_B1F" in w, w)
ck("a door to a map never stood on passes", A._new_map_from_shut("GAME_CORNER", P) == "")
ck("a map with a road edge is not judged", A._new_map_from_shut("PEWTER_CITY", P) == "")
part = json.loads(json.dumps(REC))
part["door_dests"]["MT_MOON_B2F"].pop("15,27")
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
    json.dump(part, f)
ck("a door with no recorded destination passes", A._new_map_from_shut("MT_MOON_B2F", f.name) == "")
src = (ROOT / "planner/author.py").read_text()
ck("validate refuses it with the reason",
   'elif k == "new_map_from" and _new_map_from_shut(v):' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
