#!/usr/bin/env python3
"""A way out that did not fire is not reported as a same-map pad, and one
stretch of ground under two names is one place.

Run of record 6, 2026-09-26, Mt. Moon: the model sent use_warp to B1F's
ladder at (27,3) — the way out to Route 4 — and was told "ok (moved,
warped — same map, you are now at 27,5)". The ladder never fired: the op
held "down" on it for forty frames and walked two cells, which the shim's
teleport test counted as a pad. The run wrote the ladder off, filed it
under a 1F part as a pad back into the cave, and never tried it again.
The route there had already failed: B2F was named "20,5" and "3,2" for one
stretch holding the (21,17) ladder, the walk wanted one and landed in the
other, and called itself lost (user: "stop it, fix both, and restart
clean"). In the game on 2026-09-26 the ladder fires: from an isolated save
on B1F, use_warp(27,3) warped to LAST_MAP.

Pinned: the shim's same-map test needs a JUMP between two frames and a tile
whose own warp leads to this map; an exit filed with a door the room does
not have is refused before the same-map branch; two regions of one map that
hold an exit at the same tile are one place, for the router's edges, its
arrival test and the walk's landing checks; seams do not make them one.
Synthetic, the game side source-anchored."""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


shim = (ROOT / "harness/shim.lua").read_text()
ck("the shim counts a same-map warp only on a jump, from a pad that leads here",
   "local _same_ok = (_tile_dest == nil or _tile_dest == startMap)" in shim
   and "if _same_ok and _jump" in shim
   and "+ math.abs((_pp.cellY or 0) - _ly) > 1" in shim
   and "local _mdw = startMap and G.data and G.data.maps and G.data.maps[startMap]" in shim)

ex = E.Executor.__new__(E.Executor)
ex.explored = {
    "MT_MOON_B1F|4,4": {"21,17": {"to": "MT_MOON_B2F|3,2", "n": 6}},
    "MT_MOON_B2F|3,2": {"21,17": {"to": "MT_MOON_B1F|4,4", "n": 2}},
    "MT_MOON_B2F|20,5": {"21,17": {"to": "MT_MOON_B1F|4,4", "n": 4},
                         "5,7": {"to": "MT_MOON_B1F|20,2", "n": 4}},
    "MT_MOON_B1F|20,2": {"27,3": {"to": "ROUTE_4|24,5", "n": 0}},
    "ROUTE_4|4,4": {"north": {"to": "X|0,0", "n": 1}},
    "ROUTE_4|24,5": {"north": {"to": "Y|0,0", "n": 1}},
}
ck("two parts holding an exit at the same tile are one place",
   ex._same_place("MT_MOON_B2F|3,2", "MT_MOON_B2F|20,5"))
ck("...parts that share only a seam are not",
   not ex._same_place("ROUTE_4|4,4", "ROUTE_4|24,5"))
ck("...nor parts of two maps", not ex._same_place("MT_MOON_B2F|3,2", "MT_MOON_B1F|4,4"))
ex.explored["ROUTE_9|50,6"] = {"walk:ROUTE_9|6,2": {"to": "ROUTE_9|6,2", "n": 1}}
ex.explored["ROUTE_9|0,8"] = {"walk:ROUTE_9|6,2": {"to": "ROUTE_9|6,2", "n": 1}}
ck("...nor parts that both walk to a third", not ex._same_place("ROUTE_9|50,6", "ROUTE_9|0,8"))
ck("the router's edges carry the other name's exits",
   "5,7" in ex._edges_of("MT_MOON_B2F|3,2"))
ex._mark_now = None
r = ex._route("MT_MOON_B1F|4,4", "MT_MOON_B1F|20,2")
ck("...so the way to the exit's part is found through the other name",
   r == [("21,17", "MT_MOON_B2F|3,2"), ("5,7", "MT_MOON_B1F|20,2")], r)
ck("arriving at the other name of the destination is arriving",
   ex._route("MT_MOON_B1F|4,4", "MT_MOON_B2F|20,5") == [("21,17", "MT_MOON_B2F|3,2")])
src = (ROOT / "planner/executor.py").read_text()
ck("the walk's landing checks read the same rule",
   src.count("not self._same_place(self._where(o), nxt)") >= 3)

# a foreign door, same map: refused before the pad branch
ex2 = E.Executor.__new__(E.Executor)
ex2.logf = io.StringIO(); ex2.t0 = time.time()
ex2.explored = {}; ex2.door_dests = {}; ex2._faint_at = None; ex2.blockers = {}
ex2._where = lambda o: f"{o['map']['id']}|{o['_region']}"
ex2._count_visit = lambda r: None
ex2._save_memory = lambda: None
ex2._twin_keys = lambda o, s: []
ONE = {"map": {"id": "MT_MOON_1F", "warps": [{"x": 5, "y": 5, "dest": "MT_MOON_B1F"}]},
       "_region": "2,2", "player": {"x": 3, "y": 3}}
ex2.note_transition(ONE, {"x": 27, "y": 3}, dict(ONE, player={"x": 4, "y": 4}),
                    op_detail="warped — same map, you are now at 4,4")
ck("a same-map 'warp' at a door this room does not have is not filed",
   not ex2.explored and "edge_key_foreign" in ex2.logf.getvalue(), ex2.explored)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
