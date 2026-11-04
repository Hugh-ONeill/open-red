#!/usr/bin/env python3
"""A walk refused "no path" from a part with nothing left to see refutes that
hop, and go's chain-break note stops offering it.

Runs 71 and 72 (2026-11-02/04): east of Route 4's one-way ledges, every go
said "The chain breaks inside ROUTE_4 ... go to ROUTE_4|63,10 then walk_to
36,2 is how they join". The walk back over the ledge was already refuted in
the record (_bad_seam), and every use_warp to the Mt Moon doors filed under
the western parts came back "no path" from ground with nothing unseen. The
model walked Cerulean and east Route 4 for hours.

Pinned on run 72's own Route 4 ledger: _route_gap does not offer a refuted
hop and names it instead; a use_warp "no path" from seen-out ground to a
door filed under another part refutes the hop to that part; with no gap
left, go's note says the walk was tried and did not land; "no path" from a
part that still has unseen ground refutes nothing. Synthetic.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

EXPLORED = {
    "ROUTE_4|4,4": {"south": {"n": 3, "to": "ROUTE_3|57,0", "inferred": True},
                    "11,5": {"n": 3, "to": "MT_MOON_POKECENTER|0,3"},
                    "18,5": {"n": 4, "to": "MT_MOON_1F|3,2"}},
    "ROUTE_4|36,2": {"24,5": {"n": 1, "to": "MT_MOON_B1F|20,2"},
                     "walk:ROUTE_4|63,10": {"n": 1, "to": "ROUTE_4|63,10"}},
    "ROUTE_4|63,10": {"east": {"n": 31, "to": "CERULEAN_CITY|20,0"}},
    "CERULEAN_CITY|20,0": {"west": {"n": 30, "to": "ROUTE_4|63,10"}},
    "MT_MOON_1F|3,2": {"14,35": {"n": 2, "to": "ROUTE_4|4,4"}},
}
EAST, WEST, MID = "ROUTE_4|63,10", "ROUTE_4|4,4", "ROUTE_4|36,2"
WANT = "MT_MOON_1F|3,2"


def rig():
    ex = E.Executor.__new__(E.Executor)
    ex.explored = {k: {kk: dict(vv) for kk, vv in v.items()} for k, v in EXPLORED.items()}
    ex.visits = {k: 1 for k in EXPLORED}
    ex._bad_seam = {(EAST, f"walk:{MID}", MID)}
    ex.pad_lands = {}
    ex.log = lambda *a, **k: None
    ex._save_memory = lambda: None
    ex._where = lambda o: f"{o['map']['id']}|{o['map']['region']}"
    return ex


def obs(frontier):
    return {"mode": "overworld", "player": {"x": 89, "y": 11},
            "map": {"id": "ROUTE_4", "region": "63,10", "frontier": frontier}}


NOTE = ("use_warp(x=18,y=5): FAILED — couldn't reach the warp tile (no path — "
        "the ground you have SEEN and can walk from here is 115 cell(s) and the "
        "closest it comes to 18,5 is 63,10)")

ex = rig()
g = ex._route_gap(EAST, WANT)
ck("the refuted hop to the middle part is not offered",
   not g or g[2] != MID, g)

ex._refute_walk(obs([]), "use_warp", {"x": 18, "y": 5}, NOTE)
ck("a door's no-path from seen-out ground refutes the hop to its part",
   (EAST, f"walk:{WEST}", WEST) in ex._bad_seam, ex._bad_seam)
g = ex._route_gap(EAST, WANT)
ck("with every hop refuted no gap is offered", g is None, g)
ck("...and the refuted one is named for the note",
   getattr(ex, "_route_gap_refuted", None)
   and ex._route_gap_refuted[1] == EAST, getattr(ex, "_route_gap_refuted", None))

src = (ROOT / "planner/executor.py").read_text()
ck("go's note says the walk was tried and did not land",
   "has been tried in this world state and did not" in src
   and 'getattr(self, "_route_gap_refuted", None)' in src)

ex2 = rig()
ex2._refute_walk(obs([{"x": 70, "y": 12, "d": 5}]), "use_warp", {"x": 18, "y": 5}, NOTE)
ck("no path from a part with unseen ground left refutes nothing",
   (EAST, f"walk:{WEST}", WEST) not in ex2._bad_seam, ex2._bad_seam)
ex3 = rig()
ex3._refute_walk(obs([]), "use_warp", {"x": 18, "y": 5}, "use_warp(x=18,y=5): ok (moved)")
ck("a walk that went is not a refusal",
   (EAST, f"walk:{WEST}", WEST) not in ex3._bad_seam)
ex4 = rig()
ex4._bad_seam = set()
g = ex4._route_gap(EAST, WANT)
# (the inferred walk back over the ledge still stands, so the gap offered is
# the next one west)
ck("with nothing refuted a gap is still offered", g and g[0] == "ROUTE_4", g)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
