#!/usr/bin/env python3
"""A field move the game refuses twice is reported refused both times.

2026-10-19, Seafoam B3F: the refusal was found by the on-screen text
changing, so a second "No SURFing on FIZZY here!" in one walk read "SURF did
not fire (the menus closed without it)" with our own advice about facing
the water. Probed in game: two presses at (16,4) both quote the game.
Source pins.
"""
from pathlib import Path
shim = (Path(__file__).resolve().parents[1] / "harness/shim.lua").read_text()
checks = [
    ("the printed-line counter is taken before the move", "local _seq_before = text_seq" in shim),
    ("a line printed during the move is the game's answer, even the same words",
     "or text_seq ~= _seq_before) then" in shim),
]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
