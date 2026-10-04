#!/usr/bin/env python3
"""A sweep stops for a spent party, not for a fainted bench.

Run 35, 2026-10-03: a two-member party with its L3 PIDGEY fainted and
BULBASAUR at 24/24 read "your party is nearly out -- 1 of 2 still standing"
and every sweep of Viridian Forest walked zero steps (user: "its having
trouble in the viridian forest"). Run 19's case the stop was written for, a
lone IVYSAUR at 21/54 in Mt Moon, still stops. Verified in game on the run 35
leg 3 checkpoint: the sweep walks again. Source pins."""
from pathlib import Path
lua = (Path(__file__).resolve().parents[1] / "harness/shim.lua").read_text()
i = lua.index("A SWEEP STOPS WHEN THE PARTY IS NEARLY OUT")
blk = lua[i:i + 5200]
checks = [
    ("one left standing counts only when that one is below half",
     "(_n > 1 and _up <= 1 and _lh * 2 < _lm)" in blk),
    ("a party below a third of its HP still stops", "_hp * 3 < _mx" in blk),
    ("the standing members' HP is what the half is measured on",
     "if h > 0 then _up = _up + 1; _lh, _lm = _lh + h, _lm + mxh end" in blk),
    # Run 36, 2026-10-04: the Route 15 gate's sweep stopped at zero steps on
    # a party at 25%, and its west door never came into view. Verified in
    # game on a crafted save (party at 6%, inside the gate): the old code
    # walks 0 steps, the new one walks 4 and finds the doorway at (0,4).
    ("a building with no wild POKEMON does not stop the sweep",
     "GATE = 1" in blk and "POKECENTER = 1" in blk and "HOUSE = 1" in blk
     and "and not _safe" in blk),
    ("...unless an unbeaten trainer stands on the floor",
     "if d.trainerClass and _beat[_k] ~= true then _safe = false; break end" in blk
     and '("%s_obj_%d")' in blk),
    ("caves, forests, the tower and the mansion keep the stop",
     not any(t + " = 1" in blk for t in ("CAVERN", "FOREST", "CEMETERY",
                                          "MANSION", "FACILITY", "OVERWORLD"))),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
