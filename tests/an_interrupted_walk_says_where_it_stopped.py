#!/usr/bin/env python3
"""A walk that a fight stopped says where the party stands, and a reply
with no ops is free once and told where the party stands.

Run 27, 2026-09-18, Pokemon Mansion 3F: walk_to(16,14), the hole, came back
"ok" though a PONYTA had stopped it partway (the shim's detail said
"interrupted (battle or script)" and the executor dropped it). Twice the
model then replied "I have just walked onto the hole ... I will now observe
where this drop takes me" with no ops; each empty reply was spent, and the
step ran out of rounds on them (user: "what just caused it to stop on
escalation 6? it was trying to get to the hole but battles interrupted
it").

Pinned: an "ok" walk that did not end on the cell asked for, on the same
map, reports where it stopped with the shim's detail; a first empty reply
in a row is not spent and is told the party's position; a second is
spent; a reply with ops resets the count. Source-anchored: the loop runs
the game.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


src = (ROOT / "planner/executor.py").read_text()
w = src[src.index('            if op == "walk_to" and step.get("x") is not None:'):][:4000]
ck("an ok walk that did not arrive says where it stopped, with the shim's detail",
   'f"walk_to({step.get(\'x\')},{step.get(\'y\')}): stopped "' in w
   and 'f"at ({_at[0]},{_at[1]}), not the cell asked for"' in w
   and '(f" — {_d0}" if _d0 else "")' in w)
ck("...only on the same map (a warp or a drop is an arrival of another kind)",
   "if (_mid0 == _mid1 and _at != (step.get(\"x\"), step.get(\"y\"))" in w)
e = src[src.index("            if not macro:\n                self.log(\"escalate_bad_proposal\""):][:2200]
ck("an empty reply is told where the party stands",
   "You are standing at (" in e and "nothing moves you until an op does." in e)
ck("...the first in a row is free and a second is spent",
   "self._empty_in_row = int(getattr(self, \"_empty_in_row\", 0) or 0) + 1" in e
   and "if self._empty_in_row > 1:\n                    spent += 1" in e)
ck("...and a reply with ops resets the count", "            self._empty_in_row = 0" in e)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
