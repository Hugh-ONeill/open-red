#!/usr/bin/env python3
"""A step's earlier failures shorten its budget only under the same plan.

The rap sheet that gives a repeat offender fewer escalation rounds was
keyed by the step's id alone, and a rewritten plan keeps its ids: every
failure of "the Mt. Moon entrance is on Route 2" was charged to the rewrite
that finally went east, and each of its attempts got the three-round floor
(run 27, 2026-09-16, user: "the rounds seem suspiciously short"). Pinned:
failures count under the plan file that was running when they happened; a
repeat of that file still earns the shorter leash; journal rows from before
plan_start named its plan count for nobody.

Synthetic: a journal on disk, no game, no model.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import executor as E          # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


live = E.RUN
tmp = Path(tempfile.mkdtemp(prefix="rap_sheet_"))
E.bind_run(tmp)
rows = [
    {"kind": "subgoal_failed", "subgoal": "enter_mt_moon"},        # old row
    {"kind": "plan_start", "plan": "leg_07_traverse_mt_moon.json"},
    {"kind": "subgoal_failed", "subgoal": "enter_mt_moon"},
    {"kind": "subgoal_failed", "subgoal": "enter_mt_moon"},
    {"kind": "plan_start", "plan": "leg_07_traverse_mt_moon.v1.json"},
    {"kind": "subgoal_failed", "subgoal": "enter_mt_moon"},
    {"kind": "plan_start", "plan": "leg_07_traverse_mt_moon.json"},
    {"kind": "plan_failed_at", "subgoal": "enter_mt_moon"},
]
(tmp / "executor_log.jsonl").write_text(
    "\n".join(json.dumps(r) for r in rows) + "\n")


def fails_for(plan_file):
    ex = E.Executor(None, plan={"goal": "x", "subgoals": []},
                    plan_path=plan_file)
    try:
        ex.logf.close()
    except Exception:
        pass
    return ex._prior_subgoal_fails.get("enter_mt_moon", 0)


ck("the same plan file keeps its own failures (both runs of it)",
   fails_for("plans/leg_07_traverse_mt_moon.json") == 3)
ck("a rewrite counts only what failed under the rewrite",
   fails_for("plans/leg_07_traverse_mt_moon.v1.json") == 1)
ck("a brand-new rewrite starts clean",
   fails_for("plans/leg_07_traverse_mt_moon.v2.json") == 0)
ck("no plan file, no record", fails_for(None) == 0)
src = (ROOT / "planner/executor.py").read_text()
ck("plan_start names the plan file",
   'self.log("plan_start", goal=plan.get("goal")' in src
   and "plan=(Path(str(self.plan_path)).name" in src)

E.bind_run(live)
failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
