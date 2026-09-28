#!/usr/bin/env python3
"""Sealed and out-of-reach are said only over ground the player has seen
(audit PT-22/23, 2026-09-28). pocket_of and reachable_cells flood the real
collision grid, unseen cells included, so "N cell(s) ... lie in pockets with
no doorway" and "no ground you can walk to touches that side" were claims a
player could not make. A pocket is sealed only when all of it has been on
screen; a side is ruled out only when every reachable cell has been.

Source checks (the shim needs a booted game; measure Diglett's Cave's sealed
count on a real boot at the stop).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "harness/shim.lua").read_text()
checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


ck("a pocket is sealed only when all of it has been seen",
   "and not pk.joins and not pk.wet\n                       and pk.all_seen" in src)
ck("pocket_of still reports whether every cell was on screen",
   "if not mask[ck] then out.all_seen = false end" in src)
ck("no side is ruled out while any reachable cell is unseen",
   "local _mask3 = SEEN[(map and map.id) or \"\"] or {}" in src
   and "for d in pairs(md.connections) do _cr[d] = true end" in src)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
