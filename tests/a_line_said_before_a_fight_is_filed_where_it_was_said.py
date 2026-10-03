#!/usr/bin/env python3
"""A line said before a fight is filed in the room it was said in.

A press that starts a fight is often made from a view with a box still up (a
field heal or lead swap just before it: map.id None), and the fight ends on
another box, so both ends of the op read None. The hint filing keyed the line
by the room before the op, else after it, found neither, and dropped it, while
the verdict still quoted it: run 25's Channeler on Pokemon Tower 3F, "The
GHOSTs can be identified by the SILPH SCOPE.", reached the trace and the ghost
note but never the hints the NOTABLE ledger reads (three archived runs).

Pinned: the room before the op wins; then the room after (an answer is said
where the answer left you); then the last view that had a map; all three
missing reads None, and the executor journals the line as unplaced instead
of dropping it silently. Synthetic: no game.
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


def o(mid=None, reg=None):
    return {"map": {"id": mid, "region": reg}} if mid or reg else {"mode": "ui"}


TOWER = o("POKEMON_TOWER_3F", "9,1")
ck("the room before the op wins",
   E.said_region(TOWER, o("LAVENDER_TOWN", "6,0"), o("ROUTE_8", "1,1")) == "POKEMON_TOWER_3F|9,1")
ck("a box up before the press: the last view with a map names the room",
   E.said_region(o(), o(), TOWER) == "POKEMON_TOWER_3F|9,1")
ck("...even when the fight ended on a box too",
   E.said_region({"mode": "battle"}, {"mode": "ui"}, TOWER) == "POKEMON_TOWER_3F|9,1")
ck("no map before the op: the room after it, ahead of an older view",
   E.said_region(o(), o("BILLS_HOUSE", "3,4"), o("ROUTE_25", "10,2")) == "BILLS_HOUSE|3,4")
ck("nothing anywhere reads None, as before",
   "None" in E.said_region(o(), o(), None))
src = (ROOT / "planner" / "executor.py").read_text()
ck("the filing uses it, with the last mapped view",
   "reg = said_region(pre_obs, obs, _pre_mapped)" in src)
ck("a line that still has no room is journaled, not silently dropped",
   '"hint_unplaced"' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
