#!/usr/bin/env python3
"""The walker's sidestep out of a person's way never steps into a boulder.

Run 27, 2026-09-18, Victory Road 2F: a push route was cut by a wild fight
with the party at (4,14) above the boulder at (4,15). The walker's sidestep
(yield_ground) tries "down" first and tested collision only on a warp, so
with STRENGTH on it shoved the boulder to (4,16), where nothing moves it
(user: "it just moved the boulder into an unmovable position somehow").

Pinned: the sidestep refuses a cell with a boulder (SPRITE_BOULDER) and asks
the game's collision on every step. Source-anchored: the walker runs in the
game."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


lua = (ROOT / "harness/shim.lua").read_text()
i = lua.index("local function yield_ground(G)")
blk = lua[i:i + 3000]
ck("a cell holding a boulder is not stepped onto",
   '(e.def or {}).sprite == "SPRITE_BOULDER" then\n            safe = false' in blk)
ck("collision is asked on every sidestep, not only on a warp",
   "if safe and on_warp then" not in blk
   and "safe = okc and Collision and Collision.canMove" in blk)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
