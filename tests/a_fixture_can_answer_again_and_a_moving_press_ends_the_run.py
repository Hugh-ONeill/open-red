#!/usr/bin/env python3
"""A pressed fixture is not "nothing new to find", and a press that fires an
event ends a run of presses.

In LT. SURGE's gym every trash can had been pressed, and the page's closing
line said only never-pressed things "can find anything new here": run 27
concluded no can could be the switch. And round 11 pressed "TRASH_CAN_6,
then 0, 1, 2, 3 ..." in one macro, so the press that opened the first lock
was undone by the next (user, 2026-09-16: "build the closing line fix and
the macro cut too").

Pinned: the closing line names the fixture exception only when a fixture is
listed; the macro stops after an interact whose press fired an event flag
when the next op is another interact, says so, and logs what it dropped.

Synthetic: the render with a stub executor, and source anchors.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import ledger as L            # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


class _Empty(dict):
    def __call__(self, *a, **k):
        return ""


class Stub:
    def __getattr__(self, name):
        return _Empty()

    def _where(self, obs):
        m = (obs or {}).get("map") or {}
        return f"{m.get('id')}|{m.get('region')}"


OBS = {"mode": "overworld", "flags": [],
       "map": {"id": "VERMILION_GYM", "region": "4,5", "objects": [],
               "warps": []}, "player": {"x": 4, "y": 5}}
can = L.Candidate(key="TRASH_CAN_3", kind="fixture", dest=None)
with_fixture = L.render([can], Stub(), OBS)
without = L.render([], Stub(), OBS)
ck("the closing line names the fixture exception where a fixture is listed",
   "except a fixture, which can answer differently when pressed again" in with_fixture)
ck("...and not where none is",
   "except a fixture" not in without
   and "are the only ones that can find anything new here. Which matters is your call." in without)

SRC = (ROOT / "planner/executor.py").read_text()
blk = SRC[SRC.index("A PRESS THAT MOVED THE WORLD ENDS A RUN OF PRESSES."):]
blk = blk[:blk.index("if not ignore_done and pred_holds(done, self.settle()):")]
ck("the cut is for an interact whose press fired a flag",
   'if op == "interact":' in blk and "_f1 - _f0" in blk)
ck("...only when the next op is another press",
   '_nxt.get("op") == "interact"' in blk and "macro[_mi + 1]" in blk)
ck("...and says what happened and logs what was dropped",
   "— stopped here: that press changed the world" in blk
   and 'self.log("macro_cut_after_event"' in blk and "dropped=" in blk)
ck("the macro loop knows each op's position",
   "for _mi, step in enumerate(macro):" in SRC)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
