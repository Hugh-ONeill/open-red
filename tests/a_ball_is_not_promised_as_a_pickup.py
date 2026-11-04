#!/usr/bin/env python3
"""The page does not promise that pressing a ball takes it.

Run 71, 2026-11-02, visit_professor_oak: the page listed Oak's three starter
balls (ITEM_OAKS_LAB_6_3/7_3/8_3) as "lying on the ground, never picked up
— PRESS IT: pressing A takes it and it costs nothing". Before his escort
they only speak and are never taken, so "takes it" was the harness's own
false claim, and it drew the run back into the lab twice. Whether a ball is
a pickup is not on the screen (an item ball and a starter ball look alike);
that a press costs nothing and shows what it is, is true of every one.

Pinned: the untouched-ball line invites the press without saying it takes
the ball; the full-bag and no-walk clauses stay. Source shape.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
lg = (ROOT / "planner/ledger.py").read_text()

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

i = lg.index('if c.kind == "item" and c.status == "untouched":')
blk = lg[i:i + 4200]
ck("the line no longer says pressing A takes it",
   '"PRESS IT: pressing A takes it' not in blk)
ck("...it says what is true of every ball",
   '"PRESS IT: pressing A costs nothing, and what it is "' in blk
   and '"shows when you do"' in blk)
ck("the full-bag clause is kept", "the BAG IS FULL (20 of 20 kinds)" in blk)
ck("the no-walk clause is kept", "WALKING TO IT IS NOT THE JOB" in blk)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
raise SystemExit(1 if bad else 0)
