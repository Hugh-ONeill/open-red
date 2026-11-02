#!/usr/bin/env python3
"""Explore is not lured back by doors its last stand already found unreached.

Run 63, 2026-10-24: explore walked to CERULEAN_CITY|8,7 for "3 way(s) out never
taken that no walk reached when you last stood there (27,11, 27,9, 4,11)",
doors behind a guard and a fence, found the same and crossed west (TODO line
3280, open at run 70's stop, 2026-11-02). Same stale-lure class as unseen
ground, which _unseen_there judges by the world mark at the last stand.
Pinned by source in the explore picker: such doors are dropped from the
ranking while the lever-free world mark is what it was at that stand, and
kept once it has moved; never for the part stood in.
"""
import sys
from pathlib import Path

src = (Path(__file__).resolve().parents[1] / "planner/executor.py").read_text()
i = src.index("...BUT NOT A DOOR THE LAST STAND THERE ALREADY FOUND UNREACHED,")
blk = src[i:i + 1400]
checks = [
    ("the mark at the last stand is compared with the mark now",
     '_region_mark_nt' in blk and '_mark_now_nt' in blk
     and "list(_then_m) == list(_now_m)" in blk),
    ("...and the doors drop out only then, never for the part stood in",
     "region != here" in blk and "_unr = []" in blk),
    ("it sits before the picker's skip test",
     i < src.index("if not (left or unpressed or unseen or _unr):", i)),
]
bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
sys.exit(1 if bad else 0)
