#!/usr/bin/env python3
"""The room sweep's summary lists the presses that happened, and names the
ones that failed, instead of the eight it set out to make.

Run 62, 2026-10-23: warped onto Silph Co. 5F's pad room, the arrival sweep
pressed the Card Key ball (ITEM_SILPH_CO_5F_21_16), got "no reachable tile",
recorded no touch, and still wrote "(swept this area: pressed A on ...
ITEM_SILPH_CO_5F_21_16 — everything reachable here that PRESSES has now
been tried)". The run never stood in that room again and spent the leg at
escalation 28 hunting the Card Key on other floors.

Pinned (source; the sweep lives inside a long method): the names actually
sent are kept, a press that recorded no touch and asked nothing is filed as
failed with its reason, the summary is built from what was sent and not
failed, a failed press is said with its reason, and "everything reachable
here ... has now been tried" needs no failure.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


src = (ROOT / "planner" / "executor.py").read_text()
i = src.find("_sent, _failed = [], []")
blk = src[i:i + 9000] if i > 0 else ""
ck("the sweep keeps the names it actually sent", i > 0 and "_sent.append(name)" in blk)
ck("a press that took nothing and asked nothing is filed as failed",
   "_failed.append((name, _det))" in blk)
ck("the pressed list is what was sent and did not fail",
   "_pressed = [n for n in _sent if n not in _fn]" in blk)
ck("what was never sent is still left", "_left = [n for n in loose if n not in _sent]" in blk)
ck("a failed press is said, with its reason", "the sweep could NOT press" in blk)
ck("\"everything ... tried\" needs no failure",
   "if _pressed and not _left and not _failed:" in blk)
ck("the old list-of-intent is gone", "_pressed = list(loose[:8])" not in src)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
