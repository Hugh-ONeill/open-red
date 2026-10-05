#!/usr/bin/env python3
"""A crossing no op named is kept with the cells walked into it, and `go`
replays those cells instead of pressing a warp nobody can stand on.

Run 36, 2026-10-05: Seafoam B3F's (20,17) is the warp at the bottom of a
current; a surfing party is carried into it from (20,11). steps.log named
the tile, the edge was filed as a door, and `go` replayed it as use_warp:
"(20,17) is a WALL right now", fifteen times, and the one way east through
the island read as shut (user: "you can go east through seafoam"). Proven
on a copy of the live save: the recorded cells, walked, land on B4F (2,0),
and the walked route from there reaches ROUTE_20|52,2.

Pinned: the approach is the last cells on the floor before the landing,
in order, without repeats, capped; nothing when the log has no such pair;
the ride walks to the first cell, surfs there when the walk falls short,
then steps cell by cell and stops when the floor changes; a cell the
current already carried the party to is skipped; a ride that never left
says so; the door hop uses it when the edge has one. Synthetic."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_tmp = tempfile.mkdtemp()
os.environ["RED_BRIDGE_DIR"] = _tmp
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


log = Path(E.RUN) / "steps.log"
rows = [("SEAFOAM_ISLANDS_B2F", 19, 6)] + [
    ("SEAFOAM_ISLANDS_B3F", x, y) for x, y in
    [(18, 7), (18, 8), (18, 9), (18, 10), (18, 10), (18, 11), (19, 11),
     (20, 11), (20, 12), (20, 13), (20, 14), (20, 15), (20, 16), (20, 17)]
] + [("SEAFOAM_ISLANDS_B4F", 20, 15), ("SEAFOAM_ISLANDS_B4F", 20, 14)]
log.write_text("".join(f"1.0 {m} {x} {y}\n" for m, x, y in rows))
a = E.Executor._approach_on("SEAFOAM_ISLANDS_B3F", "SEAFOAM_ISLANDS_B4F")
ck("the approach is the last cells before the landing, in order",
   a[-1] == [20, 17] and a[-4:] == [[20, 14], [20, 15], [20, 16], [20, 17]], a)
ck("...without repeats, and capped", len(a) == 12 and a.count([18, 10]) == 1, a)
ck("no such pair, no approach",
   E.Executor._approach_on("SEAFOAM_ISLANDS_B3F", "ROUTE_20") == [])


class FakeBridge:
    """Moves the player as the ops say; (20,17) is the current's mouth."""
    def __init__(self, at, onto_water_ok=False):
        self.x, self.y, self.map = at[0], at[1], "SEAFOAM_ISLANDS_B3F"
        self.sent = []
        self.water_ok = onto_water_ok

    def obs(self):
        return {"map": {"id": self.map, "region": "21,6"}, "mode": "overworld",
                "player": {"x": self.x, "y": self.y},
                "party": [{"moves": ["SURF"]}]}

    def send(self, op, **kw):
        self.sent.append((op, kw))
        if op == "walk_to":
            if kw.get("surf") or self.water_ok:
                self.x, self.y = kw["x"], kw["y"]
        elif op == "walk":
            d = {"right": (1, 0), "left": (-1, 0), "down": (0, 1), "up": (0, -1)}[kw["dir"]]
            self.x, self.y = self.x + d[0], self.y + d[1]
            if (self.x, self.y) == (20, 14):      # the current takes over
                self.map, self.x, self.y = "SEAFOAM_ISLANDS_B4F", 20, 15
        o = self.obs()
        o["result"] = {"ok": True, "detail": ""}
        return o


def ride(at, cells, **kw):
    ex = E.Executor.__new__(E.Executor)
    ex.b = FakeBridge(at, **kw)
    ex._send_safe = lambda op, **k: ex.b.send(op, **k)
    ex.settle = lambda: ex.b.obs()
    ex.handle_battle = lambda sg, o: o
    ex._knows_move = lambda o, m: True
    ex.log = lambda *a, **k: None
    o = ex._ride_approach({"id": "t"}, cells, ex.b.obs())
    return ex.b, o


cells = [[18, 10], [18, 11], [19, 11], [20, 11], [20, 12], [20, 13],
         [20, 14], [20, 15], [20, 16], [20, 17]]
b, o = ride((23, 9), cells)
ck("a walk that falls short of the first cell is ridden on the water",
   b.sent[0] == ("walk_to", {"x": 18, "y": 10})
   and b.sent[1] == ("walk_to", {"x": 18, "y": 10, "surf": True}), b.sent[:2])
ck("then it steps the cells in order",
   [s[1].get("dir") for s in b.sent[2:5]] == ["down", "right", "right"], b.sent)
ck("and stops when the floor changes, saying it was carried through",
   o["map"]["id"] == "SEAFOAM_ISLANDS_B4F" and o["result"]["ok"]
   and len(b.sent) == 2 + 6, (len(b.sent), o["result"]))
b, o = ride((23, 9), [[18, 10], [18, 11], [30, 30]], onto_water_ok=True)
ck("a ride that never left the floor says so",
   not o["result"]["ok"] and "stayed on SEAFOAM_ISLANDS_B3F" in o["result"]["detail"],
   o["result"])
ck("a cell it is not next to is walked to",
   b.sent[-1] == ("walk_to", {"x": 30, "y": 30, "surf": True}), b.sent[-1])

src = (ROOT / "planner/executor.py").read_text()
ck("the door hop rides an edge's approach instead of pressing the warp",
   'if _is_door_key(key) and len(_edge.get("approach") or []) >= 2:' in src
   and '_res = self._ride_approach(sg, _edge["approach"], pre)' in src)
ck("a crossing found in steps.log keeps its approach on the edge",
   'if k == key and len(_approach) >= 2:\n                e["approach"] = _approach' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
