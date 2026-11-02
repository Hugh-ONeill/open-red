#!/usr/bin/env python3
"""A won fight's recap does not say the last foe was not knocked out.

Run 58, 2026-10-17, the lab rival: money 3000 -> 3175, BULBASAUR L5 -> L6,
"battle over: win", fight_recap lost:false, and the text "CHARMANDER L5 ...
was at 2 hp when it stopped taking hits — it was not knocked out": the last
turn read was the one before the knockout hit. Pinned by source: the clause
needs the fight to have been lost.
"""
import sys
from pathlib import Path

src = (Path(__file__).resolve().parents[1] / "planner/executor.py").read_text()
i = src.index('" — it was not knocked out"')
ok = "and first[-1] > 0 and lost else" in src[i:i + 200]
print(("ok   " if ok else "FAIL ") + "the not-knocked-out clause needs a lost fight")
sys.exit(0 if ok else 1)
