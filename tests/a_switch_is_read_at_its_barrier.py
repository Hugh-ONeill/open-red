#!/usr/bin/env python3
"""A boulder switch's state is kept while its barrier is in view, not only
while the switch is.

Run 27, 2026-09-18, Victory Road 1F: entering 2F resets 1F's switch (the
game's own script). Back on 1F, the switch (17,13) was off screen and its
barrier (8,12) in plain view and shut, but the shim dropped the state with
the switch out of view, so the page said "the last time it was on screen
its way was OPEN" and the run never shoved a boulder back onto it; three
attempts ended there (user: "it shouldnt have a problem with the
puzzles").

Pinned: the shim keeps open_now while either the switch or the cell it
opens is in view. Source-anchored: the observation runs in the game."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


lua = (ROOT / "harness/shim.lua").read_text()
i = lua.index("AN OFF-SCREEN SWITCH'S POSITION IS NOT KNOWN UNTIL RE-SEEN")
blk = lua[i:i + 2500]
ck("the state is dropped only when neither the switch nor its barrier is in view",
   "if ex and not _in_view(ex, ey)\n             and not _in_view(e.opens_x, e.opens_y) then\n            e.open_now = nil" in blk)
led = (ROOT / "planner/ledger.py").read_text()
ck("the page's open-then-shut wording is what a kept state feeds",
   "IT WAS OPEN THE LAST TIME YOU STOOD ON THIS" in led)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
