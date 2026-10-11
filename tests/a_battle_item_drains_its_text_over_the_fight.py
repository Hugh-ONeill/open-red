#!/usr/bin/env python3
"""A battle item drains its message over the fight before it returns.

Run 48, Cerulean rival (2026-10-11): the policy used a POTION on turn 6,
battle_item returned "used POTION in battle" with "GNOCCHI recovered by
20!" still in a box over the fight (the drain loop read the box as "not a
battle" and left), and the next battle_move answered "not in battle". The
policy's loop quit mid-fight, the fight was recapped half done and
re-entered, and the rival's BILL line never reached the record. Probed on
run 48's leg-10 save with the lead at 20 HP: before, move 2 after the item
failed "not in battle" with HP still unhealed; after, HP 9 -> 18 (healed,
then the foe's turn) and move 2 goes through.

Pinned: the drain taps on while the battle state is still on the stack
under whatever is on top, and stops at the action or move menu. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "harness/shim.lua").read_text()
checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


fn = SRC[SRC.index("function OPS.battle_item(G, c)"):]
fn = fn[:fn.index("\nfunction OPS.throw_ball")]
ck("the old early exit is gone",
   "if not (t and U.is_battle(t)) then break end" not in fn)
ck("it stops at the action or move menu",
   'if t.phase == "menu" or t.phase == "moveSelect" then break end' in fn)
ck("over a box it taps on while the battle is under it",
   "for _, st in ipairs((G.stack and G.stack.states) or {}) do" in fn
   and "if st == b then under = true break end" in fn
   and "if not under then break end" in fn)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"{len(checks) - len(failed)}/{len(checks)} passed")
sys.exit(1 if failed else 0)
