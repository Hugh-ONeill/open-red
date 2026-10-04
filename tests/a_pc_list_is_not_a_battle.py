#!/usr/bin/env python3
"""A screen with a `kind` is not a fight unless it has the sides of one.

Run 36, 2026-10-03: the new base's PC deposit list carries kind =
"pc_item_deposit"; every `t.enemy or t.kind` test read it as a battle, back-out
returned without pressing B, and the battle's A presses deposited the whole
bag after store_item(TM_BIDE) (user: "it also just deposited every item").
Reproduced in game on the run's leg-27 checkpoint: 16 kinds -> 0 before, 16
-> 15 after, and retrieve_item brings it back. Source pins."""
from pathlib import Path
lua = (Path(__file__).resolve().parents[1] / "harness/shim.lua").read_text()
import re
checks = [
    ("one test for a fight", "function U.is_battle(t)" in lua),
    ("it needs sides, a trainer or a phase beside the kind",
     "(t.kind ~= nil and\n    (t.player ~= nil or t.trainer ~= nil or t.phase ~= nil))" in lua),
    ("no bare `X.enemy or X.kind` test is left",
     not re.search(r"\((\w+)\.enemy or \1\.kind\)", lua) and "if top.enemy or top.kind then" not in lua),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
