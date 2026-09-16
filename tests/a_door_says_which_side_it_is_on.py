#!/usr/bin/env python3
"""A door on the page says which side it is on, as the screen shows it.

Run 27 came out on Route 6's north part, went through the gate building
at (10,7), heard "Gee, I'm thirsty, though! Oh wait there, the road's
closed." at the gate room's top door, decided the guards were "blocking the
way south", and walked back to Cerulean for water with "walk south" top of
its page (user, 2026-09-16: "build the door sides thats on-screen info").
Pinned: indoors a door on the room's edge names that wall; outdoors a door
in the outer quarter of the map names that part; a door in the middle
names nothing; the label carries it; where a door leads is never said.

Synthetic: no game, no model.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import ledger as L            # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


ck("the gate room's top door is on its north wall",
   L.door_side(3, 0, 8, 6, False) == "on the room's north wall")
ck("...and the door you came in by on its south wall",
   L.door_side(3, 5, 8, 6, False) == "on the room's south wall")
ck("a corner door names both walls",
   L.door_side(0, 0, 8, 6, False) == "on the room's north-west wall")
ck("a door in the middle of a room names nothing",
   L.door_side(4, 3, 8, 6, False) == "")
ck("outdoors, a door in the top quarter is in the north part",
   L.door_side(10, 7, 20, 36, True) == "in the north part of this map")
ck("...a door in the bottom quarter in the south part",
   L.door_side(10, 30, 20, 36, True) == "in the south part of this map")
ck("...and one in the middle of the map names nothing",
   L.door_side(10, 18, 20, 36, True) == "")
ck("no dimensions, or not knowing indoors from out, names nothing",
   L.door_side(3, 0, None, None, False) == ""
   and L.door_side(3, 0, 8, 6, None) == "")
c = L.Candidate(key="3,0", kind="door", dest=None)
c.twins = ["4,0"]
c.side = L.door_side(3, 0, 8, 6, False)
ck("the label carries the side after the width",
   c.label() == "door (3,0), two tiles wide, on the room's north wall")
ck("nothing says where it leads",
   "SAFFRON" not in c.label() and "leads" not in c.label())
src = (ROOT / "planner/ledger.py").read_text()
ck("every door candidate is given its side from the published map",
   'c.side = door_side(w.get("x"), w.get("y"), m.get("width"),' in src)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
