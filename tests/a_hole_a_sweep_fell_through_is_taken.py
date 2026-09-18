#!/usr/bin/env python3
"""A hole a sweep fell through is filed as taken, and a two-tile hole is
one hole on the page.

Run 27, 2026-09-18, Pokemon Mansion 3F: a sweep stepped onto (16,14) and
dropped to 1F's sealed room; a sweep has no destination cell, so the
crossing was never filed and the floor's holes kept reading as never
taken. The page also listed "3 (16,14, 17,14, 19,14)" where the shim's own
drop groups make it two (user: "do the holes still read as untried? its
gone through them (though it still renders as three holes and not two with
one being two tiles wide)").

Pinned: the sweep names the cell it stepped onto when the floor changes
under it; the recorder files an op with no cell under that one, folded to
the first tile of its drop; the per-map hole record keeps one entry per
drop, dropping twin tiles already recorded. Source-anchored: both run in
the game.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


shim = (ROOT / "harness/shim.lua").read_text()
sw = shim[shim.index("function OPS.sweep(G, c)"):]
sw = sw[:sw.index("\nfunction OPS.", 10)]
ck("the sweep notes the cell it stepped onto when the map changes under it",
   "local sweep_fell" in sw and "sweep_fell = { x = x0 + DIRS[dir][1], y = y0 + DIRS[dir][2] }" in sw)
ck("...and says it in its result",
   "you stepped onto (%d,%d) on %s " in sw and ".. fell_words" in sw)
src = (ROOT / "planner/executor.py").read_text()
nt = src[src.index("    def note_transition"):][:9000]
ck("the recorder files an op with no cell under the cell it fell through",
   'r"you stepped onto \\((\\d+),(\\d+)\\) on ([A-Z0-9_]+)"' in nt
   and '"transition_by_fall"' in nt)
ck("...folded to the first tile of that hole's drop",
   'if _mine is not None and _mine.get("drop") is not None:' in nt)
ck("...only when it fell from the map it started on",
   '_fell.group(3) == str(src).split("|")[0]' in nt)
ck("the hole record keeps one entry per drop and drops twins already kept",
   "(set(self.map_holes.get(_mid, ())) | _first) - _twins)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
