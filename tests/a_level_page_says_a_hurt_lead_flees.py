#!/usr/bin/env python3
"""A level step's page says wilds are fought only while the lead is at the
policy's flee threshold or above, and says so of the lead now.

Run 27, 2026-09-18: the page said "a wild met here: it is FOUGHT, because
this step is judged on levels" and "every wild battle is experience" while
the pinned policy flees any wild with the lead under 30% HP; the level-50
leg fled 150 training battles on turn one (user: "maybe we can just tighten
up the wording a bit to let the bot see that better").

Pinned: the words carry the threshold from the active spec; a hurt lead is
named with its HP and "a wild met now is fled"; a healthy lead gets no such
clause; no threshold in the spec, no words. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


E.ACTIVE_SPEC = {"flee_wild": {"when_traversal": True, "hp_below": 0.3}}
ex = object.__new__(E.Executor)
hurt = {"party": [{"species": "MACHOP", "hp": 10, "max_hp": 74}]}
well = {"party": [{"species": "MACHOP", "hp": 70, "max_hp": 74}]}
w = ex._flee_hp_words(hurt)
ck("the threshold comes from the spec", "under that, your own battle policy FLEES it" in w and "30% HP" in w, w)
ck("...a hurt lead is named with its HP", "your lead MACHOP is at 13% now, so a wild met now is fled" in w, w)
ck("...a healthy lead gets no such clause", "now is fled" not in ex._flee_hp_words(well))
ck("...the short form for the how-to line",
   ex._flee_hp_words(well, short=True).startswith(" (your own battle policy FLEES a wild while the lead is under 30% HP"))
E.ACTIVE_SPEC = {"flee_wild": {"when_traversal": True}}
ck("no threshold in the spec, no words", ex._flee_hp_words(hurt) == "")
src = (ROOT / "planner/executor.py").read_text()
ck("the level step's fought line carries it",
   '"it is FOUGHT, because this step is judged on levels"\n                        + self._flee_hp_words(obs))' in src)
ck("...and so does the how-to line", '"wild battle FOUGHT is experience for whoever you send out"' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
