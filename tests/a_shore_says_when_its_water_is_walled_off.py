#!/usr/bin/env python3
"""A crossing refused from the shore says when the water there, swum, does
not reach the edge either, instead of offering SURF for a round.

Run 67, 2026-10-28, Route 20 by Seafoam's (48,5): from the shore the
refusal said "a party Pokemon knows SURF ... from there water is
walkable"; every swim then read "walled off before it", and the run went
shore -> swim -> refused -> shore for hours. Proven on a copy of the live
save: from (48,6) west now reads walled off, and east (open water to
Route 19) still offers SURF.

Pinned: the swim search is asked only when someone knows SURF and the
search did not already swim; its verdict lives for that cross; both
clauses that offered SURF read it. Source-anchored: it runs in the game.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
shim = (ROOT / "harness" / "shim.lua").read_text()
ck("the swim search is asked from the shore",
   "local _walled = knows_surf and not _swim and (nwater > 0 or _tw_n > 0)\n"
   "                  and bfs_to_edge(G, dir, 0, true) == nil" in shim)
ck("...its verdict is kept for this cross only",
   "wd.swim_walled = _walled or nil" in shim
   and "bfs_to_edge = function(G, dir, skip, surf, blind, collect, only)\n  wd.swim_walled = nil" in shim
   and "wd.swim_walled = nil  -- and a cross's swim verdict only inside that cross" in shim)
ck("the water-between clause says it is walled off",
   "with the water counted as ground does not reach" in shim)
ck("the edge words agree", "or _ks and wd.swim_walled" in shim
   and "and swum, the water you can ride from here" in shim)
ck("the reachable case still offers SURF",
   "and a party Pokemon knows SURF: {\\\"op\\\":\\\"field_move" in shim)
bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n)
sys.exit(1 if bad else 0)
