#!/usr/bin/env python3
"""A go between two parts of one map names where the walked record breaks.

Run 60, 2026-10-22: from the Pokemon Mansion 1F's north part to its south
part, the walked record runs 1F -> 2F|10,1 -> 3F|5,8 and, separately,
2F|6,1 -> 3F|1,1 -> the hole -> 1F|12,14: it breaks inside 2F, whose two
parts join only with the statues the other way. _route_gap took every part
of 1F as a goal, so the part stood in counted as arrived, the chain looked
whole, and go said only "no walked way" for eleven rounds while the model
flipped the 1F statue back and forth.

Pinned: a part asked for is that part; the question itself (here -> want)
is not reported as the break; the 2F break is; a map asked for by name
still takes all its parts; and the note says how the statues stood when the
far part's way on was walked.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


M = "POKEMON_MANSION_"
EXPLORED = {
    M + "1F|1,1": {"5,10": {"to": M + "2F|10,1", "switches": "UNPRESSED", "n": 13},
                   "5,27": {"to": "CINNABAR_ISLAND|10,0", "switches": "UNPRESSED", "n": 5}},
    M + "2F|10,1": {"7,10": {"to": M + "3F|5,8", "switches": "PRESSED", "n": 3},
                    "5,10": {"to": M + "1F|1,1", "switches": "PRESSED", "n": 11}},
    M + "3F|5,8": {"7,10": {"to": M + "2F|10,1", "switches": "PRESSED", "n": 3}},
    M + "2F|6,1": {"6,1": {"to": M + "3F|1,1", "switches": "PRESSED", "n": 10}},
    M + "3F|1,1": {"16,14": {"to": M + "1F|12,14", "switches": "PRESSED", "n": 4},
                   "6,1": {"to": M + "2F|6,1", "switches": "PRESSED", "n": 6}},
    M + "1F|12,14": {"21,23": {"to": M + "B1F|10,9", "switches": "UNPRESSED", "n": 6}},
}

ex = object.__new__(E.Executor)
ex.explored = EXPLORED
gap = ex._route_gap(M + "1F|1,1", M + "1F|12,14")
ck("the break inside 2F is named", gap == (M + "2F", M + "2F|10,1", M + "2F|6,1"), gap)
ck("...not the question itself (1F north to 1F south)",
   not gap or gap[0] != M + "1F", gap)
ck("a whole chain has no break",
   ex._route_gap(M + "3F|1,1", M + "1F|12,14") is None)
ck("a map asked for by name still takes all its parts",
   ex._route_gap(M + "2F|10,1", M + "1F") is None)
OBS = {"map": {"switches_on": False}}
ck("the far part's way on says how the statues stood",
   "walked with this building's switch statues PRESSED, and they are UNPRESSED now"
   in ex._switch_words(M + "2F|6,1", "6,1", OBS))
src = (ROOT / "planner" / "executor.py").read_text()
ck("the gap note carries those words",
   "_sw = self._switch_words(_gb, _gk, obs)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
