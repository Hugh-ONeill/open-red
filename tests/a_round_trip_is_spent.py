#!/usr/bin/env python3
"""A stretch of rounds that ends where it began, having found nothing new and
changed nothing, spends every set of ops in it.

The repeat gate spends ops only when they FAILED; a warp up and a warp back
down each report "ok", so Victory Road 1F's upper part was left by (1,1) and
re-entered by (0,8) round after round (run 37 ~1.5h, run 41, 2026-10-10).
"""
import sys
import types
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E                                      # noqa: E402

checks = []
def ck(n, ok): checks.append((n, bool(ok)))

def ex():
    o = types.SimpleNamespace(_spent_macros={}, _trip_trail=[], logged=[])
    o.log = lambda k, **kw: o.logged.append((k, kw))
    o._note_round_trip = types.MethodType(E.Executor._note_round_trip, o)
    return o

def snap(m, hp=8, lv=290, fl=200, bag=(19, 40)):
    return (m, 1, 1, "overworld", (6, lv), fl, bag, hp, "x")

UP = ("VICTORY_ROAD_1F|14,0", '[{"op":"use_warp","x":1,"y":1}]', "m", 0)
DOWN = ("VICTORY_ROAD_2F|15,0", '[{"op":"use_warp","x":0,"y":8}]', "m", 0)

o = ex()
t1 = []; r1 = o._note_round_trip({"id": "s"}, 1, UP, snap("VICTORY_ROAD_1F"), snap("VICTORY_ROAD_2F"), t1)
t2 = []; r2 = o._note_round_trip({"id": "s"}, 2, DOWN, snap("VICTORY_ROAD_2F"), snap("VICTORY_ROAD_1F"), t2)
ck("one way is not a trip", r1 == "")
ck("there and back is a round trip", r2 == "VICTORY_ROAD_1F -> VICTORY_ROAD_2F -> VICTORY_ROAD_1F")
ck("...and both halves are spent", UP in o._spent_macros and DOWN in o._spent_macros)
ck("...with the path as the answer", "round trip" in o._spent_macros[UP]["why"])
ck("...and the round says so", any("round trip" in t for t in t2))

o = ex()
o._note_round_trip({"id": "s"}, 1, UP, snap("ROUTE_9"), snap("CERULEAN_POKECENTER", hp=8), [])
r = o._note_round_trip({"id": "s"}, 2, DOWN, snap("CERULEAN_POKECENTER", hp=300), snap("ROUTE_9", hp=300), [])
ck("a heal trip is not a loop (HP changed)", r == "" and not o._spent_macros)

o = ex()
o._note_round_trip({"id": "s"}, 1, UP, snap("A"), snap("B"), [])
r = o._note_round_trip({"id": "s"}, 2, DOWN, snap("B"), snap("A"), ["(this round found something new — 1 way(s) taken for the first time — ...)"])
ck("a round that found something new breaks the stretch", r == "" and not o._spent_macros)

o = ex()
o._note_round_trip({"id": "s"}, 1, UP, snap("A"), snap("B"), [])
r = o._note_round_trip({"id": "s"}, 2, DOWN, snap("B"), snap("A", lv=291), [])
ck("a level gained on the way is not a loop", r == "")

o = ex()
r = o._note_round_trip({"id": "s"}, 1, UP, snap("A"), snap("A"), [])
ck("a round that never left the map is not a trip (the existing gate owns it)", r == "")

PADS = ("SILPH_CO_4F|10,2", '[{"op":"use_warp","x":11,"y":7},{"op":"walk_to","x":9,"y":11},{"op":"use_warp","x":9,"y":11}]', "m", 0)
TR = ["use_warp(x=11,y=7): ok (map->SILPH_CO_10F, moved, warped)", "walk_to(9,11): ok",
      "use_warp(x=9,y=11): ok (map->SILPH_CO_4F, moved, warped)"]
o = ex()
r = o._note_round_trip({"id": "s"}, 1, PADS, snap("SILPH_CO_4F"), snap("SILPH_CO_4F"), list(TR))
ck("a round that warps out and back is a round trip (run 66, Silph 4F/10F pads)",
   r == "SILPH_CO_4F -> SILPH_CO_10F -> SILPH_CO_4F" and PADS in o._spent_macros)

src = (ROOT / "planner/executor.py").read_text()
ck("the round loop calls it before the feedback is logged",
   src.index("self._note_round_trip(sg, rnd,") < src.index('self.log("escalate_feedback", subgoal=sg["id"], round=rnd,'))

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)
