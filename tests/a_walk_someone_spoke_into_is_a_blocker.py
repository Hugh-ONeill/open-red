#!/usr/bin/env python3
"""A walk someone spoke into and sent back is written as a blocker.

Run 50, Pewter (2026-10-11): before Brock the guide boy stops every east
cross — "You're a trainer right? BROCK's looking for new challengers!
Follow me!" — and walks the party back. The note says so ("someone spoke
and the walk ended short"), which no blocker branch read, so the ledger
had no row, the training step's page offered east -> ROUTE_3 as a way on,
and each new step tried it again (user: "its getting caught in the rt3
trap somehow, i thought it was supposed to register that as a blocker").
The strike's reason also cut the boy off: his quote starts past 160.

Pinned on run 50's own note: a seam blocker in his words; the strike
keeps his whole line. Synthetic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


NOTE = ("cross(dir=east): FAILED — couldn't reach east edge gap (39,17), stuck at (29,18) — "
        "11 cell(s) of walking still to do — during this walk someone spoke and the walk "
        "ended short: \"You're a trainer right? BROCK's looking for new challengers! Follow "
        "me!\" — and while it spoke you were walked back: from within 3 cell(s) of the gap "
        "to 34 away, at (9,13)")
LINE = "\"You're a trainer right? BROCK's looking for new challengers! Follow me!\""
HERE = "PEWTER_CITY|4,2"
OBS = {"map": {"id": "PEWTER_CITY", "region": "4,2", "warps": []},
       "player": {"x": 29, "y": 18}, "party": [], "badges": [], "flags": ["f"], "bag": {}}

ex = E.Executor.__new__(E.Executor)
ex.explored = {HERE: {}}
ex.blockers = {}
ex._outcomes = {}
ex._cur_target = "map:ROUTE_3"
ex.hints = {}
ex.touched = {}
ex.frontier = {HERE: ["east"]}
ex._no_cross = {}
ex.log = lambda *a, **k: None
ex._save_memory = lambda *a, **k: None
for _ in range(40):
    try:
        ex._record_outcome(OBS, "cross", {"dir": "east"}, NOTE)
        break
    except AttributeError as e:
        setattr(ex, str(e).split("'")[-2], {})
b = ex.blockers.get(f"{HERE}|east") or {}
ck("the east seam has a blocker row", bool(b), ex.blockers)
ck("...a seam", b.get("kind") == "seam")
ck("...in the boy's words", LINE in str(b.get("what")), b)
ck("...and nothing about what lifts it", b.get("lifts") is None and not b.get("lifts_note"))
why = E.Executor._strike_why(NOTE.split(": FAILED — ", 1)[1])
ck("the strike keeps his whole line though it starts past 160", why.endswith(LINE), why)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
