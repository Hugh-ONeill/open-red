#!/usr/bin/env python3
"""A trainer who walked up and fought during an op is named as who spoke.

A sweep of the Pewter gym met a JR.TRAINER, and the line "Stop right there,
kid! You're still light years from facing BROCK!" came back as `it said:`
right after "came into view: PEWTERGYM_BROCK". The model read it as Brock
setting a condition (run 44, 2026-10-10). Probed on the real game from the
run's leg-5 save teleported into the gym: the same sweep now ends
' — JR.TRAINER♂ fought you on the way, and it said: "Stop right there ...'.

Pinned: the fight recorded during this op names the speaker, only when the
op pressed nobody and no one stopped the walk, never the "a trainer"
fallback; the note keeps the "it said: " the readers split on. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "planner/executor.py").read_text()
checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


rt = SRC[SRC.index("    def _run_traced("):]
rt = rt[:rt.index("\n    def ", 10)]
ck("the fight held before the op is kept", '_fight0 = getattr(self, "_last_fight", None)' in rt)
ck("...right where the op's before-view is",
   rt.index("pre_obs = obs\n") < rt.index("_fight0 =") < rt.index("pre_obs = obs\n") + 80)
ck("a fight recorded during the op names who spoke",
   "_lf is not _fight0" in rt and 'who = _by_fight = str(_lf["who"])' in rt)
ck("...not when the op pressed someone, or someone stopped the walk",
   "if (not step.get(\"name\") and not _stopped and _lf" in rt)
ck("...and never the unnamed fallback", '_lf.get("who") not in (None, "", "a trainer")' in rt)
ck("the note names them and keeps the words the readers split on",
   "f' — {_by_fight} fought you on the way, and it said: \"'" in rt
   and "' — it said: \"'" in rt)
ck("the marker starts empty each op", rt.count("_by_fight = None") == 1)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"{len(checks) - len(bad)}/{len(checks)} passed")
sys.exit(1 if bad else 0)
