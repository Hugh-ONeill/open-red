#!/usr/bin/env python3
"""A dry leg is never cut on the round that found something new.

Run 67, 2026-10-27: the leg "Give the GOLD TEETH to the Warden" was judged
dry (2 of its last 40 rounds new) on the round that walked into
FUCHSIA_MEETING_ROOM, a map never stood on, the first of three untried
Fuchsia doors the model had at last turned to.

Pinned: a full dry window is cut on a dry round; the same window is not cut
on a round that gained; the gaining round still counts, so the next dry
round can cut.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

def rig():
    ex = E.Executor.__new__(E.Executor)
    ex.log = lambda *a, **k: None
    ex._target_key = lambda sg: "lacks_item:GOLD_TEETH"
    ex._leg_rounds = [0] * (E.Executor.LEG_DRY_WINDOW - 1)
    ex._attempt_rounds = E.Executor.LEG_DRY_GRACE + 5
    return ex

sg = {"id": "speak_to_warden_in_city"}
ex = rig()
ck("a dry window is cut on a dry round", ex._leg_dry_round(sg, 12, False) is True)
ex = rig()
ck("...but not on the round that found something", ex._leg_dry_round(sg, 12, True) is False)
ck("...which still counts", ex._leg_rounds[-1] == 1, ex._leg_rounds[-3:])
ex._leg_rounds[-E.Executor.LEG_DRY_WINDOW:-1] = [0] * (E.Executor.LEG_DRY_WINDOW - 1)
ck("...and the next dry round can still cut", ex._leg_dry_round(sg, 13, False) is True)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
