#!/usr/bin/env python3
"""A travel step whose target no walked ground reaches gets the floor's seen
ways off read together: where each is known to lead, that none leads to
the target, and which sides have never been on screen.

Run 27, 2026-09-17, Route 12 after the flute: the step wanted ROUTE_13, the
run believed it lay west, and every westward crossing landed on ROUTE_11;
the rows said the south side had never been on screen and row 1 was the
walk to the unseen ground, but nothing read them against the belief
(user: "now its pingponging instead of exploring south").

Pinned: said only when every seen way off has a known far side from the
run's own record; an untaken way, a target already stood on, or a way known
to lead to the target silences it; it names the unseen sides and the
frontier count; it rides the page beside the route line. Synthetic.
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


def fake():
    ex = object.__new__(E.Executor)
    ex.visits = {"ROUTE_12|0,61": 15, "ROUTE_12|8,0": 3, "ROUTE_11|58,8": 14, "LAVENDER_TOWN|6,0": 2}
    ex.explored = {"ROUTE_12|0,61": {"west": {"to": "ROUTE_11|58,8"},
                                     "walk:ROUTE_12|8,0": {"to": "ROUTE_12|8,0", "intra": True}},
                   "ROUTE_12|8,0": {"north": {"to": "LAVENDER_TOWN|6,0"},
                                    "10,15": {"to": "ROUTE_12_GATE_1F|3,0"}}}
    ex.door_dests = {"ROUTE_12": {"10,15": "ROUTE_12_GATE_1F"}}
    return ex


def obs(**kw):
    m = {"id": "ROUTE_12", "connections": {"west": "ROUTE_11", "north": "LAVENDER_TOWN"},
         "warps": [{"x": 10, "y": 15}], "sides_unseen": ["south"], "seen": {"frontier_n": 4}}
    m.update(kw)
    return {"map": m}


got = fake()._ways_off_known_line(obs(), "ROUTE_13", "ROUTE_12|0,61")
ck("every seen way off is read against the target",
   got.startswith("\nEVERY WAY OFF THIS FLOOR THAT YOU HAVE SEEN LEADS SOMEWHERE YOU HAVE ALREADY BEEN: north -> LAVENDER_TOWN; west -> ROUTE_11; door (10,15) -> ROUTE_12_GATE_1F. None of them is known to lead to ROUTE_13."), got)
ck("...the unseen side is named", "south side(s) have never been on screen; a way on that side would be there" in got, got)
ck("...and the frontier count", "ends at 4 spot(s)" in got, got)
ck("a way never taken silences it (the never-taken rows own that)",
   fake()._ways_off_known_line(obs(warps=[{"x": 10, "y": 15}, {"x": 3, "y": 70}]), "ROUTE_13", "ROUTE_12|0,61") == "")
ex = fake(); ex.visits["ROUTE_13|0,0"] = 1
ck("a target the run has stood on silences it", ex._ways_off_known_line(obs(), "ROUTE_13", "ROUTE_12|0,61") == "")
ex = fake(); ex.explored["ROUTE_12|0,61"]["west"] = {"to": "ROUTE_13|0,0"}
ck("a way known to lead to the target silences it", ex._ways_off_known_line(obs(), "ROUTE_13", "ROUTE_12|0,61") == "")
ck("no target map, nothing", fake()._ways_off_known_line(obs(), "", "ROUTE_12|0,61") == "")
ck("standing on the target, nothing", fake()._ways_off_known_line(obs(), "ROUTE_12", "ROUTE_12|0,61") == "")
src = (ROOT / "planner/executor.py").read_text()
ck("it rides the page beside the route line",
   "+ floor_note + floor_away + route_line\n                    + self._ways_off_known_line(obs, want_map, here)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
