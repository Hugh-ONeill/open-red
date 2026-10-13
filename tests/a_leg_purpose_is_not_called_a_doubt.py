#!/usr/bin/env python3
"""A leg's purpose is not called a doubt (run 18, 2026-09-28).

plans/outline.notes holds real doubts and, mostly, an upkeep leg's purpose
("for: Reach Mt. Moon"); the chain labelled every one "a doubt you recorded
when outlining", so a training leg read as doubted (user: "what does this
mean? ... the doubt stuff?"). A "for:" note now reads "(you added this when
outlining, for: ...)", and every stripper takes both forms.

Source checks plus the strippers.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import upkeep_ask as U  # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


sh = (ROOT / "fresh_discovery.sh").read_text()
# ...and since run 54 (2026-10-12) a purpose is not shown at all: it steered
# the plans toward the leg it was written for. upkeep_ask still reads it
# from plans/outline.notes.
ck("a for: note is not put in the goal string",
   'for:*) : ;;' in sh and "(you added this when outlining, $note)" not in sh)
import or_leg  # noqa: E402
ck("...the party-leg check reads the purpose from the notes file, not the goal",
   "or_leg.purpose(leg)" in (ROOT / "planner" / "upkeep_ask.py").read_text()
   and 'NOTES = Path("plans/outline.notes")' in (ROOT / "planner" / "or_leg.py").read_text())
ck("...and anything else is still a doubt",
   '*)     [ -n "$note" ] && goal="$leg (a doubt you recorded when outlining: $note)"' in sh)
p = "every party member is at least level 12 (you added this when outlining, for: Reach Mt. Moon)"
ck("the author strips the purpose form", A._DOUBT_NOTE.sub("", p) == "every party member is at least level 12")
ck("upkeep_ask strips it too", U._NOTE.sub("", p) == "every party member is at least level 12")
ck("the doubt form still strips", A._DOUBT_NOTE.sub("", "Help Bill (a doubt you recorded when outlining: x)") == "Help Bill")

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
