#!/usr/bin/env python3
"""What a can said before the game announced a reset is not on its row,
the cans are laid out as the room draws them, and a reset frees the
presses it undid.

Run of record 3 lost Lt. Surge's gym (2026-09-25): 257 presses, the 1st
lock found 11 times, and the page's rows counted every press since the
run walked in — "TRASH_CAN_12 ... pressed 54x ... 'The 1st electric lock
opened!' (3x)" — which the model read as a trait: it opened each cycle on
12, 14 or 0 whatever the room had said since. In its last cycle it
pressed 12 ten times, each "Nope". Twenty-three presses were also refused
as "same ops, same world": the world mark counts flags, and a reset puts
the lock flags back where they were (user: "yeah do those too").

Pinned: once the press log holds an answer saying something "were
reset", each fixture row counts only presses since it, with that line
quoted, and every older answer and count is off the row; the ordered
list starts at the reset; six or more fixtures of one kind get one line
laying them out by row, starred when pressed since the reset; a room with
no reset keeps the old rows; the repeat key carries the count of resets
the run has been told of, bumped from the round's own trace. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
sys.path.insert(0, str(ROOT / "tests"))
import ledger as L          # noqa: E402
import untried as U         # noqa: E402
import candidates as C      # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


RESET = "Nope! There's only trash here. Hey! The electric locks were reset!"
NOPE = "Nope, there's only trash here."
OPEN1 = "Hey! There's a switch under the trash! Turn it on! The 1st electric lock opened!"
# the gym's own layout, as the run's page gave it: TRASH_CAN_n at
# x = 1 + 2*(n // 3), y = 7 + 2*(n % 3)
CANS = [(f"TRASH_CAN_{i}", 1 + 2 * (i // 3), 7 + 2 * (i % 3)) for i in range(15)]


def page(log):
    ex = C.make(frontier={U.HERE: ["1,1"]})
    o = C.obs(ex, ["1,1"])
    o["map"]["connections"] = {}
    cands = L.build(ex, o, target="badge:THUNDERBADGE")
    for name, x, y in CANS:
        cands.append(L.Candidate(key=name, kind="fixture", status="touched",
                                 n=sum(1 for k, _ in log if k == name),
                                 note="it said: \"%s\"" % OPEN1 if name == "TRASH_CAN_12" else "",
                                 x=x, y=y))
    ex._press_log = {U.HERE: [list(e) for e in log]}
    ex._outcomes = {}
    return L.render(cands, ex, o, target="badge:THUNDERBADGE")


LOG = ([("TRASH_CAN_12", OPEN1), ("TRASH_CAN_14", RESET)]
       + [("TRASH_CAN_12", NOPE)] * 3 + [("TRASH_CAN_0", NOPE)])
pg = page(LOG)
row12 = next((l for l in pg.splitlines() if "TRASH_CAN_12 (" in l), "")
ck("a row counts only presses since the last reset, with the line quoted",
   'pressed 3x since the game last said "%s"' % RESET in row12
   and '"%s" (3x)' % NOPE in row12, row12)
ck("...and nothing older is on it: not the opening, not the all-time count",
   "1st electric lock opened" not in row12 and "pressed 4x" not in row12, row12)
row5 = next((l for l in pg.splitlines() if "TRASH_CAN_5 (" in l), "")
ck("a can not pressed since reads so", "not pressed since the game last said" in row5, row5)
ol = next((l for l in pg.splitlines() if "WHAT PRESSING THINGS HERE HAS SAID" in l), "")
ck("the ordered list starts at the reset",
   ol.startswith('SINCE THE GAME LAST SAID "%s"' % RESET)
   and "TRASH_CAN_14: \"%s\"" % RESET in ol and OPEN1 not in ol, ol[:300])
gl = next((l for l in pg.splitlines() if l.startswith("WHERE THE 15 TRASH_CANS STAND")), "")
ck("the cans are laid out by row as the room draws them, starred since the reset",
   "y=7: TRASH_CAN_0 x=1*, TRASH_CAN_3 x=3, TRASH_CAN_6 x=5, TRASH_CAN_9 x=7, TRASH_CAN_12 x=9*" in gl
   and " | y=9: " in gl and " | y=11: " in gl, gl[:400])
ck("...and the grid says nothing about what is under which",
   "switch" not in gl.lower().replace("pressed since", ""), gl)
pg0 = page([("TRASH_CAN_12", NOPE), ("TRASH_CAN_0", NOPE), ("TRASH_CAN_3", NOPE)])
ck("a room with no reset keeps its old rows",
   "since the game last said" not in pg0
   and "WHERE THE 15 TRASH_CANS STAND" in pg0 and "*" not in
   next((l for l in pg0.splitlines() if l.startswith("WHERE THE 15")), ""), pg0[-600:])

ex_src = (ROOT / "planner/executor.py").read_text()
ck("the repeat key carries the resets the run has been told of",
   'int(getattr(self, "_resets_heard", 0) or 0))' in ex_src
   and '+ sum(str(t).lower().count("were reset") for t in trace)' in ex_src
   and "and k[2:] == _mac_key[2:]})" in ex_src)
ck("...counted after the round's key was taken",
   ex_src.index("_mac_key = (self._where(obs)")
   < ex_src.index('+ sum(str(t).lower().count("were reset") for t in trace)'))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
