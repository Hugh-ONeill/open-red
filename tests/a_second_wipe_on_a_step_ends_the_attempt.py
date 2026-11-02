#!/usr/bin/env python3
"""A second wipe on the same step ends the plan attempt, outside the league too.

Run 71, 2026-11-02, Pewter Gym: each blackout set _plan_regress (enter_pewter_gym
undone on waking at the Center), run_plan replayed from there, and defeat_brock
restarted at round 1 with its wipe count back at one. The party lost to the
JR.TRAINER's DIGLETT L11 six times, ~16 s apart, earned nothing, and never
reached the rewrite where training is offered. Only the league had "a lap lost
past the first is a decision" (run 19). User: stop, fix, relaunch.

Pinned by source: outside the league a step's second wipe-regress logs
wipe_regress_decision and plan_failed_at and returns False; the first still
replays; and journal_text tells the rewrite why the plan ended.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ex = (ROOT / "planner/executor.py").read_text()
au = (ROOT / "planner/author.py").read_text()
i = ex.index("...AND SO IS A GYM'S, OR ANY STEP'S.")
blk = ex[i:i + 2600]
checks = [
    ("outside the league, counted per step",
     "if _rg is not None and not _in_league and _rg < idx:" in blk
     and '_wr[sg["id"]] = _wr.get(sg["id"], 0) + 1' in blk),
    ("the second ends the attempt", 'if _wr[sg["id"]] >= 2:' in blk
     and '"wipe_regress_decision"' in blk and '"plan_failed_at"' in blk
     and "return False" in blk),
    ("...before the replay, which the first wipe still gets",
     blk.index("return False") < blk.index("<- regressing to")),
    ("the rewrite is told why the plan ended",
     'k == "wipe_regress_decision"' in au and "blacked the " in au),
]
bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
sys.exit(1 if bad else 0)
