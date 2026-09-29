#!/usr/bin/env python3
"""What the rival says after a fight is heard, under his name (run 18,
2026-09-28).

A trainer met on the way leaves the battle's own lines and then its speech
in one run of boxes, and one noisy box ("gained 240 EXP. Points") used to
drop the lot: the rival's "I went to BILL's ... go thank him!" after the
Cerulean fight, the game's one pointer to the ticket, never reached a page
(user: "does the model even pay attention to what the rival says because its
usually actually important"). And a scene's lines were filed under whoever
was pressed first: the rival's Town Map line in Oak's lab went under
OAKSLAB_OAK1. Plus the sweep's low-HP stop, staged with it.

Synthetic, plus source checks.
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


run = ("Enemy PIDGEOTTO fainted! / IVYSAUR gained 240 EXP. Points! / IVYSAUR grew to level 20! / "
       "JERK: Hey, guess what? I went to BILL's and got him to show me his rare POKeMON! / "
       "After all, BILL's world famous as a POKeMANIAC! / Since you're using his system, go thank him!")
main, first, extra = E.split_heard(run)
ck("the battle's own lines are dropped, box by box",
   "EXP" not in main and "grew to level" not in main and "fainted" not in main, main)
ck("...and the rival's speech is kept whole, under his printed name",
   first == "JERK" and "I went to BILL's" in main and "go thank him" in main, (main, first))
main2, first2, extra2 = E.split_heard(
    "JERK: Hey, guess what? I went to BILL's! / Since you're using his system, go thank him!")
ck("a speech that opens with a printed name is that speaker's", first2 == "JERK", first2)
lab = ("OAK: Oh, SAGE! How is my old POKeMON? / JERK: I'll borrow a TOWN MAP from my sis! "
       "I'll tell her not to lend you one, SAGE! Hahaha!")
main3, first3, extra3 = E.split_heard(lab)
ck("a scene is split by printed speaker: Oak's line is Oak's",
   first3 == "OAK" and "TOWN MAP" not in main3, main3)
ck("...and the rival's is filed under JERK", extra3 and extra3[0][0] == "JERK"
   and "TOWN MAP" in extra3[0][1], extra3)
ck("nothing but noise is nothing", E.split_heard("SAGE saved the game. / IVYSAUR gained 12 EXP. Points!")[0] == "")
ck("an ordinary line is untouched",
   E.split_heard("I'm on guard duty. Gee, I'm thirsty, though! / Oh wait there, the road's closed.")
   == ("I'm on guard duty. Gee, I'm thirsty, though! / Oh wait there, the road's closed.", None, []))

sh = (ROOT / "harness/shim.lua").read_text()
ck("a sweep stops when one Pokemon is left standing or a third of the HP remains",
   "((_n > 1 and _up <= 1) or _hp * 3 < _mx)" in sh
   and "stopped: your party is nearly out" in sh)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
