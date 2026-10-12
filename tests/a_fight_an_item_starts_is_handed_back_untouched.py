#!/usr/bin/env python3
"""A fight an item starts is handed back untouched, not pressed through.

use_item(POKE_FLUTE) beside ROUTE16_SNORLAX: the op's text-advancing A rode
"SNORLAX woke up! It attacked in a grumpy rage!" into the battle, picked FIGHT
and move 1, and GRAVELER's EXPLOSION ended it inside the op: no policy turn,
no catch, GRAVELER at 0/123 (run 53, 2026-10-12). Reproduced on a copy of the
leg 28 checkpoint teleported to ROUTE_16 (27,10): before the fix the op came
back "used POKE_FLUTE" in the overworld with GRAVELER fainted; after it,
"AND A FIGHT BEGAN", mode=battle, SNORLAX 140hp, the party untouched.

The battle's frame there carries kind="wild" and no .enemy, so battle_frame()
does not see it; U.is_battle() does.

Source checks (harness/shim.lua).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


sh = (ROOT / "harness/shim.lua").read_text()
ui = sh[sh.index("function OPS.use_item(G, c)"):]
ui = ui[:ui.index("\nfunction OPS.", 10)]
loop = ui[ui.index("while true do"):ui.index("ui_back_out(G)\n  -- ...AND IF IT IS STILL UP")]
ck("the advancing loop looks for a battle anywhere on the stack",
   "A FIGHT IS NOT THIS OP'S TO PLAY" in loop
   and "U.is_battle(_st[k])" in loop)
ck("...before it presses anything",
   loop.index("A FIGHT IS NOT THIS OP'S TO PLAY") < loop.index('U.tap(G, "a")')
   and loop.index("A FIGHT IS NOT THIS OP'S TO PLAY") < loop.index('U.tap(G, "b")'))
ck("...and returns at once, so no back-out presses land in the fight",
   "AND A FIGHT BEGAN" in loop and "return true" in loop[loop.index("A FIGHT IS NOT"):
                                                            loop.index("ONE USE PER OP")])
ck("the check is not the .enemy-only battle_frame()",
   "battle_frame(G)" not in loop[loop.index("A FIGHT IS NOT"):loop.index("ONE USE PER OP")])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
