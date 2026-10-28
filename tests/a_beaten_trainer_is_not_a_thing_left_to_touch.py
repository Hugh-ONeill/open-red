#!/usr/bin/env python3
"""A trainer the screen shows beaten is not offered as a thing left to touch.

Run 67, 2026-10-28, Route 20: every swimmer read beaten, and the failed
cross west said "Do NOT conclude this area is a dead end yet: you can
reach 2 thing(s) here you have never interacted with (ROUTE20_SWIMMER2,
ROUTE20_SWIMMER3) ... Interact with all of them before leaving"; the run
spent a round pressing them on the way to Cinnabar.

Synthetic.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

x = object.__new__(E.Executor)
x.pad_lands = {}
x._beaten_seen = {"ROUTE20_SWIMMER3"}
cur = {"map": {"id": "ROUTE_20", "objects": [
    {"name": "ROUTE20_SWIMMER2", "kind": "trainer", "reachable": True, "beaten": True},
    {"name": "ROUTE20_SWIMMER3", "kind": "trainer", "reachable": True},
    {"name": "ROUTE20_SWIMMER4", "kind": "trainer", "reachable": True}]}}
txt = " ".join(x._untouched_lines(
    cur, ["ROUTE20_SWIMMER2", "ROUTE20_SWIMMER3", "ROUTE20_SWIMMER4"], []))
ck("a trainer the obs shows beaten is not offered", "SWIMMER2" not in txt, txt)
ck("...nor one the run saw beaten", "SWIMMER3" not in txt, txt)
ck("...one not beaten still is",
   "you can reach 1 thing(s)" in txt and "(ROUTE20_SWIMMER4)" in txt, txt)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
