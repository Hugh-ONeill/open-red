#!/usr/bin/env python3
"""The backtrack scan passes a step the harness ruled out in this plan.

Run 62, 2026-10-24: leg 45's rewrites put "explore the island" before
enter_cinnabar_gym; the pre-check ruled it out ("every bit of CINNABAR_ISLAND
a walk reaches has been on screen"), and each failed enter_cinnabar_gym
re-opened it, walked the party out of the Mansion, and had it ruled out
again (user: "backtrack should skip the ruled out steps").

Pinned: every ruled-out log site records the id; run_plan resets the set;
the scan passes a recorded id and goes on to an earlier step.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

src = (ROOT / "planner" / "executor.py").read_text()
ck("every ruled-out log site records the id",
   src.count('getattr(self, "_ruled_out_ids", set()).add(sg["id"])') == 3
   and src.count('self.log("subgoal_ruled_out"') == 3)
i = src.index("    def run_plan(self, plan: dict) -> bool:")
ck("run_plan starts the plan with none", "self._ruled_out_ids = set()" in src[i:i + 200])
j = src.index("for back in range(idx - 1, max(-1, idx - 5), -1):")
blk = src[j:j + 1200]
ck("the scan passes a ruled-out step and goes on",
   'if c.get("id") in getattr(self, "_ruled_out_ids", ()):' in blk
   and "continue" in blk[blk.index("_ruled_out_ids"):blk.index("_ruled_out_ids") + 300])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
