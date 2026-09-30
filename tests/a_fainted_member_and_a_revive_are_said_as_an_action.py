#!/usr/bin/env python3
"""A fainted member and a REVIVE in the bag are said on the page as an action.

The run never used a REVIVE outside a battle, and a fainted trainee was told
it "cannot move until it is healed at a Pokemon Center" with REVIVEs in the
bag (run 19, 2026-09-30). The fact and the op; the spend is the model's.

Synthetic, plus a source check.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


party = [{"species": "GRAVELER", "hp": 150}, {"species": "PIDGEOT", "hp": 0}]
t = E.Executor._revive_note({"mode": "overworld", "party": party, "bag": {"REVIVE": 3}})
ck("a fainted member with a REVIVE held is said, with the op",
   "PIDGEOT (slot 2) fainted" in t and '{"op":"use_item","item":"REVIVE","slot":2}' in t, t)
ck("no REVIVE held: nothing said",
   E.Executor._revive_note({"mode": "overworld", "party": party, "bag": {"POTION": 3}}) == "")
ck("nobody fainted: nothing said",
   E.Executor._revive_note({"mode": "overworld", "party": party[:1], "bag": {"REVIVE": 3}}) == "")
ck("in a battle: nothing said (the battle has its own rules)",
   E.Executor._revive_note({"mode": "battle", "party": party, "bag": {"REVIVE": 3}}) == "")
src = (ROOT / "planner/executor.py").read_text()
ck("it leads the escalation page", "return self._revive_note(obs) + move_head + out" in src)
ck("the fainted-trainee note no longer sends it only to a Center",
   "or brought back with a REVIVE from the bag" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
