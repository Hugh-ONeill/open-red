#!/usr/bin/env python3
"""A round that healed at a Center did not black out.

The escalation round decided "the party wiped while I ran" by looking for
the WORD in its own trace: `any("blackout" in t for t in trace)`. On
2026-09-06 the nurse's feedback gained the sentence "this is now where you
wake after a blackout", and from then on every round with a heal in it was
a wipe. Run 28 never blacked out once. Its journal holds 0 "blackout" rows
and 40 "blackout_round" rows, every one of them set off by that sentence,
and 94 pages told the model THIS STEP HAS BLACKED OUT, up to six times on
one step, half its money gone, with "WHAT BEAT YOU: RATTATA L10" under it
(2026-09-21). The first such round of each step was also pardoned.

Every detector of a real wipe writes a "blackout" row to the journal, so
log() counts them and the round compares the count against what it was
when the round began. What the trace SAYS no longer decides anything.

Pinned: a heal row does not move the count and a blackout row does; the
round snapshots the count before it runs anything and reads the difference;
no test on the trace's words is left; the nurse's sentence still carries
the word (which is why the old test could not stand); the real wipe keeps
its own wording; the page line and the journal row are still written.
Synthetic."""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ex = E.Executor.__new__(E.Executor)
ex.logf = io.StringIO()
ex.t0 = time.time()

ex.log("heal_done", ok=True, where="CERULEAN_POKECENTER")
ck("a heal at a Center is not a wipe", getattr(ex, "_wipes_logged", 0) == 0)
ex.log("escalate_feedback", trace=[
    "heal(): ok (moved, the nurse healed the party — the whole party is at "
    "full HP; this is now where you wake after a blackout)"])
ck("...whatever the nurse's feedback says",
   getattr(ex, "_wipes_logged", 0) == 0)
ex.log("blackout_return", to="ROUTE_4|63,10")
ex.log("blackout_round", n=1)
ck("...and rows ABOUT a wipe are not one either",
   getattr(ex, "_wipes_logged", 0) == 0)

ex.log("blackout", subgoal="s", op="explore", respawn="PALLET_TOWN")
ck("a blackout row is a wipe", ex._wipes_logged == 1)
ex.log("blackout", subgoal="s", op="cross", respawn="VIRIDIAN_POKECENTER",
       detected="state")
ck("...each one of them, whichever detector wrote it", ex._wipes_logged == 2)
ck("the rows were still written to the journal",
   ex.logf.getvalue().count('"kind": "blackout"') == 2)

SRC = (ROOT / "planner/executor.py").read_text()
ck("the round reads the count, not the trace's words",
   'had_blackout = getattr(self, "_wipes_logged", 0) > _wipes_at_start' in SRC)
_code = [l for l in SRC.splitlines() if not l.lstrip().startswith("#")]
ck("...and no line of code tests the trace for the word",
   not any('"blackout" in t' in l for l in _code)
   and sum("had_blackout = " in l for l in _code) == 1)
ck("the count is taken as the round begins, before anything runs",
   SRC.index("rnd += 1\n            _wipes_at_start = ")
   < SRC.index("start = self.settle()\n            self._note_map(start)"))
_esc = SRC[SRC.index("    def escalate("):]
ck("...inside the loop that charges the round",
   _esc.index("while spent < rounds") < _esc.index("_wipes_at_start = ")
   < _esc.index("had_blackout = "))
ck("every detector writes the row the count reads",
   SRC.count('self.log("blackout", subgoal=') >= 3)

LUA = (ROOT / "harness/shim.lua").read_text()
ck("the nurse's sentence still carries the word, so the words cannot decide",
   "this is now where you wake " in LUA and "after a blackout" in LUA)
ck("a real wipe keeps its own words in the trace",
   "your party FAINTED mid-op (blackout)" in SRC)
ck("the page line and the journal row are still written",
   "THIS STEP HAS BLACKED OUT" in SRC and 'self.log("blackout_round"' in SRC)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
