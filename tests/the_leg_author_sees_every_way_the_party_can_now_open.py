#!/usr/bin/env python3
"""The leg author sees every way the party can now open, from the same record
the escalation page's "every way the party can now open" uses.

Run of record 12 (2026-09-27): the page listed ROUTE_9|0,8's bush at (5,8)
from the first round of "Reach Rock Tunnel", and the leg was still authored
through Diglett's Cave four times; the author reads walked ground, the
outline and events, never the executor's remote lists. A first version of
this line was cut to six places alphabetically, and ROUTE_9 fell behind
ROUTE_2 and ROUTE_25, the same way the page's own list once dropped it.

Pinned: with a CUT-knower in the party every recorded bush is listed, grouped
by place and never cut to a count; without one nothing is said; a bush
whose far side was not recorded says so; build_prompt carries it; it names
no destination. Synthetic.
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


run = Path(tempfile.mkdtemp(prefix="openable_"))
bw = {f"ROUTE_2|{i},0": ["5,10"] for i in range(8)}
bw.update({"ROUTE_25|10,2": ["26,3"], "ROUTE_9|0,8": ["5,8"],
           "ROUTE_2|3,43": ["12,52", "12,60"], "VIRIDIAN_CITY|17,0": ["?"]})
(run / "explored.json").write_text(json.dumps({"bush_ways": bw}))


def party(moves):
    return {"party": [{"species": "IVYSAUR", "nickname": "SPROUT",
                       "moves": [{"id": m} for m in moves]}]}


(run / "obs.json").write_text(json.dumps(party(["CUT", "RAZOR_LEAF"])))
t = A.openable_ways_text(run)
ck("with a CUT-knower, the way that leads on is listed however many come first",
   "ROUTE_9|0,8: a bush at (5,8)" in t, t[:300])
ck("...every recorded place, never cut to a count",
   all(r in t for r in bw), t)
ck("...one place's bushes together",
   "ROUTE_2|3,43: bushes at (12,52), (12,60)" in t)
ck("...a bush whose far side was not recorded says so",
   "VIRIDIAN_CITY|17,0: a bush you could walk to (what lies past it was not recorded)" in t)
ck("...who knows the move is named", "(SPROUT knows CUT)" in t)
ck("...and the choice is left to the model",
   "is yours to judge" in t and "should" not in t and "Lavender" not in t)

(run / "obs.json").write_text(json.dumps(party(["TACKLE"])))
ck("without a CUT-knower nothing is said", A.openable_ways_text(run) == "")

src = (ROOT / "planner/author.py").read_text()
ck("build_prompt carries it, so drafts, review and rewrites all see it",
   "+ openable_ways_text()" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
