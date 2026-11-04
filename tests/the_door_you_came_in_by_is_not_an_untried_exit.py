#!/usr/bin/env python3
"""The door you came in by is not an exit never taken from the room.

Run 71, 2026-11-02, travel_to_celadon_city r18: the Badge House had been
walked into through its north door from CERULEAN_CITY|8,7, landing one tile
inside at (2,1). From the inside that door had never been walked, so explore
walked the run there for "1 exit(s) never taken" and took it back out to
where it had come from.

Pinned: a door one step from a landing whose destination is the map walked
from (or LAST_MAP) is not untried; a door nobody landed beside still is; a
pad's landing stays untried (a ride back can set you down elsewhere).
Synthetic.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

H = "CERULEAN_BADGE_HOUSE|2,0"


def rig(**over):
    ex = E.Executor.__new__(E.Executor)
    ex.explored = {
        "CERULEAN_CITY|8,7": {"9,9": {"n": 1, "to": H, "land": "2,1"}},
        "CERULEAN_CITY|20,0": {"9,11": {"n": 1, "to": H, "land": "2,6"}},
        H: {"2,7": {"n": 1, "to": "CERULEAN_CITY|20,0"}},
    }
    ex.frontier = {H: ["2,0", "2,7", "9,4"]}
    ex.door_dests = {"CERULEAN_BADGE_HOUSE": {"2,0": "LAST_MAP", "2,7": "LAST_MAP"}}
    ex.warp_looks = {}
    ex.pad_lands = {}
    ex.visits = {H: 2}
    ex._no_cross = {}
    ex._bad_seam = set()
    for k, v in over.items():
        setattr(ex, k, v)
    return ex


ex = rig()
left = ex._frontier_left(H)
ck("the north door it came in by is not untried", "2,0" not in left, left)
ck("a door no walk landed beside still is", "9,4" in left, left)

ex2 = rig(warp_looks={"CERULEAN_BADGE_HOUSE": {"2,0": "pad"}})
ck("a pad's landing stays untried", "2,0" in ex2._frontier_left(H), ex2._frontier_left(H))

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
