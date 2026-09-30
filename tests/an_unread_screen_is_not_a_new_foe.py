#!/usr/bin/env python3
"""A battle screen that could not be read does not count as a new foe.

Between knockouts the observation often carries no foe; it counted as one,
and the real foe after it as another, so per-foe setup rules re-armed on the
same Pokemon and the count ran 2, 4, 6, 8 through the rival's six (run 19,
2026-09-30).

Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as B  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ctx = {"turn": 1}
pidgeot = {"species": "PIDGEOT", "level": 61, "hp": 182, "maxhp": 182}
alakazam = {"species": "ALAKAZAM", "level": 59, "hp": 160, "maxhp": 160}
ck("the first foe is foe 1", B._foe_clock(ctx, pidgeot) == (1, 1))
ctx["turn"] = 3
ck("an unread screen changes nothing", B._foe_clock(ctx, {})[0] == 1)
ctx["turn"] = 4
ck("...and the same foe after it is still foe 1, three turns in",
   B._foe_clock(ctx, dict(pidgeot, hp=90)) == (1, 4))
ctx["turn"] = 6
B._foe_clock(ctx, {})
ck("the next real foe is foe 2, not 4", B._foe_clock(ctx, alakazam)[0] == 2)
ck("an unread screen before any foe reads as the first",
   B._foe_clock({"turn": 1}, {}) == (1, 1))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
