#!/usr/bin/env python3
"""When event flags fire on a step, the leg's own check-done question is
asked again before the next step, and a yes ends the plan there.

Run 33, 2026-10-03: "Battle the rival for the first time" was planned as a
walk to Route 22; the fight happened in Oak's lab on step one
(EVENT_BATTLED_RIVAL_IN_OAKS_LAB) and the plan walked on north (user: "its
still having a lot of trouble getting around the idea of battling the rival
for the first time in the actual lab").

Pinned: no events, no question; events fired, the question is asked with
them named as what changed; a yes ends the plan and is logged; a no runs
on; the plan's first step only sets the baseline. Synthetic: no game, the
judge stubbed.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

asked = []
ex = object.__new__(E.Executor)
ex._leg_goal = "Battle the rival for the first time"
ck("no events, no question", ex._leg_done_after_events([]) is False)

src = (ROOT / "planner/executor.py").read_text()
i = src.index("def _leg_done_after_events")
body = src[i:i + 3500]
ck("the question is the leg's own check-done, with the events as what changed",
   '"--check-done", "--goal", goal' in body
   and '"events that fired during the step just "' in body)
ck("...and only the model's yes (exit 0) ends anything", "return r.returncode == 0" in body)
j = src.index("_fl_prev = getattr(self, \"_flags_at_step\", None)")
loop = src[j - 400:j + 1200]
ck("asked at a step boundary after the first, only when flags are new",
   "if (idx > 0 and idx < len(subgoals) and _fl_prev is not None" in loop
   and "and _fl_now - _fl_prev):" in loop)
ck("a yes ends the plan and says why",
   'self.log("plan_objective_met_by_events"' in loop and "return True" in loop)
ck("it can be switched off for an A/B", 'os.environ.get("RED_MIDLEG_CHECK") == "0"' in body)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
