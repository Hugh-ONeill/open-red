#!/usr/bin/env python3
"""A pad ride between two parts of one map is not remembered as a walk.

Run 66, 2026-10-25, Silph Co. 8F: the (11,9) pad put the party in the
floor's |1,1 part, and _note_intra wrote "walk:SILPH_CO_8F|1,1" on |14,0
and "walk:SILPH_CO_8F|14,0" on |1,1 beside the pad's own edges. `go` to
the elevator then led with the walk leg out of a pocket no walk leaves and
spent the round on "no path".

Pinned: arriving on a warp tile records no walk edge; arriving on plain
ground still does.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

MAP = "SILPH_CO_8F"
WARPS = [{"x": 3, "y": 11, "look": "pad"}, {"x": 11, "y": 9, "look": "pad"},
         {"x": 18, "y": 0, "look": "lift"}]

def obs(region, x, y):
    return {"map": {"id": MAP, "region": region, "warps": WARPS},
            "player": {"x": x, "y": y, "surfing": False}}

def rig():
    ex = E.Executor.__new__(E.Executor)
    ex.explored = {}
    ex._faint_at = None
    ex.log = lambda *a, **k: None
    ex._save_memory = lambda: None
    ex._where = lambda o: f"{MAP}|{o['map']['region']}"
    return ex

ex = rig()
ex._intra_prev = f"{MAP}|14,0"
ex._note_intra(obs("1,1", 3, 11))
ck("landing on the pad writes no walk edge",
   not any(k.startswith("walk:") for k in ex.explored.get(f"{MAP}|14,0", {})),
   ex.explored)
ex._note_intra(obs("1,1", 3, 10))
ck("...and stepping off it inside the same part writes none either",
   not any(k.startswith("walk:") for n in ex.explored.values() for k in n), ex.explored)

ex = rig()
ex._intra_prev = f"{MAP}|14,0"
ex._note_intra(obs("1,1", 5, 4))
ck("a walk that ends on plain ground is still recorded",
   f"walk:{MAP}|1,1" in ex.explored.get(f"{MAP}|14,0", {}), ex.explored)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
