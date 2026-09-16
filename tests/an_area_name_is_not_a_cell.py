#!/usr/bin/env python3
"""An area name beside DONE_WHEN is said to be a part of a map, not a cell.

Run 27 held {"map":"ROUTE_24","not_area":["ROUTE_24|13,11","ROUTE_24|17,4",
"ROUTE_24|4,4"]} standing at (19,4), called (19,4) "one of the forbidden
coordinates", and walked one cell west "to trigger the completion of the
subgoal" (2026-09-16). Pinned: the note appears when area or not_area is in
the condition (any_of included), says which part the party is in and
whether the condition names it, and is absent otherwise. It never says
where another part is.

Synthetic: no game, no model.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import executor as E          # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


ex = object.__new__(E.Executor)
DW = {"map": "ROUTE_24",
      "not_area": ["ROUTE_24|13,11", "ROUTE_24|17,4", "ROUTE_24|4,4"]}
here = {"map": {"id": "ROUTE_24", "region": "17,4"}}
t = ex._area_ids_note(DW, here)
ck("a not_area condition carries the note", "AREA NAMES ARE NOT CELLS" in t)
ck("...saying an area is a part of a map, not the single cell",
   "names a whole walkable PART of that map" in t
   and "not the single cell (x,y)" in t)
ck("...and that stepping to a neighboring cell does not leave it",
   "Stepping to a neighboring cell does not leave a part" in t)
ck("...and which part the party is in, and that the condition names it",
   "You are in ROUTE_24|17,4 now, which this condition names." in t)
elsewhere = {"map": {"id": "ROUTE_24", "region": "9,20"}}
ck("a part the condition does not name is said plainly",
   "You are in ROUTE_24|9,20 now." in ex._area_ids_note(DW, elsewhere))
ck("an area inside any_of carries it too",
   "AREA NAMES" in ex._area_ids_note(
       {"any_of": [{"area": "MT_MOON_B2F|3,2"}, {"map": "ROUTE_4"}]}, here))
ck("a plain map condition does not", ex._area_ids_note({"map": "ROUTE_24"},
                                                        here) == "")
ck("nothing says where another part is",
   "north" not in t.lower() and "bridge" not in t.lower())
src = (ROOT / "planner/executor.py").read_text()
ck("the note sits beside DONE_WHEN on the page",
   'f"{self._area_ids_note(done, obs)}"' in src
   and src.index('DONE_WHEN: {json.dumps(done)}')
   < src.index('f"{self._area_ids_note(done, obs)}"'))

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
