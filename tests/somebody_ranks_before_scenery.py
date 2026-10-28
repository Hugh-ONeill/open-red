#!/usr/bin/env python3
"""Rooms with somebody never pressed rank before rooms with only scenery.

Run 67, 2026-10-28: "Rooms you have SEEN things in that you have never
touched" showed four slots, three of them CUT_TREE in parts of Celadon and
Route 16; the Diner's five people, the Coin Case giver among them, never
reached the line.

Pinned (source shape; the line is built inside the escalation page): the sort
key puts rooms whose untouched things are all bushes/boulders/signs after the
rest, distance ordering each group; later the same day a room with an
untaken ball ranks before one with only people (Mansion B1F's (5,13), the
Secret Key, lost the slots to Cinnabar's nurse and clerks), five slots.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner" / "executor.py").read_text()
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ck("scenery is judged per room",
   '_scenery = all(str(n) == "CUT_TREE" or "BOULDER" in str(n)' in src
   and 'or str(n).startswith("SIGN_") for n in left)' in src)
ck("the sort key puts scenery-only rooms last, and a ball before a person",
   '_ball = any(str(n).startswith("ITEM_") for n in left)' in src
   and "held.append(((2 if _scenery else 0 if _ball else 1, len(path))," in src)
ck("the cap (five since run 67's Mansion B1F ball) and wording stay",
   '"; ".join(t for _, t in held[:5])' in src
   and '"\\nRooms you have SEEN things in that you have "' in src)

bad = [c for c in checks if not c[1]]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok else f"\n      {str(d)[:300]}"))
print(f"{len(checks) - len(bad)}/{len(checks)} checks pass")
sys.exit(1 if bad else 0)
