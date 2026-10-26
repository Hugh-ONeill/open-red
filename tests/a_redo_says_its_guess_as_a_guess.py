#!/usr/bin/env python3
"""The backtrack's REDO note offers "another part of this map" as a guess.

Run 66, 2026-10-25, leg 31: enter_gym failed on SAFFRONCITY_ROCKET3 standing
in the gym door ("Get out of the way!"); the backtrack re-opened
exit_silph_co (map SAFFRON_CITY) with a note that said the gym "turned out
to be impossible from here, which means this map has more than one area
that satisfies DONE_WHEN and you reached the wrong one". The run wrote "the
previous objective failed because I was at the wrong location within the
city" and walked out to Route 7.

Pinned: the note no longer states the inference as fact, still names the
blocked objective, and names the person-in-the-way reading beside it.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()

checks = []
def ck(n, ok): checks.append((n, bool(ok)))

i = src.index('"\\n\\nREDO: you ALREADY satisfy DONE_WHEN')
note = src[i:i + 900]
ck("the inference is not stated as fact",
   "which means this" not in note and "you reached the wrong one" not in note
   and "turned out to be impossible" not in note)
ck("the blocked objective is still named", "blocked_by" in note)
ck("another walked part is offered as a maybe", "may lead on" in note)
ck("...beside something on the way not passable yet", "not passable" in note)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
