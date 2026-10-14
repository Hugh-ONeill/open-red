#!/usr/bin/env python3
"""A machine aimed at a Pokemon that already knows its move says so
(run 57, 2026-10-14).

GRAVELER knew SELFDESTRUCT; TM36 aimed at it was answered by the
four-moves guard, "re-send it with forget= one of those four", and the run
re-sent it with ROCK_THROW, DOUBLE_EDGE and EARTHQUAKE in turn, getting the
same sentence each time, with the bag slot it needed for the CARD KEY still
full. The shim now refuses before the four-moves guard: the Pokemon already
knows the move, no forget= will help, and who else ABLE does not know it.
Probed in game on a run 57 save with TM36 added: unpatched gave the
four-moves line with and without forget=; patched gave this one both times,
TM unspent, overworld.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = (ROOT / "harness" / "shim.lua").read_text()
fails = []


def ck(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


i_known = src.find('" ALREADY KNOWS " .. _mvname')
i_four = src.find('" already knows four moves: "')
ck("the shim refuses a move the Pokemon already knows", i_known > 0)
ck("...before the four-moves guard can ask for a forget=", 0 < i_known < i_four)
blk = src[src.rfind("A MOVE IT ALREADY KNOWS IS NOT TAUGHT AGAIN", 0, i_known):i_known + 400]
ck("...whatever forget= was sent (it sits outside the 'not c.forget' guard)",
   "not c.forget" not in blk)
ck("...and says no forget= will help, and who else could take it",
   "no forget= will help" in blk and "do not know it yet" in blk)

print(f"\n{'FAIL' if fails else 'ok'} {len(fails)} failed")
sys.exit(1 if fails else 0)
