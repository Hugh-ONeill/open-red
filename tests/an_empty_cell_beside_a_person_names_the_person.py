#!/usr/bin/env python3
"""A press at an empty cell beside a person says so and names the person.

2026-09-04, Rocket Hideout B4F: the model sent {"op":"interact","x":22,"y":12}
four rounds running to fight the grunt standing at (23,12); the shim said only
"no reachable tile adjacent to target — standing on the tiles you would press
from: ROCKETHIDEOUTB4F_ROCKET1 at (23,12)". (TODO line 1927, still open at run
70's stop, 2026-11-02.) Pinned by source in OPS.interact: a coordinate press
whose cell holds no person or fixture, with a person beside it, says nothing
pressable is AT the cell and gives that person's by-name op; the executor's
empty-cell note still rides along.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
shim = (ROOT / "harness/shim.lua").read_text()
ex = (ROOT / "planner/executor.py").read_text()
i = shim.index("AN EMPTY CELL BESIDE A PERSON IS NOT THE PERSON.")
blk = shim[i:i + 2400]
checks = [
    ("only for a coordinate press", "if not c.name then" in blk),
    ("the cell's own occupants are checked first",
     "npc.cellX == tx and npc.cellY == ty" in blk and "f.x == tx and f.y == ty" in blk),
    ("the person beside it is named with the by-name op",
     'nothing that can be pressed is AT (%d,%d)' in blk and '\\"op\\":\\"interact\\"' in blk),
    ("...before the pressed-nothing and no-reachable-tile refusals",
     blk.index("nothing that can be pressed is AT") < blk.index("if #pressed_empty > 0 then")),
    ("the executor's empty-cell note reads the new words too",
     '"nothing that can be pressed is AT" in det' in ex),
]
bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
sys.exit(1 if bad else 0)
