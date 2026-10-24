#!/usr/bin/env python3
"""The dead-end line says no "except" when nothing is excepted.

Run 62, 2026-10-24: on Mansion 1F, with no PC or sign in the room, the line
read "Everything here that presses has now been tried except , and a
computer stores while a sign reads — neither opens ground". Pinned (source):
the except clause is said only when there is something to except.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner" / "executor.py").read_text()
ok = ('"Everything here that presses has now been tried. ")' in src
      and "if _talk else" in src[src.find("NO \"EXCEPT\" WITH NOTHING AFTER IT"):][:900])
print(("ok   " if ok else "FAIL ") + "the except clause needs something to except")
print(f"\n{int(ok)}/1 checks passed")
sys.exit(0 if ok else 1)
