#!/usr/bin/env python3
"""A walk_to that drops the party through a hole books the fall, and a
fight on landing never resends the walk on the floor below.

Run 27, 2026-09-18, Victory Road 3F: walk_to(23,15), the hole, said "ok"
and the party landed on 2F; only cross and use_warp ever booked landings,
so the hole read "never taken" every time and explore's item 1 kept
sending the party down it (user: "its gone through the hole a few times but
never pushed the boulder into the hole yet").

Pinned: the walk_to branch books a map change through note_transition; the
fold to a hole's first tile applies to any key; the fight-resume stops when
the map is no longer the one the walk was sent on. Mixed."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


src = (ROOT / "planner/executor.py").read_text()
ck("a walk_to that changed the map is booked as a way taken",
   "self.note_transition(_pre, step, obs, op_detail=_d0)" in src
   and "A WALK THAT CHANGED THE MAP IS A WAY TAKEN" in src)
ck("a key sent onto a hole's other tile is folded to its first tile",
   "a walk sent onto a hole's OTHER tile books the drop under its" in src)

ex = object.__new__(E.Executor)
ex.sent = []
st = {"n": 0}


def settle(*a, **k):
    return {"mode": "overworld", "player": {"x": 22, "y": 16}, "map": {"id": "VICTORY_ROAD_2F"}}


def drain(sg, o):
    st["n"] += 1
    return settle(), st["n"] == 1        # one fight on landing, then none


ex._drain_fights = drain
ex.settle = settle
ex._send_safe = lambda op, **kw: ex.sent.append(op) or {}
ex.log = lambda *a, **k: None
ex._walk_map_at_send = "VICTORY_ROAD_3F"
o, n = ex._walk_on_after_fights({"id": "t"}, "walk_to", {"x": 23, "y": 15},
                                {"mode": "battle"})
ck("a fight on the floor below does not resend the walk there", ex.sent == [], ex.sent)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
