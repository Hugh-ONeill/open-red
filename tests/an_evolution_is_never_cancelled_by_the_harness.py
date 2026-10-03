#!/usr/bin/env python3
"""No harness B lands on a running evolution.

The new base cancels a level-up evolution on one B PRESS once 80 frames have
passed (EvolutionState, #968/#1031; the old base needed B HELD). At campaign
speed the harness's box-closing B presses cancelled it: GULLIVER the
BULBASAUR "stopped evolving" at the start of a grind and was still one at
L18 (run 36, 2026-10-03, user: "it stopped bulba from evolving").

Verified in game on a copy of run 36's leg-4 save (GULLIVER set to L15, one
exp short of 16): fixed shim -> IVYSAUR L16 after the next grind; the same
test on the old shim -> BULBASAUR L16. Source pins below."""
from pathlib import Path
lua = (Path(__file__).resolve().parents[1] / "harness/shim.lua").read_text()
checks = [
    ("a running, cancelable evolution is detected anywhere on the stack",
     "function U.evolving(game)" in lua and "st.newSpecies ~= nil and st.cancelable" in lua),
    ("B is refused while it runs, at the tap every loop goes through",
     'if btn == "b" and U.evolving(game) then' in lua),
    ("closing boxes waits an evolution out instead of pressing through it",
     "while U.evolving(G) do" in lua),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
