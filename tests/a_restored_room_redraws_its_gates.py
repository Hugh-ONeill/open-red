#!/usr/bin/env python3
"""A checkpoint restore in Cinnabar's gym redraws its gates from the save.

The gym rewrites its gate blocks from the gate flags only on entry and after
a fight (story6 applyGymGates); a restore put the save back without either,
so the next arena trial walked the last trial's open gates, scored 4/8 where
the first scored 8/8, and every Cinnabar room read 75% whatever the policy
or the level (2026-10-01; after the fix, 8/8 and 8/8). Source checks.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


sh = (ROOT / "harness/shim.lua").read_text()
cr = sh[sh.index("function OPS.checkpoint_restore("):]
cr = cr[:cr.index("\nfunction OPS.", 10)]
ck("a restore reruns the entry hook of a map drawn from the save",
   "hooks.onEnter" in cr and "local _redraw = { CINNABAR_GYM = true }" in cr)
ck("...after the restore itself succeeded",
   cr.index("pcall(Checkpoint.restore, G, ck)") < cr.index("local _redraw"))
ck("...and only there (a league room's entry starts an event)",
   "_redraw[_mid]" in cr)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
