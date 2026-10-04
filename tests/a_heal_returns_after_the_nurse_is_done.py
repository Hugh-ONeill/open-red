#!/usr/bin/env python3
"""A heal hands back the player only after the nurse is done.

The party is healed BEFORE the machine runs (HealParty, then the balls
light up), and while the machine runs the overworld is on top with no
script, emote or text box. OPS.heal stopped riding the ceremony there,
read every Pokemon at full HP and returned; "Your POKeMON are fighting
fit!", her bow and "We hope to see you again!" then went up on the next
op and ate its input. Every first walk after a heal stood still: "blocked
at (3,3) heading down" in the Fuchsia Center (run 36 checkpoint, pc_box,
2026-10-04). Verified in game: the walk after the heal now moves on the
first try, and pc_box passes from that checkpoint. Source pins.
"""
from pathlib import Path
lua = (Path(__file__).resolve().parents[1] / "harness/shim.lua").read_text()
i = lua.index("function OPS.heal(G, c)")
j = lua.index("\nend\n", i)
body = lua[i:j]
k = body.index("RIDE OUT THE WHOLE CEREMONY")
tail = body[k:]
checks = [
    ("the heal waits out the machine and the bow",
     "_ow.healAnim or _ow.emote" in tail),
    ("...presses through the nurse's last lines while a box is up",
     'if G.stack:top() ~= _ow then' in tail and 'U.tap(G, "a")' in tail),
    ("...and hands back only a quiet overworld, a few checks in a row",
     "_quiet >= 3" in tail),
    ("the HP check comes after the wait, not before it",
     tail.index("_quiet >= 3") < tail.index("local after = hurt()")),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
