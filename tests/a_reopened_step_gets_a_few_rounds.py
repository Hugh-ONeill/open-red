#!/usr/bin/env python3
"""A step re-opened by a backtrack gets a few rounds, not a full budget.

Runs 68-69 (measured 2026-11-01 over the executor logs): 65 re-opens (a
backtrack to an earlier step whose condition had stopped holding), 5 of them
let the failed step through, each inside 5 rounds. The 40 re-opens that never
got back to their own condition spent 259 rounds (free rounds and flag-step
budgets included), and the failed step was not even retried after them.

Pinned: the backtrack's first pass passes reopen when it is not a relocate;
the escalation stops at REOPEN_ROUNDS on a round boundary and says so; a
relocate (redo) is not capped; the cap is the measured 5.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
src = (ROOT / "planner" / "executor.py").read_text()
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ck("the cap is the measured five", E.Executor.REOPEN_ROUNDS == 5)
ck("escalate takes reopen", "reopen: bool = False) -> tuple[bool, list]:" in src)
i = src.index("if reopen and rnd >= self.REOPEN_ROUNDS:")
loop = src.rindex("while spent < rounds and rnd <", 0, i)
ck("the check sits inside the round loop, before the round is counted",
   loop < i < src.index("rnd += 1", i))
ck("...and says so when it stops", '"reopen_budget_spent"' in src[i:i + 300])
j = src.index('self.log("backtrack", failed=sg["id"], redoing=prev["id"],')
ck("the backtrack's first pass re-opens only what it does not relocate",
   "reopen=not _redo)" in src[j:j + 900])
k = src.index("moved2, _ = self.escalate(")
ck("the second pass, run only after a relocate, is not capped",
   "reopen" not in src[k:k + 500])

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
sys.exit(1 if bad else 0)
