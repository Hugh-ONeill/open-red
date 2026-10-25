#!/usr/bin/env python3
"""The "nothing in this room serves the goal" walk never takes the party to a
part of the target map the step's not_area rules out.

Run 65, 2026-10-24: reach_mt_moon_east_exit was {"map": "ROUTE_4", "not_area":
["ROUTE_4|4,4"]}; standing in the fossil room, this walk took the party three
legs to ROUTE_4|4,4, the excluded part, round after round, undoing the
model's way toward the east exit.

Pinned: the region scan skips parts in not_area.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

src = (ROOT / "planner" / "executor.py").read_text()
i = src.index('f"Nothing in THIS room serves the goal, so the "')
blk = src[i - 2600:i]
ck("the step's not_area is read", '_na = (sg.get("done_when") or {}).get("not_area") or []' in blk, blk[-900:])
ck("...and a ruled-out part is skipped", "if region in _na:\n                                continue" in blk)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
