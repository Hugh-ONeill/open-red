#!/usr/bin/env python3
"""A room the run has seen a nurse in is a Center on both pages: the
executor's near-Centers list and the author's start line.

Run 27, 2026-09-18: only maps named *_POKECENTER counted, so the Indigo
Plateau lobby — its nurse in the run's own sightings, two hops from Route
23 — was never named, and every training plan for "every party member at
level 50" walked back through Victory Road to heal at Viridian (user: "it
kept trying to go to viridian").

Pinned: the executor lists a nurse room with its walked legs; the author's
start line lists nurse rooms, nearest by walked hops first, with the count.
Synthetic."""
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
ex.visits = {"ROUTE_23|9,0": 3, "INDIGO_PLATEAU_LOBBY|8,0": 12, "VIRIDIAN_POKECENTER|0,3": 7}
ex.explored = {}
ex.sightings = {"INDIGO_PLATEAU_LOBBY|8,0": ["INDIGOPLATEAULOBBY_NURSE", "PC"],
                "VIRIDIAN_POKECENTER|0,3": ["VIRIDIANPOKECENTER_NURSE"]}
ex._where = lambda o: "ROUTE_23|9,0"
ex._route = lambda a, b: (["n", "d"] if b.startswith("INDIGO") else None)
line = ex._respawn_line({"respawn": {"map": "VIRIDIAN_POKECENTER"}})
ck("the executor's near-Centers list names a room with a nurse", "INDIGO_PLATEAU_LOBBY (2 leg(s))" in line, line)

src = (ROOT / "planner/state_text.py").read_text()
i, j = src.index("def centers_text"), src.index("def daycare_text")
ns = {"__file__": str(ROOT / "planner/state_text.py")}
exec(src[i:j], ns)
import json, tempfile, os  # noqa: E402
tmp = Path(tempfile.mkdtemp())
(tmp / "run").mkdir()
(tmp / "planner").mkdir()
(tmp / "run" / "explored.json").write_text(json.dumps({
    "sightings": ex.sightings,
    "explored": {"ROUTE_23|9,0": {"north": {"to": "INDIGO_PLATEAU|0,0"}},
                 "INDIGO_PLATEAU|0,0": {"11,5": {"to": "INDIGO_PLATEAU_LOBBY|8,0"}}}}))
ns["__file__"] = str(tmp / "planner" / "state_text.py")
got = ns["centers_text"]("ROUTE_23")
ck("the author's start line lists nurse rooms, nearest by walked hops first",
   got.startswith(" — ANY Pokemon Center heals") and "INDIGO_PLATEAU_LOBBY (2 walked hop(s) from here), VIRIDIAN_POKECENTER" in got, got)
ck("...and it rides every standing-in line", src.count("+ centers_text(m)") >= 2)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
