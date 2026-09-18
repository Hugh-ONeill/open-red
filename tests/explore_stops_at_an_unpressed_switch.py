#!/usr/bin/env python3
"""Explore does not walk off a floor whose one unfinished thing is a switch
statue never pressed; it says what is left and stops.

Run 27, 2026-09-18, Pokemon Mansion B1F: explore never presses a switch
(it moves the whole building's walls; the model chooses), so with SWITCH
(20,3) the only thing untouched the floor read as done, and explore walked
the party to a pocket of 1F, where the run judged itself trapped and used
an ESCAPE_ROPE (user: "it was in the basement, it just didnt have the
curiosity to explore the whole way").

Pinned: an untouched, reachable switch statue stops explore before it
walks away, with the press op spelled out, the same as a boulder does.
Source-anchored: the step runs the game.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


src = (ROOT / "planner/executor.py").read_text()
n = src.index("    def _explore_step")
blk = src[n:n + 60000]
ck("an untouched reachable switch statue stops explore",
   '_levers_here = [c for c in cands\n                        if "SWITCH" in str(c.key).upper()\n                        and c.status == "untouched" and c.reachable]' in blk)
ck("...saying what is left and spelling the press",
   "what is left on this floor is " in blk and '"answer":"yes"}}. ' in blk
   and "Walking off this floor leaves it exactly as it is." in blk)
ck("...after the boulder rule and before the walk to another area",
   blk.index("_rocks_here = [c for c in cands") < blk.index("_levers_here = [c for c in cands")
   < blk.index("# nowhere here: the nearest area over walked ground"))
ck("explore still never presses a switch itself",
   'and "SWITCH" not in str(c.key).upper()' in blk)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
