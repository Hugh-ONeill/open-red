#!/usr/bin/env python3
"""A lift ride draws every frame even when the run draws one in N.

Run 36, 2026-10-04: under stream.sh's RED_DRAW_EVERY=30 every Celadon store
ride hit the 120001-frame watchdog after the floor was chosen (5 of 5), while
drawing every frame the same ride took two seconds. In game with the fix and
RED_DRAW_EVERY=30: 4F, 1F, 5F, two seconds each. Source pins."""
from pathlib import Path
lua = (Path(__file__).resolve().parents[1] / "harness/shim.lua").read_text()
checks = [
    ("the draw skip yields to a draw-all flag",
     "if every > 1 and drawn % every ~= 0 and not wd.draw_all" in lua),
    ("the elevator op sets it for its whole length and always clears it",
     "wd.draw_all = true\n  local ok, r1, r2 = pcall(U.elevator_body, G, c)\n  wd.draw_all = false" in lua),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
