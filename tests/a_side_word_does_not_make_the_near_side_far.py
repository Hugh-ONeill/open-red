#!/usr/bin/env python3
"""A side word does not make the near side far.

Run 69, 2026-10-30, leg "Exit Mt. Moon". The run had come out of Mt Moon
only by its west mouth, onto ROUTE_4|4,4, the part it walked in on from
Route 3. The plan's words said east, and _came_out_onto's side rule picked
the eastmost part ever come out onto, of one: the near side. validate then
told the author three times that ROUTE_4|4,4 "IS" the far side and to end
on {"area": "ROUTE_4|4,4"}, and the plan it kept ends on a bare ROUTE_4
that the west mouth meets.

Pinned: one part come out onto, near by the record, is not named far for
any side word; between two parts the side still decides (Rock Tunnel).
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = {"ROUTE_3|57,0": {"north": {"n": 1, "to": "ROUTE_4|4,4"}},
      "MT_MOON_POKECENTER|0,3": {"3,7": {"n": 2, "to": "ROUTE_4|4,4"}},
      "MT_MOON_1F|3,2": {"14,35": {"n": 2, "to": "ROUTE_4|4,4"},
                         "25,15": {"n": 3, "to": "MT_MOON_B1F|24,14"}}}
for side in (None, "east", "west", "north", "south"):
    got = A._came_out_onto("MT_MOON_1F", "ROUTE_4", explored=ex, side=side)
    ck(f"the near side alone is not far (side={side})", got == [], got)

rt = {"ROUTE_10|0,4": {"walk:south": {"n": 1, "to": "ROUTE_10|9,60"}},
      "ROUTE_9|1,4": {"east": {"n": 1, "to": "ROUTE_10|0,4"}},
      "ROCK_TUNNEL_1F|15,3": {"15,3": {"n": 2, "to": "ROUTE_10|0,4"},
                              "15,33": {"n": 2, "to": "ROUTE_10|14,52"}},
      "LAVENDER_TOWN|0,0": {"north": {"n": 1, "to": "ROUTE_10|14,52"}}}
got = A._came_out_onto("ROCK_TUNNEL_1F", "ROUTE_10", explored=rt, side="south")
ck("between two parts the side still decides", {c[0] for c in got} == {"ROUTE_10|14,52"}, got)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
