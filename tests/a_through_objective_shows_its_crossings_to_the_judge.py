#!/usr/bin/env python3
"""An objective about going through a place shows its done judges every way
the run came into that place and every way it left.

Run 27, 2026-09-18: "Navigate the Seafoam Islands" came after "Reach
Cinnabar Island", the run crossed Seafoam to reach Cinnabar, and the leg's
own judge said "has not yet exited the islands to reach the other side" —
the record held SEAFOAM_ISLANDS_1F|21,12 --(27,17)--> ROUTE_20|58,9 and the
walk west to Cinnabar. The chain sent the run back to cross again.

Pinned: through/across/traverse/navigate objectives naming a place get the
crossings (floors of one place are one place; in-map walks do not count);
other objectives get nothing; both judges carry it. Synthetic.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


led = Path(tempfile.mkdtemp()) / "explored.json"
led.write_text(json.dumps({"explored": {
    "ROUTE_20|44,2": {"48,5": {"to": "SEAFOAM_ISLANDS_1F|3,2"}},
    "SEAFOAM_ISLANDS_1F|3,2": {"23,15": {"to": "SEAFOAM_ISLANDS_B1F|20,10"},
                               "walk:SEAFOAM_ISLANDS_1F|21,12": {"to": "SEAFOAM_ISLANDS_1F|21,12"}},
    "SEAFOAM_ISLANDS_1F|21,12": {"27,17": {"to": "ROUTE_20|58,9"}},
    "ROUTE_20|58,9": {"west": {"to": "CINNABAR_ISLAND|10,0"}}}}))
t = A.crossings_text("Navigate the Seafoam Islands", led)
ck("a navigate objective gets the crossings into and out of the place",
   "YOUR CROSSINGS OF SEAFOAM_ISLANDS" in t
   and "INTO it: ROUTE_20|44,2 --(48,5)--> SEAFOAM_ISLANDS_1F|3,2" in t
   and "OUT of it: SEAFOAM_ISLANDS_1F|21,12 --(27,17)--> ROUTE_20|58,9" in t, t)
ck("...floors of one place are one place, and in-map walks do not count",
   "B1F" not in t and "walk:" not in t, t)
ck("...and it leaves the verdict to the judge", "Which of these is the far side is yours to judge." in t)
ck("'go through' and 'traverse' are the same kind of objective",
   A.crossings_text("Go through the Seafoam Islands", led) != "" and A.crossings_text("Traverse the Seafoam Islands", led) != "")
ck("an objective that is not about going through a place gets nothing",
   A.crossings_text("Defeat Blaine for the Volcano Badge", led) == ""
   and A.crossings_text("Reach Cinnabar Island", led) == "")
ck("no crossings on record, nothing", A.crossings_text("Navigate the Rock Tunnel", led) == "")
src = (ROOT / "planner/author.py").read_text()
ck("both done judges carry it",
   "+ crossings_text(goal, observed)" in src and "+ crossings_text(deed, observed))" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
