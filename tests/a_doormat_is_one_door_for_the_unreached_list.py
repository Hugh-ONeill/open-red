#!/usr/bin/env python3
"""A doorway's other tiles are not ways out never taken.

Run 62, 2026-10-24 (and run 60): the Pokemon Mansion's front mat is four
tiles, (4,27)-(7,27), all to Cinnabar. The run came in by (5,27); from 1F's
south half the other three were filed in unreached_at as "ways out never
taken that no walk reached", so the B1F page's explore line read "FULLY
WORKED ... look for the way to 4,27, 6,27" and sent the run up off the
basement while the Secret Key's corner of it had never been on screen.

Pinned: a tile whose doorway has a taken tile is not unreached; a doorway
none of whose tiles is taken still is; a lone door untaken still is.
Synthetic: no game.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E                                   # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

HERE = "POKEMON_MANSION_1F|12,14"


def note(taken):
    ex = E.Executor.__new__(E.Executor)
    ex.frontier, ex.unreached_at, ex.shut_doors = {}, {}, {}
    ex.explored, ex.visits = {}, {}
    for _a in ("map_doors", "map_seen", "map_holes", "door_dests",
               "seen_far", "sightings", "_tried_objs", "_cut_bushes"):
        setattr(ex, _a, {})
    ex._where = lambda o: HERE
    ex._sealed = lambda h: set()
    ex._taken_here = lambda h: {k: {} for k in taken}
    ex._unopened_doors = lambda o: []
    ex._rebuild_area_aliases = lambda: None
    ex._save_memory = lambda: None
    mat = [{"x": x, "y": 27, "dest": "CINNABAR_ISLAND", "reachable": False}
           for x in (4, 5, 6, 7)]
    obs = {"map": {"id": "POKEMON_MANSION_1F", "region": "12,14",
                   "connections": {},
                   "warps": mat + [
                       {"x": 21, "y": 23, "dest": "POKEMON_MANSION_B1F", "reachable": True},
                       {"x": 26, "y": 27, "dest": "CINNABAR_ISLAND", "reachable": True},
                       {"x": 5, "y": 10, "dest": "POKEMON_MANSION_2F", "reachable": False}],
                   "holes": []}}
    ex.note_frontier(obs)
    return ex.unreached_at.get(HERE) or []


u = note(taken={"5,27", "21,23", "26,27"})
ck("the mat's other tiles are not unreached once one tile is taken",
   not ({"4,27", "6,27", "7,27"} & set(u)), u)
ck("...while a lone untaken door still is", "5,10" in u, u)
u2 = note(taken={"21,23", "26,27"})
ck("a mat none of whose tiles is taken still is",
   {"4,27", "5,27", "6,27", "7,27"} <= set(u2), u2)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
