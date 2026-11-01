#!/usr/bin/env python3
"""A door with a recorded edge that landed somewhere is not "spent".

Run 69, 2026-11-01, Victory Road 3F: (23,7) read "reached for 5x and never
once got through" beside its own last result "ok (map->VICTORY_ROAD_2F,
warped)". The try tally and the box tally are never cleared when the same
door later warps, and the plan wrote a step to "enter the door at (23,7) on
2F that has never been taken".

Pinned: a door whose edge leads somewhere else, taken and not shut, is left
out of both tallies; a door with only failed tries, a shut door, and a
self-loop stay spent.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

R = "VICTORY_ROAD_3F|2,0"
ex = E.Executor.__new__(E.Executor)
ex._mark_now = ("m",)
ex._exit_tries = {R: {k: {"n": 5, "at": ("m",)} for k in ("23,7", "2,0", "9,9", "8,8")}}
ex._boxed_doors = {R: {"23,7": 3, "2,0": 2}}
ex.explored = {R: {
    "23,7": {"n": 5, "to": "VICTORY_ROAD_2F|1,5"},
    "9,9": {"n": 2, "to": "VICTORY_ROAD_2F|1,5", "shut": True},
    "8,8": {"n": 1, "to": R},
}}
sp = ex._spent_exits(R)
ck("a door that warped somewhere is not spent", "23,7" not in sp, sp)
ck("...a door with only failed tries still is", "2,0" in sp, sp)
ck("...a shut door still is", "9,9" in sp, sp)
ck("...a self-loop still is", "8,8" in sp, sp)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
sys.exit(1 if bad else 0)
