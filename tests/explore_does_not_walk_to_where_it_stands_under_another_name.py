#!/usr/bin/env python3
"""Explore does not pick another name for the place it stands in, accepts
that name on arrival, and counts a walk that does not arrive as dry.

Run 36, 2026-10-05: ROUTE_23|8,90 and ROUTE_23|10,104 had both been left
by the Route 22 gate door at (7,139): one stretch of road, two names.
Standing in one, explore picked the other twelve times; the route walker
called the walk arrived at once (_same_place), explore's own check said
"did not arrive", nothing was counted, and the next round picked it again
(user: "its pingponging bad but i think its just on the one explore op").

Pinned: two names sharing a door tile are one place, two that share only
a walk are not; the picker skips the place you stand in by either test;
arrival accepts either; a walk that still does not arrive is counted with
the dry walks. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ex = E.Executor.__new__(E.Executor)
ex.explored = {
    "ROUTE_23|10,104": {"7,139": {"to": "ROUTE_22_GATE|4,0"},
                        "walk:ROUTE_23|8,90": {"to": "ROUTE_23|8,90"}},
    "ROUTE_23|8,90": {"7,139": {"to": "ROUTE_22_GATE|4,0"},
                      "walk:ROUTE_23|4,31": {"to": "ROUTE_23|4,31"}},
    "ROUTE_23|4,31": {"walk:ROUTE_23|8,90": {"to": "ROUTE_23|8,90"},
                      "4,31": {"to": "VICTORY_ROAD_1F|5,9"}},
}
ck("two names left by the same door are one place",
   ex._same_place("ROUTE_23|10,104", "ROUTE_23|8,90"))
ck("two that share only a walk are not",
   not ex._same_place("ROUTE_23|8,90", "ROUTE_23|4,31"))

src = (ROOT / "planner/executor.py").read_text()
ck("the picker skips the place it stands in under another name",
   "if (self._same_area(here, region) or self._same_area(region, here)\n"
   "                    or self._same_place(here, region)):" in src)
ck("arrival accepts the other name",
   "if not (self._same_area(self._where(cur), region)\n"
   "                or self._same_place(self._where(cur), region)):" in src)
ck("a walk that does not arrive is a dry walk",
   'tr.append("explore: the walk did not arrive; author from here"' in src
   and "tr += self._count_dry_walk(region)\n            return False, tr, []" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
