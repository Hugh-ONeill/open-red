#!/usr/bin/env python3
"""A person who walked away is not a press that brought up nothing.

Run 71, 2026-11-02, Pallet Town: interact on PALLETTOWN_GIRL, who wanders,
pressed empty floor where she had been and reported "pressed it from (4,8)
facing up, (4,7) facing up and nothing came up; its other sides are taken:
PALLETTOWN_GIRL at (5,6)", which counted her as touched (0677494) though no one
spoke to her. Pinned by source in OPS.interact: the pressed-nothing record
is kept only when the target is not a named person.
"""
import sys
from pathlib import Path

src = (Path(__file__).resolve().parents[1] / "harness/shim.lua").read_text()
i = src.index("function OPS.interact(G, c)")
body = src[i:src.index("\nfunction ", i + 10)]
j = body.index("local pressed_empty = {}")
ok = ("if not npc_named and math.abs(a[1] - tx) + math.abs(a[2] - ty) == 1 then"
      in body[j:j + 2200]) and body.index("local npc_named = nil") < j
print(("ok   " if ok else "FAIL ") + "a named person who moved is never recorded as pressed-nothing")
sys.exit(0 if ok else 1)
