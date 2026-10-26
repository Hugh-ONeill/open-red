#!/usr/bin/env python3
"""Explore's picker never offers a lift car as somewhere to walk.

Run 66, 2026-10-25, Rocket Hideout: each round was "elevator B4F, explore",
and explore walked the party from B4F straight back into
ROCKET_HIDEOUT_ELEVATOR|2,1, "which still has 1 exit(s) never taken, 1
thing(s) never pressed" -- the car's re-pointed door and its panel. The row
text already skips cars (ledger._left_parts); the picker did not.

Pinned: the picker loop skips any *_ELEVATOR region before counting it; the
row text's skip still stands.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()
led = (ROOT / "planner/ledger.py").read_text()

checks = []
def ck(n, ok): checks.append((n, bool(ok)))

i = src.index("        for region in regions:\n            # ...NOR ANOTHER NAME FOR IT.")
blk = src[i:i + 2600]
j = blk.index('if str(region).split("|")[0].endswith("_ELEVATOR"):')
ck("the picker skips a lift car", j > 0 and "continue" in blk[j:j + 80])
ck("...before it counts the car's exits", j < blk.index("left = self._frontier_left(region)"))
ck("the row text still skips cars", 'if str(region).split("|")[0].endswith("_ELEVATOR"):\n        return []' in led)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
