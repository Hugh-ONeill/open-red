#!/usr/bin/env python3
""""Exit <place>" is done by the walked record when the place has been left
by two different mouths, and an exit by its only mouth is not refused.

"Exit Rock Tunnel" was refused with the tunnel left by both mouths (ROUTE_10|0,4
and ROUTE_10|14,52) and the run standing in Lavender Town; the missing rung then
invented "an NPC inside Rock Tunnel gives HM05" and inserted a leg for it
(run 41, 2026-10-08). EXIT is a through word on the DONE side only.
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

tunnel = rec({"ROCK_TUNNEL_1F|4,2": {"15,1": {"to": "ROUTE_10|0,4", "n": 2}},
              "ROCK_TUNNEL_1F|14,2": {"15,33": {"to": "ROUTE_10|14,52", "n": 1}}})
half = rec({"ROCK_TUNNEL_1F|4,2": {"15,1": {"to": "ROUTE_10|0,4", "n": 2}}})
mansion = rec({"POKEMON_MANSION_1F|5,27": {"5,27": {"to": "CINNABAR_ISLAND|6,3", "n": 3}}})
ck("both mouths walked: 'Exit Rock Tunnel' is done by the record",
   A._through_by_record("Exit Rock Tunnel", tunnel))
ck("...one mouth: not done by the record",
   A._through_by_record("Exit Rock Tunnel", half) is None)
ck("...and an exit is never refused on one mouth (the mansion has one)",
   A._not_through_yet("Exit the Pokemon Mansion", mansion) is None)
ck("'through' is still refused on one mouth",
   A._not_through_yet("Go through Rock Tunnel", half))

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)
