#!/usr/bin/env python3
"""An op struck out because something was IN THE WAY is tried again once
the screen shows that way clear.

Run 27, 2026-09-17: SAFFRONCITY_ROCKET8 stood on Silph Co's door at
(18,22) and said "I'm a security guard. Suspicious kids I don't allow in!".
use_warp(18,21) came to nothing, banked three strikes, and the gate refused
it thereafter as "nothing about you changed since" — which is measured by
badges, event flags and bag kinds. The Rocket then left; the door read
reachable; the gate went on refusing, four attempts of the leg (user: "has
it entered silph co yet?").

Pinned: a strike whose recorded reason was a body or an unreachable way
stands down when the observation now shows that doorway reachable, or that
named thing present and reachable; the round says so in its own trace; a
strike for any other reason, or with the way still blocked, still refuses.
Synthetic.
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


WHY = ("couldn't reach the warp at (18,21) — SAFFRONCITY_ROCKET8 is "
       "standing there")


def fake(obs):
    ex = object.__new__(E.Executor)
    ex._dead_ops = {"S": 3}
    ex._dead_why = {"S": WHY}
    ex._dead_at = {}
    ex._mark_now = [4, 30, 19]
    ex.settle = lambda: obs
    ex.log = lambda *a, **k: None
    return ex


OPEN = {"map": {"warps": [{"x": 18, "y": 21, "reachable": True}],
                "objects": [{"name": "SAFFRONCITY_ROCKET9", "x": 19, "y": 22,
                             "reachable": True}]}}
SHUT = {"map": {"warps": [{"x": 18, "y": 21, "reachable": False}],
                "objects": [{"name": "SAFFRONCITY_ROCKET8", "x": 18, "y": 22,
                             "reachable": True}]}}

ex, tr = fake(OPEN), []
ck("a warp the screen now shows reachable lifts the strike",
   ex._gated("S", "use_warp", {"x": 18, "y": 21}, tr) is False, tr)
ck("...the strikes start over", ex._dead_ops["S"] == 0)
ck("...and the round says what changed",
   tr and "is not in the way now" in tr[0] and "no walk to it is blocked" in tr[0], tr)

ex, tr = fake(SHUT), []
ck("a warp still unreachable still refuses",
   ex._gated("S", "use_warp", {"x": 18, "y": 21}, tr) is True
   and "REFUSED" in tr[0], tr)
ex, tr = fake({"map": {"warps": [], "objects": []}}), []
ck("a warp not on screen at all still refuses",
   ex._gated("S", "use_warp", {"x": 18, "y": 21}, tr) is True, tr)

ex, tr = fake(SHUT), []
ex._dead_why = {"S": "object 'SAFFRONCITY_ROCKET8' not visible"}
ck("a named thing back on screen and reachable lifts its strike",
   ex._gated("S", "interact", {"name": "SAFFRONCITY_ROCKET8"}, tr) is False, tr)
ex, tr = fake(OPEN), []
ex._dead_why = {"S": "object 'SAFFRONCITY_ROCKET8' not visible"}
ck("...but not while it is still off screen",
   ex._gated("S", "interact", {"name": "SAFFRONCITY_ROCKET8"}, tr) is True, tr)

ex, tr = fake(OPEN), []
ex._dead_why = {"S": "cannot afford FRESH_WATER: it costs 200 and you have 3"}
ck("a strike for another reason is untouched",
   ex._gated("S", "use_warp", {"x": 18, "y": 21}, tr) is True, tr)
ex, tr = fake(OPEN), []
ex._dead_ops["S"] = 2
ck("under three strikes the gate never fires",
   ex._gated("S", "use_warp", {"x": 18, "y": 21}, tr) is False and tr == [])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
