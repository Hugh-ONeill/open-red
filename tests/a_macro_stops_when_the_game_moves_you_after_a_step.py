#!/usr/bin/env python3
"""A macro stops when the game moves you after a step (run 18, 2026-09-28).

walk_to(5,5) on Mt. Moon 1F stood on the ladder and returned "ok"; the game
took the party down a frame later, and the next op, use_warp(5,5) written
for 1F, ran on B1F and went straight back up. The new ladder was ledgered as
spent. The rest of a macro was written for the map it started on: when the
map at the start of a step is not the map the last step ended on, stop, and
say where the game carried you.

Source checks (the late warp needs a live game).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()
checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


loop = src[src.index("        for _mi, step in enumerate(macro):"):]
ck("the end map is reset before the steps run",
   "self._macro_end_map = None\n        for _mi, step in enumerate(macro):" in src)
ck("each step's end map is kept",
   "after = self._snapshot(obs)\n            self._macro_end_map = after[0]" in src)
ck("a step that starts on another map stops the macro, logged",
   'self.log("macro_cut_map_moved"' in loop
   and "_now_map != self._macro_end_map" in loop)
ck("...and the trace says where the game carried you",
   "and then the game carried you" in loop and "from where you stand" in loop)
ck("the check comes before the done test and the when-guard",
   loop.index('"macro_cut_map_moved"') < loop.index("if when and not pred_holds(when, obs):"))

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
