#!/usr/bin/env python3
"""The lift sits out the arrival announcement instead of handing the model
a box to press B at.

A Silph ride ends in ElevatorShake's "pa" phase, which holds while the
arrival chime plays and then pops itself (src/world/ElevatorShake.lua's
.musicLoop). The op's wait loop could come out the far side while that phase
still ran, and the step-out below is gated on the overworld being on top, so
the op answered "you are still IN the car; a screen is STILL up that would
not close (phase=pa)". The model then spent a whole round tapping B at a
clock — "ran but had NO visible effect" every time — and walked out the
round after (user, 2026-09-09: "is it still actually having the b-press
elevator issue or are we just still telling it that"). Now the op waits for
the clock before it reports, and if a timed state somehow survives that, the
words say it is a clock rather than inviting a keypress.

The clock is an audio source, so it runs in wall time: 900 frames ran out
before it on all five rides of run 20, and every one handed the model the
phase=pa jargon (user, 2026-10-01: "clean up the whole press b rigamarole
message with the elevator"). The wait now also holds for wall time.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sh = (ROOT / "harness" / "shim.lua").read_text()
fails = []


def ck(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


i = sh.index("function OPS.elevator")
blk = sh[i:sh.index("-- CHOOSE WHO GOES OUT FIRST", i)]
ck("the op drains a timed state before it gives up", "A TIMED STATE IS NOT A STUCK BOX: SIT IT OUT." in blk and "while _is_fade(G.stack:top()) do" in blk)
ck("...for its frames AND for wall time, since the chime is real audio",
   "_n >= 900 and (not _t0 or _clock() - _t0 >= 10)" in blk and "love.timer.getTime" in blk)
ck("...before the step-out, which is gated on the overworld", blk.index("while _is_fade(G.stack:top()) do") < blk.index("AND THEN WALK OUT"))
ck("the old would-not-close verdict is gone from what the model is TOLD",
   'A screen is STILL up that would not close ("' not in blk and 'A screen is still up' not in blk)
ck("a surviving timed state is named as the chime, in plain words", "The arrival chime is still playing; it ends " in blk and "phase=" not in blk.split("AND IF IT IS STILL UP")[1])
ck("...and no longer asks for a B press", '{\\"op\\":\\"tap\\",\\"btn\\":\\"b\\"} "\n              .. "before walking out"' not in blk)
sys.exit(1 if fails else 0)
