#!/usr/bin/env python3
"""A toss answers "Is it OK to toss X?" with YES, after pressing the text
through to its choice.

The new base shows the question as a prompting text box and pushes its
YES/NO only after A (BagMenu's toss: stay = { prompt = true, onShown =
ChoiceBox }). OPS.toss checked once for a choice, found the text, pressed
A once in its cleanup loop, raised the YES/NO, left on seeing no text page,
and ui_back_out answered it with B: NO. Every toss failed "toss did not go
through", with the bag full on Safari Zone East (run 36, 2026-10-04).
Verified in game from that checkpoint: a single TM tosses and frees its
slot, and one of three SUPER_POTION tosses through the quantity wheel.
Source pins.
"""
from pathlib import Path
lua = (Path(__file__).resolve().parents[1] / "harness/shim.lua").read_text()
i = lua.index("function OPS.toss(G, c)")
body = lua[i:lua.index("\nend\n", i)]
k = body.index("WAITS FOR A PRESS BEFORE IT ASKS")
tail = body[k:]
checks = [
    ("the text is pressed through until the choice is up",
     "if ui_is_choice(G) then break end" in tail
     and 'U.tap(G, "a"); U.wait(8)' in tail),
    ("...bounded",
     "for _ = 1, 12 do" in tail),
    ("YES is chosen by row, not by whatever the cursor holds",
     'ui_cursor_to(G, "index", 1)' in tail),
    ("the answer comes before the clean-up loop and the back-out",
     tail.index('ui_cursor_to(G, "index", 1)') < tail.index("ui_back_out(G)")),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
