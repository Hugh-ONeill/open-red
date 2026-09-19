#!/usr/bin/env python3
"""A step whose condition rules parts of its map out says so on the page,
and says when the party is standing in one of them.

{"map": "ROUTE_4", "not_area": [...]} keeps the target key "map:ROUTE_4",
so the page told a party standing in a ruled-out part of Route 4 that its
goal was the map it was already on, and nothing about why the step had not
closed. Run 28 spent an escalation round reasoning that a warp "at (27,3)
on the MT_MOON_B1F map" must lead to "the desired part of Route 4"
(2026-09-19, user's paste of GOAL/DONE_WHEN/THINKS).

Pinned: the barred parts are listed with how often each was walked; the one
underfoot is named as such, with the fact that walking about in it cannot
close the step; a step that bars nothing says nothing; the exploration page
carries the line first. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


class Ex(E.Executor):
    def __init__(self, here, visits):
        self._here, self.visits = here, visits

    def _where(self, obs):
        return self._here


SG = {"id": "exit_mt_moon",
      "done_when": {"map": "ROUTE_4",
                    "not_area": ["ROUTE_4|36,2", "ROUTE_4|4,4"]}}
VISITS = {"ROUTE_4|36,2": 4, "ROUTE_4|4,4": 12}

w = Ex("ROUTE_4|36,2", VISITS)._barred_parts_words(SG, {})
ck("the condition's map and its barred parts are both said",
   w.startswith("THIS STEP RULES PARTS OUT: its condition asks for ROUTE_4, "
                "but NOT ROUTE_4|36,2"), w)
ck("the part underfoot is named as the one underfoot",
   "ROUTE_4|36,2 — the part you are standing in right now" in w, w)
ck("...with the fact that walking about in it cannot close the step",
   "you are in one of them now, so no amount of walking about in it can "
   "close this step." in w, w)
ck("the other barred part carries how often it was walked",
   "ROUTE_4|4,4 — walked 12x" in w, w)
ck("what closes the step is said",
   "It closes when you stand on a part of ROUTE_4 that is not one of those"
   in w, w)

w2 = Ex("ROUTE_4|20,0", VISITS)._barred_parts_words(SG, {})
ck("standing somewhere else, the barred parts are still listed",
   "ROUTE_4|36,2 — walked 4x" in w2)
ck("...and nothing says the party is in one", "you are in one of them now" not in w2)
ck("a part never stood in says so",
   "ROUTE_4|9,9 — never stood in" in
   Ex("ROUTE_4|20,0", {})._barred_parts_words(
       {"done_when": {"map": "ROUTE_4", "not_area": "ROUTE_4|9,9"}}, {}))
ck("a step that bars nothing says nothing",
   Ex("ROUTE_4|20,0", VISITS)._barred_parts_words(
       {"done_when": {"map": "ROUTE_4"}}, {}) == ""
   and Ex("X|0,0", {})._barred_parts_words(None, {}) == "")

src = (ROOT / "planner/executor.py").read_text()
ck("the exploration page carries it first",
   "move_head = self._barred_parts_words(sg, obs)" in src)
ck("it reads the same ruled-out parts the routing does",
   "bars = self._ruled_out_parts(sg)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
