#!/usr/bin/env python3
"""Where it can go is said beside where it cannot (run 18, 2026-09-28).

In Cerulean with the south closed, the page said "NO PART OF THIS MAP YOU
HAVE STOOD ON TOUCHES ITS SOUTH SIDE" and the author's same-walk refusal said
"go somewhere else", five rounds running, while every draft walked to
Vermilion again; Route 24's east side, never crossed, sat forty lines further
down (user: "the page should encourage it to go where it *can* go instead of
pursuing where it *cant*"). Both now name the walked places with a way never
taken: the frontier less what was taken, less ways a standing blocker holds.

Synthetic, plus a source check.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import ledger as L  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


REC = {"visits": {"CERULEAN_CITY|20,0": 60, "ROUTE_24|4,4": 20},
       "frontier": {"CERULEAN_CITY|20,0": ["19,17", "east", "north", "north#skip1"],
                    "ROUTE_24|4,4": ["east", "south"]},
       "explored": {"CERULEAN_CITY|20,0": {"19,17": {"to": "CERULEAN_POKECENTER|0,3"},
                                           "north": {"to": "ROUTE_24|4,4"}},
                    "ROUTE_24|4,4": {"south": {"to": "CERULEAN_CITY|20,0"}}},
       "blockers": {"CERULEAN_CITY|20,0|east": {"where": "CERULEAN_CITY|20,0", "key": "east",
                                                "cleared": False}},
       "sightings": {}, "touched": {}}
d = Path(tempfile.mkdtemp(prefix="leads_"))
(d / "run").mkdir()
(d / "run/explored.json").write_text(json.dumps(REC))
here = os.getcwd()
os.chdir(d)
try:
    leads = A.untried_leads(Path("run"), skip_maps={"VERMILION_CITY"})
finally:
    os.chdir(here)
ck("the author's refusal names Route 24's untaken east side",
   any(l.startswith("ROUTE_24|4,4 (the way east never taken") for l in leads), leads)
ck("...not a door taken sixty times, nor a way a blocker holds",
   not any("19,17" in l or "the way east" in l and "CERULEAN" in l for l in leads), leads)


class X:
    pass


x = X()
x.explored, x.visits, x.frontier, x.blockers = REC["explored"], REC["visits"], REC["frontier"], REC["blockers"]
x._route = lambda a, b: [] if a == b else ["hop"]
ex_leads = L.untried_leads_ex(x, "CERULEAN_CITY|20,0")
ck("the page's list says the same, with its distance",
   ex_leads == ["ROUTE_24|4,4 (the way east never taken — 1 leg(s) away)"], ex_leads)
src = (ROOT / "planner/ledger.py").read_text()
ck("it is said right after the no-part-touches-that-side line",
   src.index("_leads = untried_leads_ex(ex, here, cap=3)")
   > src.index("NO PART OF THIS MAP YOU HAVE STOOD ON TOUCHES ITS "))
asrc = (ROOT / "planner/author.py").read_text()
ck("the same-walk refusal carries the author's list",
   "PLACES THIS RUN HAS WALKED THAT STILL HAVE SOMETHING " in asrc)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
