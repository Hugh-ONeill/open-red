#!/usr/bin/env python3
"""A door stopped by someone still talking or asking says so, not "refused".

Run 70, 2026-11-02, collect_hm04 r13: use_warp at SAFARI_ZONE_GATE (3,0) said
"you reached the door and it refused to open — the game said: \\"Welcome to
the SAFARI ZONE!\\". You stood on the mat; walking somewhere else and coming
back will not change the answer." The worker's pay-to-join question was the
rest of that speech, and answering it opens the way; the model wondered if
HM03 had opened it. Next round the box was still up.

Pinned by source in OPS.use_warp: with a yes/no box open the refusal says a
question is open and the answer decides it; with a box up it says the game
is still talking; only otherwise does it say coming back will not change it;
and the check does not call the ui_* locals defined below the op.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "harness/shim.lua").read_text()
checks = []
def ck(n, ok): checks.append((n, bool(ok)))

i = src.index("function OPS.use_warp(G, c)")
j = src.index("REACHED AND REFUSED IS NOT UNREACHED", i)
blk = src[j:j + 2600]
a = blk.find("is ASKING you something now")
b = blk.find("is still talking: a box is up")
c = blk.find("will not change the answer")
ck("an open question is said first", 0 < a < b < c)
ck("...tested inline, not through ui_* locals defined later",
   "_t.index ~= nil and _t.items == nil and not _t.prizes" in blk
   and "ui_is_choice(G)" not in blk[:c] and "ui_top(G)" not in blk[:c])
ck("the plain refusal still reads as before for the ledger",
   "somewhere else and coming back will not change the answer." in blk)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
