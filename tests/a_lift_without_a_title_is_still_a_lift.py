#!/usr/bin/env python3
"""The floor menu is known by its rows, and a key is blamed only when the
game says key.

Run 36, 2026-10-04: the new base's lift panel has no title, so the elevator
op never saw its floor menu, pressed A into it, and reported "the LIFT KEY is
what it wants" in the Celadon Department Store while the game asked "Which
floor do you want?"; the model believed the store's lift locked for an hour.
In game after the fix: rode to 4F and back to 1F. Source pins."""
from pathlib import Path
lua = (Path(__file__).resolve().parents[1] / "harness/shim.lua").read_text()
checks = [
    ("a list whose rows read as floors is the floor menu",
     'if lab:match("^%s*B?%d+F%s*$") or lab:find("ROOF") then n = n + 1 end' in lua),
    ("A is never pressed into an open list while waiting",
     "if t and t.items then break end          -- some other list: do not press into it" in lua),
    ("a key is named only when the game's words say key",
     'if tostring(_said):lower():find("key") then' in lua
     and '"the panel opened no floor menu — the LIFT KEY is what "' not in lua),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
