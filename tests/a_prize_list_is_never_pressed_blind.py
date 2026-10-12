#!/usr/bin/env python3
"""A prize counter's list is left open with its rows said, never pressed blind.

Run 53 (2026-10-12): at the Game Corner prize counter the run chose CANCEL
(menu index=4) and sent interact answer="yes" to open the counter again.
interact had read "Which prize do you want?" the round before, its
ui_is_choice() still called the prize list a yes/no (the observation had
stopped doing so, top.prizes), and "yes" pressed A on row 1: an ABRA for 180
coins nobody chose. Reproduced on a run 53 save in the prize room with 2040
coins: unpatched, the second interact reached "So, you want ABRA?"; with only
the yes/no test fixed, the first interact pressed through to the ABRA; now
both interacts answer "opened a prize list: 1=ABRA (180 coins), ...,
4=CANCEL ... left OPEN", coins and box unchanged.

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
ch = sh[sh.index("local function ui_is_choice(G)"):]
ch = ch[:ch.index("\nend") + 4]
ck("the shim's yes/no test does not take a prize list", "not t.prizes" in ch, ch)
it = sh[sh.index("function OPS.interact(G, c)"):]
it = it[:it.index("\nfunction OPS.", 10)]
i_pr = it.index("if t and type(t.prizes) == \"table\" then")
ck("interact stops at a prize list and says its rows",
   "opened a prize list" in it and "wd.menu_rows(t)" in it[i_pr:i_pr + 900])
ck("...before the A that would take the top row",
   i_pr < it.index('if t == ow then return true end', i_pr - 2000 if i_pr > 2000 else 0)
   and i_pr < it.index("if ui_is_choice(G) then", i_pr))
ck("...beside the rule that leaves any other list open",
   it.index("ANY OTHER LIST IS A CHOICE") < i_pr)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
