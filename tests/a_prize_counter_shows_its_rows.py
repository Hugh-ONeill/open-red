#!/usr/bin/env python3
"""A prize counter shows its rows, and is not a yes/no.

Run 47, Game Corner prize room (2026-10-11): the counter is a table of
prizes with coin costs, `scalars` keeps no tables, and with a cursor and no
`items` it read as a yes/no question. The run learned it one press at a
time ("So, you want ABRA?", "So, you want NIDORINA?") while looking for a
SECRET KEY the counter does not sell. Probed on run 47's own save: the
press now stops with ui.rows ["1=ABRA (180 coins)", "2=CLEFAIRY (500
coins)", "3=NIDORINA (1200 coins)", "4=CANCEL"], is_choice false, nothing
bought.

Pinned: the rows come from wd.menu_rows in the item menus' numbering; a
prize screen is never is_choice in the observation, nor in the shim's own
choice test (interact stops at the list by its own branch).
Synthetic.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "harness/shim.lua").read_text()
checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


ck("the ui observation carries the prize rows", "o.ui.rows = wd.menu_rows(top)" in SRC)
fn = SRC[SRC.index("wd.menu_rows = function(top)"):]
fn = fn[:fn.index("\nend\n") + 5]
ck("...numbered as item rows are, with coin costs",
   '("%d=%s (%s coins)"):format(i' in fn)
ck("...and the CANCEL row", '("%d=CANCEL"):format(#rows + 1)' in fn)
ck("...and nothing for a screen without prizes",
   'type(top.prizes) ~= "table" then return nil end' in fn)
ck("a prize screen is never a yes/no in the observation",
   "if top.prizes then o.ui.is_choice = false end" in SRC)
# The interact's stop at the counter rested on the shim's choice test calling
# the list a yes/no, and so did the answer="yes" that took row 1 the next
# time (run 53, 2026-10-12). The stop is its own branch now
# (a_prize_list_is_never_pressed_blind), and the choice test agrees with
# the observation.
ck("the shim's own choice test excludes a prize list, as the observation does",
   "and t.items == nil and not t.prizes" in SRC
   and "opened a prize list" in SRC)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"{len(checks) - len(failed)}/{len(checks)} passed")
sys.exit(1 if failed else 0)
