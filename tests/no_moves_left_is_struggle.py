#!/usr/bin/env python3
"""With no moves left, FIGHT is Struggle, not a failure.

Run 51, Mt Moon 1F (2026-10-11): a lone IVYSAUR with every move at 0 PP.
FIGHT printed "NUGGET has no moves left!" (the game then uses Struggle
itself), battle_move called that a failure every turn, the policy's loop
left the fight, and the Lass's CLEFAIRY won without being hit. Probed on
run 51's forest save with every PP at 0: before, three "no move list
opened" failures while the game struggled on underneath; after, "no moves
left — the game used STRUGGLE", ok.

Pinned: the line is matched across the box's line break, the turn is
ridden out, and the op says Struggle was used. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "harness/shim.lua").read_text()
fn = SRC[SRC.index("function OPS.battle_move(G, c)"):]
fn = fn[:fn.index("\nfunction OPS.", 10)]
checks = [
    ("matched across the line break",
     'said:gsub("%s+", " "):find("has no moves left", 1, true)' in fn),
    ("the turn is ridden out", "U.battle_advance(G, b)" in fn.split("has no moves left", 2)[2][:400]),
    ("it is said as Struggle, ok", 'return true, "no moves left — the game used STRUGGLE"' in fn),
    ("other screens are still refusals", 'return false, "no move list opened — the screen says' in fn),
]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
bad = [n for n, ok in checks if not ok]
print(f"{len(checks) - len(bad)}/{len(checks)} passed")
sys.exit(1 if bad else 0)
