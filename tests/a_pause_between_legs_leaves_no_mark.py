#!/usr/bin/env python3
"""The chain can be paused where nothing is in flight, so a resume is
indistinguishable from never having stopped.

stop_all.sh asks the executor to stop and save, and the world is safe
either way: the game is written at every round boundary. What it cannot do
is stop between ATTEMPTS. Pausing run 31 on the night of 2026-09-21 cut an
attempt of leg 16 partway, and the relaunch threw its plan away — "leg
16/42: plans/leg_16_reach_celadon_city.v1.json was written from
POKEMON_FAN_CLUB (the run stands on ROUTE_11) — asking for it again from
here" — and authored a v2. Nothing was lost and the run was not helped;
what it leaves is a visible discontinuity in a run whose whole worth is
that nobody touched it (user, 2026-09-22: "id rather it didnt do that? id
prefer it had clean pauses/resumes so we can claim no interference,
otherwise well have to run it and wait for it straight through however many
days").

Between legs there is nothing in flight: the last leg is banked in
run/outline_leg, the next has not been chosen, no plan has been read and no
attempt has begun. A pause there is the moment before the leg would have
started either way.

Pinned: the check is at the top of the leg loop, before the outline is read
and before the next leg is chosen; the file is removed as it fires, so a
pause is once and a relaunch is not caught by its own sentinel; it exits 0,
because a pause is not a failure and the campaign loop must not treat it as
one; it says how many legs are done; and the progress mark is untouched, so
the relaunch resumes exactly where it stood. Synthetic."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SH = (ROOT / "fresh_discovery.sh").read_text()
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ck("a sentinel file pauses the chain", 'if [ -e run/pause ]; then' in SH)
ck("...and is removed as it fires, so one touch is one pause",
   re.search(r"if \[ -e run/pause \]; then\n\s*rm -f run/pause\n", SH) is not None)
ck("...and the chain leaves by the front door, not as a failure",
   re.search(r"=== PAUSED at a leg boundary.*\n\s*exit 0\n", SH) is not None)
ck("the pause says how much was done and that nothing was in flight",
   "leg(s) done, nothing in flight" in SH)

_loop = SH[SH.index("\nwhile :; do"):]
_pause = _loop.index("if [ -e run/pause ]; then")
ck("it is checked inside the leg loop, so every leg boundary is a chance",
   _pause > 0)
ck("...before the outline is read",
   _pause < _loop.index("mapfile -t LEGS < plans/outline.txt"))
ck("...and before the next leg is chosen",
   _pause < _loop.index("i=$((done_legs + 1))"))
# the comment above the check quotes the line that set this off, so the
# anchor has to be the CODE that prints it, not the words
ck("...and before any plan is looked at",
   _pause < _loop.index('$plan was written from $_from'))

ck("the progress mark is not touched by the pause",
   'rm -f run/pause\n' in SH
   and not re.search(r"rm -f run/pause\n(?:.*\n){0,3}.*\$PROGRESS\"?\s*$",
                     SH, re.M))
ck("the reason is written where the check is",
   "A PAUSE BETWEEN LEGS LEAVES NO MARK" in SH
   and "POKEMON_FAN_CLUB" in SH)

# ---- the sequence, as a pause and a resume run it -----------------------
def loop(pause_before_leg, legs=4, sentinel=False):
    """Returns the legs run, and whether it exited at a boundary."""
    done, ran, paused = 0, [], False
    for _ in range(legs * 2):
        if sentinel and done == pause_before_leg:
            sentinel = False          # rm -f run/pause
            paused = True
            break
        if done >= legs:
            break
        done += 1
        ran.append(done)
    return ran, paused, done


first, paused, mark = loop(2, sentinel=True)
ck("a pause stops before the next leg, with the mark where it was",
   first == [1, 2] and paused and mark == 2, (first, mark))
rest, paused2, mark2 = loop(2, sentinel=False)
ck("...and the relaunch is not caught by the pause it already served",
   not paused2)
ck("the two halves together are the same legs, in the same order, once each",
   first + [l for l in rest if l > mark] == [1, 2, 3, 4])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
