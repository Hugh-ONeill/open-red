#!/usr/bin/env python3
"""The bag line says which ways to free a slot work where you stand.

Run 67, 2026-10-28, Pokemon Mansion B1F: the line read "WAYS TO FREE A SLOT,
the reversible one first: STORING at a Pokemon Center's PC", and the run kept
leaving the basement to store things while the Secret Key lay refused for
want of a slot and a CARBOS sat in the bag (user: "i wish itd just use the
carbos though").

Pinned: no ranking of storing first; using and tossing are said to work where
you stand; the singles a use spends at no loss are named; the TM warning
stays.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = E.Executor.__new__(E.Executor)
ex.visits, ex.explored = {}, {}
ex._where = lambda o: "POKEMON_MANSION_B1F|20,1"
o = {"bag": {**{f"K{i}": 1 for i in range(17)}, "CARBOS": 1, "TM_REST": 1, "GREAT_BALL": 10},
     "key_items": []}
t = ex._bag_pressure_line(o)
ck("storing is not ranked first", "the reversible one first" not in t, t[:200])
ck("using and tossing work where you stand", "USING and TOSSING work where you stand" in t, t)
ck("a free-to-use single is named", "nothing lost from the party: CARBOS" in t, t)
ck("the TM warning stays", "a TM tossed is a move the party will never get" in t, t)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
