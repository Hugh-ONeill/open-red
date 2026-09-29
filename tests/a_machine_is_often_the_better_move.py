#!/usr/bin/env python3
"""A machine is often the better move (run 19, 2026-09-29).

The TM question closed "Saying no is a real answer and often the right one",
and run 19 kept LEECH_SEED over TM_MEGA_DRAIN on VENUSAUR (user: "we should
posit the true fact that TMs are often stronger than what a pokemon
naturally learns, or at least quicker"). Source check.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

t = E.Executor.TEACH_SYS
checks = [("the prompt no longer leans to no", "often the right one" not in t),
          ("it says a machine's move is often stronger, or earlier",
           "often STRONGER than anything that Pokemon learns by level" in t
           and "arrives long before level-up would bring it" in t),
          ("saying no is still a real answer", "Saying no is a real answer." in t)]
failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
