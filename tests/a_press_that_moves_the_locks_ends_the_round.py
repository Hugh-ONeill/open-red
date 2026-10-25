#!/usr/bin/env python3
"""A press whose result says the locks changed ends the round's presses.

Run 66, 2026-10-25: Lt. Surge's gym. The model pressed six to twelve cans a
round; after "The 1st electric lock opened!" the round went on, the next
wrong can reset both locks, and the cans after a reset were pressed into a
puzzle the round was written before. About 30 rounds (run 65: 18). The round
now stops after a press that says a lock opened or the locks were reset, and
the trace says why. It names no can.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

f = E.Executor._press_moved_puzzle
ck("the 1st lock opening moves the puzzle",
   f("interact(name=TRASH_CAN_3): ok — it said: \"Hey! There's a switch under the trash! Turn it on! The 1st electric lock opened!\""))
ck("the 2nd lock opening moves it", f("ok — it said: \"The 2nd electric lock opened! The motorized door opened!\""))
ck("a reset moves it", f("ok — it said: \"Nope! There's only trash here. Hey! The electric locks were reset!\""))
ck("only trash with no reset does not", not f("ok — it said: \"Nope, there's only trash here.\""))
ck("a person talking does not", not f("ok — it said: \"I'm a lightweight, but I'm good with electricity!\""))

src = (ROOT / "planner" / "executor.py").read_text()
ck("the round loop cuts on it, after an interact",
   'self._macro_prev_op == "interact" and trace\n                    and self._press_moved_puzzle(trace[-1])' in src)
ck("...and says why in the trace",
   "that press changed the locks, and the" in src and "macro_cut_lock_moved" in src)
ck("...without naming a can", "TRASH_CAN" not in src[src.find("def _press_moved_puzzle"):src.find("def _run_traced")])

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
