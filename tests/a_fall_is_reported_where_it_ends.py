#!/usr/bin/env python3
"""A fall down a hole is reported where it ends, not mid-drop.

A fall runs holeArrive, then spinArrive, then the arrival checks
(pendingEnterMapTail: forced SURF and the Seafoam current), with the
overworld on top throughout. scripts_busy read none of them, so run 36 was
handed SEAFOAM_ISLANDS_B3F (18,7) — the B2F hole's landing, a current start
— as a place to stand; it planned a SURF from there three times and every
first step set the queued current off ("start menu never opened",
2026-10-04). Verified in game from a save beside the B2F (19,6) hole: the
old code reports B3F (18,7) not surfing, the new one B4F (20,15) surfing,
where the current leaves you. Source pins.
"""
from pathlib import Path
lua = (Path(__file__).resolve().parents[1] / "harness/shim.lua").read_text()
i = lua.index("local function scripts_busy(G)")
blk = lua[i:lua.index("\nend\n", i)]
checks = [
    ("the fall and its spin hold the report",
     "ow.holeFall or ow.holeArrive or ow.spinArrive" in blk),
    ("...and so do the arrival checks queued behind them",
     "ow.pendingEnterMapTail" in blk),
    ("...and the engine's other scripted holds",
     "ow.teleportOut or ow.flyAnim or ow.flyArrive or ow.engaging" in blk),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
