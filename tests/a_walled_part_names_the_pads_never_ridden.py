#!/usr/bin/env python3
"""A thing seen and not reached on a floor cut by walls is followed by the
building's warp pads never ridden, said once.

Run 27, 2026-09-17, Silph Co: balls seen from 3F, 4F and 5F sat on parts of
those floors no walk from the part the run stood on reaches; the page said
"a way in you have not found yet" and the run kept going back to the same
parts to look (user: "its not just the locked doors but also areas walled
off and only accessable via warp").

Pinned: the far-rooms line ends with the building's unridden pads, per
floor, counted, and that standing there again shows the same; nothing says
where any pad goes; a building with no unridden pads adds nothing.
Synthetic.
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


ex = object.__new__(E.Executor)
ex.map_doors = {"SILPH_CO_3F": ["26,0", "27,15", "27,3", "20,0"],
                "SILPH_CO_5F": ["1,0", "9,15"],
                "SILPH_CO_1F": ["26,0", "10,0"],
                "CELADON_MART_2F": ["12,1"]}
ex.warp_looks = {"SILPH_CO_3F": {"26,0": "stairs", "27,15": "pad", "27,3": "pad", "20,0": "stairs"},
                 "SILPH_CO_5F": {"1,0": "stairs", "9,15": "pad"},
                 "SILPH_CO_1F": {"26,0": "stairs", "10,0": "door"},
                 "CELADON_MART_2F": {"12,1": "pad"}}
ex.explored = {"SILPH_CO_3F|20,0": {"20,0": {"to": "SILPH_CO_ELEVATOR|0,1"}},
               "SILPH_CO_5F|1,10": {"9,15": {"to": "SILPH_CO_3F|1,11"}}}

got = ex._pads_unridden_in_building(["SILPH_CO_4F|20,0", "SILPH_CO_3F|20,0"])
ck("the building's unridden pads are listed per floor and counted",
   got.startswith(" Standing again where you saw them shows the same. In this building 2 warp pad(s)")
   and "SILPH_CO_3F (27,15), (27,3)" in got, got)
ck("...a pad already ridden is not among them", "9,15" not in got)
ck("...stairs and doors are not pads", "26,0" not in got and "10,0" not in got)
ck("...another building's pads are not", "CELADON" not in got)
ck("...and where a pad goes is not said", "sets you down is not known until it is ridden" in got and "ELEVATOR" not in got)
ck("a building with no unridden pads adds nothing", ex._pads_unridden_in_building(["PEWTER_GYM|1,1"]) == "")
ex.explored["CELADON_MART_2F|1,1"] = {"12,1": {"to": "CELADON_MART_ROOF|0,0"}}
ck("...nor one whose only pad has been ridden", ex._pads_unridden_in_building(["CELADON_MART_5F|1,1"]) == "")
src = (ROOT / "planner/executor.py").read_text()
ck("it ends the far-rooms line", "+ self._pads_unridden_in_building(" in src
   and src.index("+ self._pads_unridden_in_building(") > src.index("not a thing that is done.\""))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:260]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
