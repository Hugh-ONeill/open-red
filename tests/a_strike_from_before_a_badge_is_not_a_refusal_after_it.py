#!/usr/bin/env python3
"""A strike earned in another world is not a refusal in this one.

Pewter's east cross was struck out three times while the guide boy walked
the run back to the gym ("You're a trainer right? BROCK's looking for new
challengers! Follow me!"). BOULDERBADGE was won, and the next leg's cross
east was refused "with nothing about you changed since" every round until
the step ended idle (run 44, 2026-10-10). The world mark was only compared
on the NEXT failure, and a refused op never fails again.

Pinned: the gate compares the strike's world mark with the world now and
lets the op through when they differ; an unchanged world is still refused.
Data from run 44's explored.json. Synthetic.
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


SIG = ("map:ROUTE_3", "PEWTER_CITY|4,2", "cross", "east", None, None, None, None, None)
WHY = ("couldn't reach east edge gap (39,17), stuck at (29,18) — during this walk someone "
       "spoke and the walk ended short: \"You're a trainer right?")
BEFORE = {"badges": [], "flags": ["EVENT_GOT_POKEDEX"], "bag": {"POKE_BALL": 5},
          "map": {"id": "PEWTER_CITY", "width": 40, "height": 36}, "player": {"x": 30, "y": 17}}
AFTER = dict(BEFORE, badges=["BOULDERBADGE"],
             flags=["EVENT_GOT_POKEDEX", "EVENT_BEAT_BROCK"])


def rig(now):
    ex = E.Executor.__new__(E.Executor)
    ex._dead_ops = {SIG: 3}
    ex._dead_at = {SIG: E.Executor._world_mark(BEFORE)}
    ex._dead_why = {SIG: WHY}
    ex.logged = []
    ex.log = lambda kind, **kw: ex.logged.append((kind, kw))
    ex.settle = lambda: now
    ex._mark_now = E.Executor._world_mark(now)
    return ex


ex, trace = rig(AFTER), []
ok = ex._gated(SIG, "cross", {"op": "cross", "dir": "east"}, trace)
ck("after the badge the struck cross is let through", ok is False, trace)
ck("...its count starts over", ex._dead_ops[SIG] == 0)
ck("...against the world it is in now", ex._dead_at[SIG] == E.Executor._world_mark(AFTER))
ck("...the round says why it is tried again", any("changed since" in t for t in trace), trace)
ck("...and the expiry is logged", any(k == "strike_expired" for k, _ in ex.logged))

ex, trace = rig(BEFORE), []
ok = ex._gated(SIG, "cross", {"op": "cross", "dir": "east"}, trace)
ck("in the same world it is still refused", ok is True and "REFUSED" in " ".join(trace), trace)
ck("...and the count is kept", ex._dead_ops[SIG] == 3)

ex, trace = rig(dict(BEFORE, bag={"POKE_BALL": 5}, flags=list(BEFORE["flags"]))), []
ck("a mark stored as a JSON list still matches the same world",
   (ex._dead_at.__setitem__(SIG, list(ex._dead_at[SIG])) or True)
   and ex._gated(SIG, "cross", {"op": "cross", "dir": "east"}, trace) is True)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
