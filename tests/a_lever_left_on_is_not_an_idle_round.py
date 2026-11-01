#!/usr/bin/env python3
"""A round that leaves ON a lever it found OFF is neither idle nor progress.

Run 69, Vermilion Gym (2026-10-30): EVENT_1ST_LOCK_OPENED had been seen reset
once, so it was a lever and _progress_mark left it out. Round 10 opened the
first lock (the macro stopped there, next251), round 11 pressed a wrong can
and reset the locks, and step_idle_end fell on round 12 with a streak of six.
The same happened twice more, the plan failed three times, leg 18 was passed
over with no rung able to move it, and the Thunder Badge came 26 hours later
on a leg inserted before the Viridian Gym.

Counting the open as progress would bring back next291's bug (the Mansion's
statue flipped every round and the streak never closed). So such a round is
not counted either way: the streak neither grows nor resets on it.

Pinned on the helper, with the Mansion's lever and the gym's lock; and the
loop uses the helper."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


def fresh():
    ex = E.Executor.__new__(E.Executor)
    ex._toggled_flags = ["EVENT_1ST_LOCK_OPENED"]
    ex._idle_streak = 0
    ex._round_levers_on = set()
    return ex


shut = {"flags": ["EVENT_X"]}
open_ = {"flags": ["EVENT_X", "EVENT_1ST_LOCK_OPENED"]}

ex = fresh()
for _ in range(5):
    ex._count_idle_round(shut, True)
ck("five rounds that changed nothing count five", ex._idle_streak == 5)
ex._count_idle_round(open_, True)
ck("a round that opened the lock does not count (run 69 round 10)",
   ex._idle_streak == 5, ex._idle_streak)
ex._count_idle_round(shut, True)
ck("...the reset after it does", ex._idle_streak == 6)
ex._count_idle_round(open_, False)
ck("a round with news resets the streak whatever the lever did", ex._idle_streak == 0)
ex._count_idle_round(open_, True)
ck("a round that found the lever ON and left it ON is idle", ex._idle_streak == 1)

# the Mansion: flipped every round, the step still ends, at twice the count
ex = fresh()
ex._toggled_flags = ["EVENT_MANSION_SWITCH_ON"]
on = {"flags": ["EVENT_MANSION_SWITCH_ON"]}
off = {"flags": []}
n = 0
for i in range(12):
    ex._count_idle_round(on if i % 2 == 0 else off, True)
    n += 1
    if ex._idle_streak >= E.Executor.IDLE_STREAK_END:
        break
ck("a lever flipped back and forth still ends the step", ex._idle_streak >= E.Executor.IDLE_STREAK_END, ex._idle_streak)
ck("...at twice the count", n == 2 * E.Executor.IDLE_STREAK_END, n)

src = (ROOT / "planner/executor.py").read_text()
ck("the escalation loop counts through the helper",
   "self._count_idle_round(start, _same_world and _seen_map" in src
   and "self._idle_streak = int(getattr(self, \"_idle_streak\", 0)) + 1\n                else:" not in src)
ck("...and a new step starts from the levers it finds on",
   "self._round_levers_on = self._levers_on(start)" in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
