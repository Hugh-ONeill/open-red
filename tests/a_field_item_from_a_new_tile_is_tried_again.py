#!/usr/bin/env python3
"""A field item struck out from one tile is tried again from another.

Run 67, 2026-10-27, leg 39 "Wake the Snorlax": the POKE FLUTE came to
nothing three times from (26,8) ("A field item acts on what you are standing
RIGHT NEXT TO"), the party then stood at (27,10) beside ROUTE16_SNORLAX, and
the flute was refused "with nothing about you changed since" because the
strike key is the area, not the tile.

Pinned: the strike lifts from a tile it was never tried from, naming both;
it holds on a tile it was tried from; other ops are unchanged.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

WHY = ('used POKE_FLUTE and NOTHING HAPPENED — the game said "Now, that\'s a '
       'catchy tune!"')
ex = E.Executor.__new__(E.Executor)
ex._dead_ops, ex._dead_why, ex._dead_at = {}, {}, {}
ex._mark_now = ("m",)
sig = ("flag:EVENT_BEAT_ROUTE16_SNORLAX", "ROUTE_16|27,10", "use_item",
       (None, None), "POKE_FLUTE", None, None, None, None)
for _ in range(3):
    ex._strike(sig, WHY, at=("ROUTE_16", 26, 8))
ck("three strikes banked", ex._dead_ops[sig] == 3, ex._dead_ops)

def obs(x, y):
    return {"map": {"id": "ROUTE_16"}, "player": {"x": x, "y": y}}

st = {"op": "use_item", "item": "POKE_FLUTE"}
t = ex._strike_reason_lifted(sig, "use_item", st, obs(27, 10))
ck("from a new tile the flute is tried again",
   "(27,10)" in t and "(26,8)" in t, t)
t = ex._strike_reason_lifted(sig, "use_item", st, obs(26, 8))
ck("from the struck tile it stays refused", t == "", t)
ex._dead_spots = {}
t = ex._strike_reason_lifted(sig, "use_item", st, obs(27, 10))
ck("with no tiles kept (an older memory file) it stays refused", t == "", t)
ex._dead_why[sig] = "no path"
t = ex._strike_reason_lifted(sig, "walk_to", {"op": "walk_to", "x": 1, "y": 1}, obs(27, 10))
ck("other ops are unchanged", t == "", t)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
