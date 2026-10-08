#!/usr/bin/env python3
"""An objective that says to NAVIGATE a place is a way through it, judged on
the walked record like "through": two mouths used is done, one is not.

"Navigate Mt. Moon and fight Team Rocket" was judged on where the party
stood; with every Rocket beaten and the far mouth (ROUTE_4|36,2) walked twice
it read "has not yet exited the mountain" from inside, and the leg traded
places with "Reach Cerulean City" (run 41, 2026-10-08).
"""
import json
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A                                        # noqa: E402

checks = []
def ck(n, ok): checks.append((n, bool(ok)))

def rec(edges):
    d = {"explored": edges, "visits": {r: 1 for r in edges}}
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(d, f); f.close()
    return f.name

both = rec({"MT_MOON_1F|3,2": {"14,35": {"to": "ROUTE_4|4,4", "n": 2}},
            "MT_MOON_B1F|20,2": {"27,3": {"to": "ROUTE_4|36,2", "n": 2}}})
one = rec({"MT_MOON_1F|3,2": {"14,35": {"to": "ROUTE_4|4,4", "n": 2}},
           "MT_MOON_B1F|20,2": {"23,3": {"to": "MT_MOON_B2F|20,5", "n": 1}}})
g = "Navigate Mt. Moon and fight Team Rocket"
ck("two mouths walked: done by the record", A._through_by_record(g, both))
ck("...one mouth: not through yet", A._not_through_yet(g, one))
ck("...and one mouth is not done", A._through_by_record(g, one) is None)
ck("'through' still reads the same",
   A._through_by_record("Go through Mt. Moon", both))
ck("an objective with neither word is left alone",
   A._through_by_record("Defeat the Rockets in Mt. Moon", both) is None)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)
