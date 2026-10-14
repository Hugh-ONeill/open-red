#!/usr/bin/env python3
"""A crossing step this plan met is not re-opened by the backtrack
(run 57, 2026-10-14).

find_rocket_hideout ({"new_map_from": "CELADON_CITY"}) was met when the run
walked into the hideout. retrieve_silph_scope then beat GIOVANNI on B4F and
ran out of rounds two steps from the SILPH SCOPE he left; the backtrack
found find_rocket_hideout false (it holds only on the map the crossing led
to) and re-opened it, the model rode the lift up to "find the hideout"
again, and the Scope stayed on the floor. A new_map_from step not carried
past unmet stays done and the scan goes on to an earlier step.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

src = (ROOT / "planner" / "executor.py").read_text()
i = src.index("for back in range(idx - 1, max(-1, idx - 5), -1):")
loop = src[i:i + 9000]
blk = loop[loop.index("if not h:"):loop.index("A PLACE STEP IS NOT UNDONE")]
ck("the scan skips a crossing step whose condition no longer reads true",
   '"new_map_from" in _dw0' in blk and "continue" in blk)
ck("...only when it was met, not carried past unmet",
   '_carried_ids' in blk and "not in" in blk)
ck("...and says so in the journal", '"backtrack_crossing_held"' in blk)
ck("the guard comes before a candidate is taken",
   loop.index('"backtrack_crossing_held"') < loop.index("cand, holds = c, False"))

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok  " if ok else "FAIL"), n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)
