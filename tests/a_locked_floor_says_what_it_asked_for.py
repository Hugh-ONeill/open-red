#!/usr/bin/env python3
"""A floor whose shut way asked for a thing the bag lacks says so wherever
that floor's leftovers are listed.

Run 27, 2026-09-17, Silph Co: from 11F the page listed 3F, 4F and 10F under
"ground you have stood on that still holds something no walk reached" and
"ways you have never taken", while each floor's shutter had said "Darn! It
needs a CARD KEY!" three lines away under WHAT YOU WERE TOLD, unconnected.
With no CARD KEY in the bag the run toured those floors for their balls,
over and over (user: "it seems to recognize when there are
untried/unpressed/unseen things on the different floors but not remember
that they are behind locked doors").

Pinned: the lock's own words and the missing item ride the far-rooms line,
the never-taken rows and the unfinished-floors rows for that floor; a held
key is the other helper's case and says nothing here; a floor with no such
words says nothing. Nothing names what lies behind which door. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ex = object.__new__(E.Executor)
ex.hints = {
    "SILPH_CO_4F|20,0": ["sweep: Intruder spotted!",
                         "DOOR_SILPH_CO_4F_12_8: Darn! It needs a CARD KEY!"],
    "SILPH_CO_4F|10,2": ["SILPHCO4F_SCIENTIST: The doors are electronically locked!"],
    "SILPH_CO_8F|14,0": ["SILPHCO8F_ROCKET1: If you don't turn back, I'll call for backup!"],
}
NOKEY = {"bag": {"POKE_BALL": 5}}
KEY = {"bag": {"POKE_BALL": 5, "CARD_KEY": 1}}

got = ex._lock_asked_unheld("SILPH_CO_4F|10,2", NOKEY)
ck("a floor's shut way that asked for a thing the bag lacks is said, from any part of it",
   got == ' — a shut way on that floor said: "Darn! It needs a CARD KEY!", and your bag holds no CARD_KEY', got)
ck("...by map name too", ex._lock_asked_unheld("SILPH_CO_4F", NOKEY) == got)
ck("a key in the bag is the other helper's case", ex._lock_asked_unheld("SILPH_CO_4F|20,0", KEY) == "")
ck("a floor with no such words says nothing", ex._lock_asked_unheld("SILPH_CO_8F|14,0", NOKEY) == "")
ck("no bag on the page, no claim", ex._lock_asked_unheld("SILPH_CO_4F|20,0", {}) == "")

src = (ROOT / "planner/executor.py").read_text()
ck("it rides the far-rooms line",
   'f" — {len(_p)} leg(s) away)"\n                                        + self._lock_asked_unheld(_r, obs)))' in src)
ck("...and both never-taken rows", src.count("+ self._lock_asked_unheld(region, obs)))") == 2)
ck("...and the unfinished-floors row", "+ self._lock_asked_unheld(_m, obs))" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:220]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
