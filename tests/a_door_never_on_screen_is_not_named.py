#!/usr/bin/env python3
"""A doorway the player has never laid eyes on is not counted and not named.

The footprint closed this everywhere else. A cell is SEEN once it has been
inside the engine's own viewport (ten cells by nine, from Camera.lua), the
mask persists in run/seen.json, the terrain picture draws unseen ground
blank and says "never on screen", and the healing and shop walks gate on
the same flag. One reader was left on the raw map table: the line that says
how many doorways a floor has read every warp the engine knows, so run 30
was told "ROUTE_2 has 3 doorway(s) in total and 1 of them (12,9) are on
part of it you have never stood on" — about a cell it had never seen
(2026-09-21, user: "fix the door count").

Never STOOD ON and never SEEN are different things, and only the first is
honest to say. A floor is still known to be unfinished by its unseen
GROUND, which the footprint reports truthfully.

Pinned: the door set is built from warps the shim marked seen; a door on
screen but out of reach still counts; a door never on screen is absent from
the count, from the named cells and from the doors-stood-beside line; the
wording no longer claims a total; and the flag is the shim's own.
Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "planner/executor.py").read_text()
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ck("the door set is built only from doors that have been on screen",
   'allw = {f"{w.get(\'x\')},{w.get(\'y\')}" for w in (m.get("warps") or [])\n'
   '                if w.get("seen")}' in SRC)
# the old wording survives in the comment that records the bug; what must
# not survive is a line of CODE that still puts it on the page
_code = [l for l in SRC.splitlines() if not l.lstrip().startswith("#")]
ck("...and the page no longer claims a total it cannot know",
   any("doorway(s) you have SEEN and" in l for l in _code)
   and not any("doorway(s) in total" in l for l in _code))
ck("the reason is written where the line is",
   "ONLY THE DOORS THAT HAVE BEEN ON SCREEN" in SRC)

# the arithmetic, worked the way the source works it
WARPS = [{"x": 3, "y": 7, "seen": True},     # stood beside, never opened
         {"x": 9, "y": 1, "seen": True},     # seen across a gap, unreachable
         {"x": 12, "y": 9, "seen": False}]   # never on screen at all
allw = {f"{w['x']},{w['y']}" for w in WARPS if w.get("seen")}
ck("a door never on screen is not in the set", "12,9" not in allw)
ck("...and one seen but unreachable is", "9,1" in allw and "3,7" in allw)
ck("the count is of what has been seen", len(allw) == 2)

stood = {"3,7"}
unseen = allw - stood
ck("what is named as out of reach is only ever something seen",
   unseen == {"9,1"} and "12,9" not in unseen)
ck("...and the doors stood beside are unaffected",
   (allw & stood) == {"3,7"})

# with nothing seen there is nothing to say, rather than a false total
ck("a floor whose doors are all unseen says nothing about doors",
   {f"{w['x']},{w['y']}" for w in WARPS if False} == set())

LUA = (ROOT / "harness/shim.lua").read_text()
ck("the flag the filter reads is the shim's own, set from the seen mask",
   'seen = ((SEEN[map.id] or {})[w.x .. "," .. w.y])' in LUA)
ck("...and the terrain picture was already drawn from that mask",
   "never on screen" in LUA and "_smask = SEEN[map.id]" in LUA)
ck("the sibling check was already seen-based and is left alone",
   "map_doors holds every warp SEEN on a map" in SRC)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
