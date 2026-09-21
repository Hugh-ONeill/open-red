#!/usr/bin/env python3
"""A grind says "no Poke Balls" only about the battles it met itself.

The flag is raised when a catch policy meets a wild with an empty bag, and
the next GRIND's note reads it. Nothing lowered it in between, so wilds met
on a plain walk left it standing for whichever grind came next. Run 29
walked Route 1 with no balls (seven such battles), bought ten in Viridian
at t+384s, and its first grind at t+402s reported "NO POKé BALLS of any
kind in the bag, so nothing could be caught" — with POKE_BALL x10 on the
status line beside it (user, 2026-09-21). No catch-without-balls row was
written during that grind; the words came from the walk before the shop.

Pinned: the flag is lowered at the start of every op, in the same place the
op's battle count is zeroed and before the op is sent; it is still raised
by a catch policy with no balls and still read by the grind's note; the
note still tells "after that the bag held none" from "none at all".
Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "planner/executor.py").read_text()
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


_rt = SRC[SRC.index("    def _run_traced("):]
_rt = _rt[:_rt.index("\n    def ", 10)]
_zero = _rt.index("self._op_battles = 0")
_lower = _rt.index("self._no_balls_note = False")
_read = _rt.index('if getattr(self, "_no_balls_note", False):')
ck("the flag is lowered where the op's battle count is zeroed",
   _zero < _lower < _zero + 900, (_zero, _lower))
ck("...once per op, before the grind's note reads it", _lower < _read)
ck("...and before the op is sent to the game",
   _lower < _rt.index("self._send_safe(", _lower))
ck("it is lowered exactly twice: at the op's start and when it is read",
   SRC.count("self._no_balls_note = False") == 2)
ck("a catch policy with no balls still raises it",
   'if name == "catch" and not _balls_in(obs):' in SRC
   and SRC.count("self._no_balls_note = True") == 1)
ck("...outside the op loop, in the battle handler",
   SRC.index("self._no_balls_note = True") < SRC.index("    def _run_traced("))
ck("the note still tells running out from never having any",
   "after that the bag held NO POKé BALLS" in SRC
   and "NO POKé BALLS of any kind in the bag, so " in SRC)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
