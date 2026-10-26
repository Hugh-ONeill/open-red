#!/usr/bin/env python3
"""The "Rooms you have SEEN things in that you have never touched" line uses
the ledger's own subtraction.

Run 67, 2026-10-26, Mt Moon: the line kept its own (presses in that part only,
nothing beaten), so 1F|2,2's four trainers, beaten on sight and pressed from
1F|3,2, read as never touched while the run circled B1F and B2F.

Pinned: the line reads ledger.untouched_in, which counts a press from any part
of the map, a thing gone, and a trainer the screen showed beaten.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()
checks = []
def ck(n, ok): checks.append((n, bool(ok)))

i = src.index('remote_line += ("\\nRooms you have SEEN things in that you have "')
blk = src[i - 2600:i]
ck("the line subtracts with ledger.untouched_in", "_ut = set(ledger.untouched_in(self, region))" in blk)
ck("...and no longer by this part's presses alone", "got = self._tried_objs.get(region, set())" not in blk)
led = (ROOT / "planner/ledger.py").read_text()
ck("untouched_in drops beaten trainers", 'getattr(ex, "_beaten_seen", None)' in led)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
