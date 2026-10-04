#!/usr/bin/env python3
"""The room sweep presses people before fixtures, and says how many it left.

Run 36, 2026-10-03: the Game Corner's sweep pressed eight things in map
order (machines first), never reached GAMECORNER_ROCKET, and announced
"everything reachable here that PRESSES has now been tried" with 28 untouched
(user: "it hasnt talked to the rocket in the game corner despite talking to
everyone else"). Source pins."""
from pathlib import Path
src = (Path(__file__).resolve().parents[1] / "planner/executor.py").read_text()
checks = [
    ("people are ordered ahead of fixtures in the sweep",
     'loose = ([n for n in loose if kinds.get(n) in ("npc", "trainer")]' in src),
    ("'everything ... tried' is said only when nothing was left",
     "if _pressed and not _left:" in src),
    ("otherwise the count and what is left are said, people named first",
     "still never pressed" in src and '_lp = [n for n in _left if kinds.get(n) in ("npc", "trainer")]' in src),
    ("the gym leader is still left out (that filter runs before)",
     src.index("A GYM LEADER IS NOT SOMETHING YOU TRY") < src.index("PEOPLE FIRST. The sweep presses eight")),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
