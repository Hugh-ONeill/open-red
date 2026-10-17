#!/usr/bin/env python3
"""A person whose every walkable neighbor was reached is not named as what
stopped a walk.

Run 58 (2026-10-17): Cerulean's east cross reported "Right where the walk
stopped: CERULEANCITY_COOLTRAINER_M ... at 31,20", four cells from the stall
point, with the search already past him at 34,21. The planner filed him as
the fence of the way east (user: "why is the cool trainer a blocker they
arent blocking anything"). Probed in game on run 58's Cerulean save: he is
now under "not what stopped you" and the fence named is the CUT_TREE at
(19,28).

Source test of shim.lua.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(name, ok): checks.append((name, bool(ok)))
src = (ROOT / "harness" / "shim.lua").read_text()
i = src.index("local function opens_more(nx, ny)")
fn = src[i:src.index("\n    end\n", src.index("return false", i)) + 9]
ck("a person opens more only through an unreached walkable neighbor",
   "not seen_cells[ax .. \",\" .. ay]" in fn and "lm:isWalkableCell(ax, ay)" in fn)
ck("...and with no reach record the old reading holds", "if not (seen_cells and lm and lm.isWalkableCell) then return true end" in fn)
loop = src[src.index("for _, npc in ipairs((ow.npcs) or {}) do", i):][:900]
ck("the person loop asks it first", "not opens_more(nx, ny)" in loop.split("by_stall")[0])
ck("...and such a person goes to the not-what-stopped-you list",
   "elsewhere[#elsewhere + 1]" in loop.split("by_stall")[0])
ck("the list is still headed as not the cause",
   "Also near that edge, though not what stopped you" in src)
bad = [n for n, ok in checks if not ok]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
