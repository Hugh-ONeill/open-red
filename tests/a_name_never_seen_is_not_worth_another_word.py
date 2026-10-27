#!/usr/bin/env python3
"""A press on a name nobody has seen is not "somebody worth another word".

Run 67, 2026-10-27: the model pressed interact(name=SAFARI_ZONE_GATE_WARDEN),
a name it made up ("not visible"); the provisional touch mark was never
retracted, and the page went on listing "SAFARI_ZONE_GATE|3,0
(SAFARI_ZONE_GATE_WARDEN — 1 leg(s) away)" as a room worth another word --
a warden at the gate, the wrong fact the run had been looping on for hours.

Pinned: retracting a touch clears its world mark; a mark for a name never
sighted on that map is not re-offered; a sighted one still is.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

R = "SAFARI_ZONE_GATE|3,0"
ex = E.Executor.__new__(E.Executor)
ex._tried_objs = {R: {"SAFARI_ZONE_GATE_WARDEN"}}
ex._touch_mark = {R: {"SAFARI_ZONE_GATE_WARDEN": {"then": ["old"], "n": 0, "at": None},
                      "SAFARIZONEGATE_SAFARI_ZONE_WORKER1": {"then": ["old"], "n": 0, "at": None}}}
ex.sightings = {R: ["SAFARIZONEGATE_SAFARI_ZONE_WORKER1", "SAFARIZONEGATE_SAFARI_ZONE_WORKER2"]}
ex._gone = {}
ex._world_mark = lambda o: ["now"]

names = ex._worth_another_word(R, {}, backfill=False)
ck("a made-up name is not re-offered", "SAFARI_ZONE_GATE_WARDEN" not in names, names)
ck("...a person the run saw still is", "SAFARIZONEGATE_SAFARI_ZONE_WORKER1" in names, names)
ex._retract_touch(R, "SAFARI_ZONE_GATE_WARDEN")
ck("retracting a touch clears its world mark",
   "SAFARI_ZONE_GATE_WARDEN" not in ex._touch_mark[R]
   and "SAFARI_ZONE_GATE_WARDEN" not in ex._tried_objs[R], ex._touch_mark)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
