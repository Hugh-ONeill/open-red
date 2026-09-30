#!/usr/bin/env python3
"""The train rule's wild_items "never" holds after the fight, not only in it.

A grind topped the party up with a HYPER_POTION after every wild fight: 26
field heals, 20 down to 1, before Victory Road and the Elite Four (run 19,
2026-09-30). Poison cures still happen (poison keeps chipping); only the
heal is gated, and only in a training step's wild fight.

Source checks: the gate sits in the executor's battle hand-off.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


src = (ROOT / "planner/executor.py").read_text()
i = src.index("battle_policy.should_field_cure(obs, ACTIVE_SPEC)")
blk = src[i:i + 4000]
ck("the cure is still unconditional", "pick = battle_policy.should_field_cure(obs, ACTIVE_SPEC)" in src[i - 60:i + 80])
ck("the heal reads the train rule's wild_items",
   '.get("wild_items") == "never"' in blk)
ck("...and skips only for a trainee in a wild fight",
   '_no_meds = _tr_never and _trainee and (b0.get("kind") or "wild") == "wild"' in blk
   and "if _no_meds:\n            pick = None" in blk)
j = src.index("_trainee = None")
ck("_trainee is always bound before the gate reads it", j < i)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
