#!/usr/bin/env python3
"""A step ending on an unfired flag is shown the fired flags that share its
distinctive word, with where each fired.

Run 66, 2026-10-25: leg 31 v4's defeat_giovanni ended on EVENT_BEAT_GIOVANNI
(this port's Viridian Gym fight) and walked the run down the Rocket Hideout to
B4F, where EVENT_BEAT_ROCKET_HIDEOUT_GIOVANNI had fired hours before. Nothing
on the page said so.

Pinned: the kin are listed with their sites; generic words (BEAT, EVENT, GOT,
floors) make no kin; a fired target, or a step on no flag, says nothing; the
note never says which kin is meant.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = E.Executor.__new__(E.Executor)
ex.flag_sites = {"EVENT_BEAT_ROCKET_HIDEOUT_GIOVANNI": "ROCKET_HIDEOUT_B4F|17,1"}
OBS = {"flags": ["EVENT_BEAT_ROCKET_HIDEOUT_GIOVANNI", "EVENT_BEAT_SILPH_CO_RIVAL",
                 "EVENT_GOT_HM01", "EVENT_BEAT_BROCK"]}
t = ex._kin_flag_note({"done_when": {"flag": "EVENT_BEAT_GIOVANNI"}}, OBS)
ck("the hideout's Giovanni is shown beside the step's flag, with its site",
   "EVENT_BEAT_ROCKET_HIDEOUT_GIOVANNI (fired in ROCKET_HIDEOUT_B4F|17,1)" in t, t)
ck("...and nothing that shares only BEAT", "BROCK" not in t and "SILPH_CO_RIVAL" not in t, t)
ck("...and it names no answer", "yours to judge" in t, t)
ck("a fired target says nothing",
   ex._kin_flag_note({"done_when": {"flag": "EVENT_BEAT_BROCK"}}, OBS) == "")
ck("a step on no flag says nothing",
   ex._kin_flag_note({"done_when": {"map": "SAFFRON_GYM"}}, OBS) == "")
ck("a flag of only generic words says nothing",
   ex._kin_flag_note({"done_when": {"flag": "EVENT_GOT"}}, OBS) == "")
src = (ROOT / "planner/executor.py").read_text()
ck("the escalation page carries it", "memory += self._kin_flag_note(sg, start)" in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
