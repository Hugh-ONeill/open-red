#!/usr/bin/env python3
"""A map walked in parts says which part is where, on first mention.

Run of record 7, 2026-09-26, Viridian Forest: "avoiding the North Gate
(which I know leads back to Route 2)". The gate leads to Route 2's north
half, a screen from Pewter; the page named the halves "ROUTE_2|8,0" and
"ROUTE_2|3,43" and nothing said which was which (user: "put it on the next
stop list", then "do the naming fix").

Pinned: a map with two walked parts says north/south (or west/east) along
its wider spread, three say west/middle/east, more are counted from the
ends, every part gets its own word; only the first mention gains it, the
key itself is never changed, a map walked in one part is left alone; the
executor's and the author's prompts go through it. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import part_names as P  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


R = ["ROUTE_2|8,0", "ROUTE_2|3,43", "VIRIDIAN_CITY|17,0",
     "ROUTE_9|50,6", "ROUTE_9|6,2", "ROUTE_9|0,8",
     "MT_MOON_B2F|23,21", "MT_MOON_B2F|27,5", "MT_MOON_B2F|20,5", "MT_MOON_B2F|3,2"]
lab = P.labels(R)
ck("two parts are north and south", lab.get("ROUTE_2|8,0") == "north"
   and lab.get("ROUTE_2|3,43") == "south", lab)
ck("three are west, middle and east", (lab.get("ROUTE_9|0,8"), lab.get("ROUTE_9|6,2"),
   lab.get("ROUTE_9|50,6")) == ("west", "middle", "east"), lab)
ck("more are counted from the ends, each its own word",
   len({v for k, v in lab.items() if k.startswith("MT_MOON_B2F")}) == 4, lab)
ck("a map walked in one part is left alone", "VIRIDIAN_CITY|17,0" not in lab)
t = P.name_parts("door (5,0) -> ROUTE_2|8,0; from ROUTE_2|3,43; again ROUTE_2|8,0; "
                 "VIRIDIAN_CITY|17,0", R)
ck("the first mention says where the part lies",
   "ROUTE_2|8,0 (the north part of ROUTE_2)" in t
   and "ROUTE_2|3,43 (the south part of ROUTE_2)" in t, t)
ck("...later mentions and the keys themselves are unchanged",
   t.endswith("again ROUTE_2|8,0; VIRIDIAN_CITY|17,0"), t)
ex = (ROOT / "planner/executor.py").read_text()
au = (ROOT / "planner/author.py").read_text()
ck("the executor's escalation prompt goes through it",
   "user = part_names.name_parts(" in ex)
ck("...and the plan author's",
   "part_names.name_parts(\n                 user, part_names.walked_regions())" in au)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
