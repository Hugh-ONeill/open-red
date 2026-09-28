#!/usr/bin/env python3
"""Seen ground that nothing on the floor leads onto is counted apart, not
offered as ground whose way on is not known.

Run of record 12 (2026-09-27): Diglett's Cave is one tunnel cut through a
rectangle, and the rock around it is drawn with tiles the collision table
calls passable. Walked end to end, the page still said "GROUND YOU HAVE SEEN
BUT CANNOT WALK TO FROM HERE: 462 cell(s) ... the way onto it is not known",
and the run wrote "a large section of the cave remains unseen ... locate the
eastern exit to Route 10" three times (user: "the shape preventing most of
the square area from being seen"). Booting that checkpoint on the new shim
gives n 0, sealed 462; a Cerulean checkpoint's 12 cells cut off by its fence
and open to the map's edge stay "not known" (n 12, sealed 0).

Pinned: the shim sorts unreached cells into pockets and calls one sealed only
with no doorway, no water, nobody between it and walked ground, not too big
to finish, and no edge that leads anywhere (an indoor edge leads nowhere);
the page says sealed ground for what it is; the walkable count subtracts it.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
import ledger as L  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


sh = (ROOT / "harness/shim.lua").read_text()
ck("the shim floods each unreached cell's pocket once",
   "local pk = pocket_of(G, u.x, u.y, dist, 2000)" in sh and "out.cells = seen" in sh)
ck("...and calls it sealed only with no door, water, person, size or real edge",
   "local shut = pk and not pk.big and not pk.joins and not pk.wet\n"
   "                       and pk.all_seen\n"
   "                       and #pk.doors == 0 and (indoor or not pk.edge)" in sh)
ck("...publishing the sealed count beside the rest",
   "sealed = sealed_n }" in sh and "{ n = 0, sealed = sealed_n, near = {}, from = {} }" in sh)

led = (ROOT / "planner/ledger.py").read_text()
ck("the page says sealed ground for what it is",
   "pockets with no doorway, no water beside them and no edge " in led
   and "that leads anywhere: nothing on this floor leads onto them" in led)
ck("...and never calls it a way not known",
   led.index('int(_su.get("sealed") or 0) > 0') > led.index("the way onto it is not known"))

obs = {"map": {"seen": {"n": 726}, "seen_unreached": {"n": 0, "sealed": 462}}}
ck("the walkable count subtracts sealed ground too",
   E.Executor._walkable_here(obs) == 264, E.Executor._walkable_here(obs))
obs = {"map": {"seen": {"n": 100}, "seen_unreached": {"n": 12}}}
ck("...and a shim without the field reads as before",
   E.Executor._walkable_here(obs) == 88)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
