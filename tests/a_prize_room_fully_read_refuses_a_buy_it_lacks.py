#!/usr/bin/env python3
"""A plan that buys at a prize room whose every counter was read, a thing
none of them lists, is refused like a buy at a read shelf.

Run 67, 2026-10-28: leg 52 was written five times as "enter the prize
room, purchase SECRET_KEY" with all three Game Corner lists kept (ABRA ...
TM50) and printed on the page; the shelf rule knew only mart shelves.

Pinned: refused once every counter is read; not while one is unread; a
coin step in the room is not; a prize it lists is not.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

V = "TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_"
SEEN = {"GAME_CORNER_PRIZE_ROOM|0,3": [V + "1", V + "2", V + "3"]}
ALL = {V + "1": ["ABRA (180 coins)"], V + "2": ["DRATINI (2800 coins)"],
       V + "3": ["TM23 (3300 coins)"]}

def plan(want):
    return {"goal": "Retrieve the Secret Key from the Game Corner", "subgoals": [
        {"id": "corner", "goal": "Enter the Game Corner", "done_when": {"map": "GAME_CORNER"}},
        {"id": "room", "goal": "Enter the prize room", "done_when": {"map": "GAME_CORNER_PRIZE_ROOM"}},
        {"id": "buy", "goal": "Exchange coins for it", "done_when": {"has_item": want}}]}

def hits(p):
    return [x for x in A.validate(p) if "lists as prizes" in x]

d = Path(tempfile.mkdtemp(prefix="prizeroom_"))
(d / "run").mkdir()
here = os.getcwd()
os.chdir(d)
try:
    (d / "run/explored.json").write_text(json.dumps({"prize_lists": {"GAME_CORNER_PRIZE_ROOM": ALL}, "sightings": SEEN}))
    h = hits(plan({"SECRET_KEY": 1}))
    ck("a buy none of the read counters lists is refused",
       h and "SECRET_KEY is not on it" in h[0] and "DRATINI" in h[0], h)
    ck("...a prize it does list stands", hits(plan({"DRATINI": 1})) == [])
    ck("...and coins in the room stand", hits(plan({"COIN": 2000})) == [])
    (d / "run/explored.json").write_text(json.dumps({"prize_lists": {"GAME_CORNER_PRIZE_ROOM": {V + "1": ALL[V + "1"]}}, "sightings": SEEN}))
    ck("with a counter never opened, nothing is claimed", hits(plan({"SECRET_KEY": 1})) == [])
finally:
    os.chdir(here)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
