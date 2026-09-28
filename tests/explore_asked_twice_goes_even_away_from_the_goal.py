#!/usr/bin/env python3
"""Explore asked twice goes, even away from the goal (2026-09-28).

Refusing every "away" explore left the run standing in Cerulean for an hour:
every place with something left (Route 4, Routes 24/25 with Bill unspoken
to) was away from Vermilion, explore was refused fifteen times and the
repeat gate refused the rest (user: "theres no world in which it should be
staying in the same place"). The first ask is still refused with the reason;
a second ask with the world unchanged goes, and the repeat gate lets that
second explore through.

Source checks (explore needs a live world to exercise).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()
checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


ck("the away refusal is keyed on step, goal and world mark",
   '_akey = (str(sg.get("id")), _g, tuple(self._world_mark(obs) or ()))' in src)
ck("asked again with nothing changed, explore goes and says so in the journal",
   'self.log("explore_went_away", subgoal=sg.get("id"),' in src)
ck("the refusal tells the model a second ask goes",
   "ask for explore again and it will walk to" in src)
ck("the repeat gate lets that second explore through",
   'self.log("repeat_allowed_explore_after_away",' in src
   and 'getattr(self, "_away_last", None) == str(sg.get("id"))' in src)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
