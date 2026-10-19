#!/usr/bin/env python3
"""At the edge of a walk, a Seafoam current is named a current and says
where it sets you down, not "WATER".

Run 58, 2026-10-19, Seafoam B3F: the party was afloat in a 30-cell pocket
whose edge is the currents at (18,7)/(19,7). The reach (seen_reach) rides
them to (20,17) and listed unseen ground past them, while the walk, which
never plans over a current, said "WATER at (19,7) ... does not reach it
either" and every sweep walked 0 steps; the run looped for hours. Probed in
game on the run's own save: the failing walk_to now names both currents
and their landing, and walk_to(19,7) rides out of the pocket to B4F.
Source pins; the landing itself is pinned by
a_current_sets_the_rider_down_somewhere.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

shim = (ROOT / "harness/shim.lua").read_text()
i = shim.index("local function bushes_blocking(G, tx, ty, reach)")
j = shim.index("\nend\n", i)
fn = shim[i:j]
ck("the edge list reads the currents while afloat",
   "seafoam_forced(G)" in fn and 'v == "carried"' in fn)
ck("...only those that touch the ground the walk reached",
   'reach[(cx + d[1]) .. "," .. (cy + d[2])]' in fn)
ck("...says where the ride sets you down, from the engine's landing",
   "seafoam_landing(G, cx, cy)" in fn and "sets you down at (%d,%d)" in fn)
ck("...and that aiming at the current's cell rides it",
   "walk_to aimed at the current's own cell rides it" in fn)
ck("a current named is not named WATER again",
   "if wx_ == c.x and wy_ == c.y then wx_ = nil end" in fn
   and fn.index("a CURRENT at (%d,%d)") < fn.index('"WATER at (%d,%d)'))
ck("the walk still does not plan over a current, only aims at one",
   "if k ~= (tx .. \",\" .. ty) then blocked[k] = true end" in shim)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
raise SystemExit(1 if failed else 0)
