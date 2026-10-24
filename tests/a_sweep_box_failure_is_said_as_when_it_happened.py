#!/usr/bin/env python3
"""A sweep press refused because a box was up says so in the past.

Run 64, 2026-10-24: "(the sweep could NOT press VIRIDIANCITY_GAMBLER1: stuck
in a menu/dialog ...)" was the box up at that press (the private-property
script), read two rounds later as a box still open: the model tapped and
menu'd at a closed youngster box, text_on_screen false.

Pinned: that reason is said as "a box was up when it tried"; other reasons
are quoted as before.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

src = (ROOT / "planner" / "executor.py").read_text()
i = src.index('"(the sweep could NOT press "')
blk = src[i - 900:i + 300]
ck("a box-up refusal is said in the past",
   'if "stuck in a menu/dialog" in d:' in blk and 'return "a box was up when it tried"' in blk, blk[-500:])
ck("...other reasons are quoted as before", "return d[:120]" in blk)
ck("...and the line uses it", 'f"{n}: {_when(d)}"' in blk)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
