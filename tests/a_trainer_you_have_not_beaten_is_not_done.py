"""A trainer standing in your way is not finished because you pressed him.

The ledger's rule was "a pressed trainer is finished business", written for
Route 16's bikers — every one of whom had been BEATEN. Press a trainer and
lose the thread of the fight and he is marked pressed all the same.

The Rocket at (9,5) in the Game Corner stands in front of the poster, and
the switch behind that poster is the only way into the Rocket Hideout. Run
17 pressed him once, the op did not finish cleanly, and he was filed at
item 24 as pressed. The page then read "Everything you can REACH here is
done (POSTER ... sits where no walk from here goes)" — true, because the
Rocket's own body is what no walk gets past — and the run spent its rounds
pressing slot machines one by one looking for another way down
(2026-09-15, user: "it has not interacted with the poster yet, the rocket
is still in front of it").

The game keeps the answer in the save and any player knows it: a trainer
you have beaten does not fight you again. The shim publishes it and the
ledger reads it. What stays the model's: whether to fight him.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import ledger as L                                         # noqa: E402

checks = []
def ck(name, cond): checks.append((name, bool(cond)))

SHIM = (ROOT / "harness" / "shim.lua").read_text()
LED = (ROOT / "planner" / "ledger.py").read_text()
EXE = (ROOT / "planner" / "executor.py").read_text()

# ---- the shim says whether a trainer has been beaten -------------------
ck("a trainer object carries whether you have beaten it",
   "beaten = beaten," in SHIM)
ck("...read from the save's own record of defeated trainers",
   "G.save.defeatedTrainers" in SHIM and '"%s_obj_%d"' in SHIM)
ck("...and only for trainers, so nothing else gains a verdict",
   'if kind == "trainer" then' in SHIM
   and SHIM.index('local beaten = nil') < SHIM.index('beaten = beaten,'))

# ---- and the ledger treats one you have not beaten as unfinished ------
ck("an unbeaten trainer ranks with the things never touched",
   L.STATUS_RANK["unbeaten"] == 0
   and L.STATUS_RANK["unbeaten"] == L.STATUS_RANK["unspoken"])
ck("...and counts as unworked, so the area is not called fully worked",
   "unbeaten" in L.UNWORKED)
ck("...and is offered to press, beside the things never pressed",
   '"untouched", "unspoken", "unbeaten"' in LED
   and EXE.count('"unbeaten", "cuttable")') == 2)
ck("...with words that say what is true and no more",
   "still standing here" in L._STATUS_WORDS["unbeaten"]
   and "you have not beaten them" in L._STATUS_WORDS["unbeaten"])
ck("...and the words point at nothing: no instruction to fight",
   not any(w in L._STATUS_WORDS["unbeaten"].lower()
           for w in ("fight ", "you must", "you should", "beat them")))

# ---- the verdict only overrides a press, never a fresh sighting -------
ck("the rule is applied after a status was set, not instead of one",
   LED.index('c.status = "unspoken" if kind in ("npc", "trainer")')
   < LED.index('c.status = "unbeaten"'))
ck("a trainer already beaten keeps whatever the press made of him",
   'o.get("beaten") is False' in LED)
ck("...so an observation that says nothing leaves the status alone",
   'is False' in LED and 'if not o.get("beaten")' not in LED)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad
      else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)
