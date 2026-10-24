#!/usr/bin/env python3
"""The other-part line says how the run came into that part, not only where
its ways out led.

Run 62, 2026-10-24: Mansion 1F's south part, entered every time by falling
through 3F's hole (16,14), read from the north half only "stood in 8x, whose
ways out you have taken led to CINNABAR_ISLAND, B1F", and the run flipped
1F's statue round after round to walk there. The way in was in the run's own
record and nowhere on the page.

Pinned: the line names walked edges that arrived in that part, with the
part and key they came from; a part with no walked way in says nothing
extra.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
sys.path.insert(0, str(ROOT / "tests"))
import candidates as C  # noqa: E402
import ledger as L  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

M = "POKEMON_MANSION_1F"
NORTH, SOUTH = M + "|1,1", M + "|12,14"


def page(arrivals):
    ex = C.make()
    ex._where = lambda o: NORTH
    ex._explore_trips = {}
    ex.explored = {NORTH: {"5,27": {"to": "CINNABAR_ISLAND|10,0", "n": 3}},
                   SOUTH: {"21,23": {"to": "POKEMON_MANSION_B1F|10,9", "n": 2},
                           "26,27": {"to": "CINNABAR_ISLAND|10,0", "n": 1}}}
    if arrivals:
        ex.explored["POKEMON_MANSION_3F|1,1"] = {"16,14": {"to": SOUTH, "n": 4}}
    ex.visits = {NORTH: 9, SOUTH: 8}
    obs = {"map": {"id": M, "region": "1,1", "warps": []},
           "player": {"x": 5, "y": 25}, "party": [], "bag": {}}
    return L.render([], ex, obs, "")


t = page(True)
ck("the other part's way in is said", "which you have come into from "
   "POKEMON_MANSION_3F|1,1 by (16,14)" in t, t[:600])
ck("...beside its ways out", "whose ways out you have taken led to" in t)
t0 = page(False)
ck("a part with no walked way in says nothing extra", "come into from" not in t0)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
