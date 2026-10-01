#!/usr/bin/env python3
"""use_item uses the item ONCE, and says what it did from the party, not the words.

After an item acted, the game put the party menu back up with the item in hand
and the op's A press used it again: one use_item POTION on a DUGTRIO at 20/101
spent all five POTIONs, and a REVIVE's second press on the now-standing
KADABRA is where "NOTHING HAPPENED — It won't have any effect" came from while
the bag was one lighter and KADABRA at 56/112 (Bruno's room's MAX_REVIVE; both
reproduced live 2026-09-30 on a Silph save, and after the fix: POTION 5->4->3
at +20 each, REVIVE 0->56, a stone evolution and a TM teach with forget=
unchanged, a revive on a standing member still reported as no effect).

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
ck("the target and the bag are read before the item is chosen",
   ui.index("local _pre = party[slot]") < ui.index('ui_cursor_to(G, "index", slot)')
   and "local _n_pre = bag_count(G, c.item)" in ui)
loop = ui[ui.index("while true do"):ui.index("ui_back_out(G)\n  -- ...AND IF IT IS STILL UP")]
ck("the loop stops once the item has acted and a menu is back",
   'if t and (t.screenId == "PartyMenu" or (t.items and not t.pages))' in loop
   and "bag_count(G, c.item) < _n_pre" in loop and "break" in loop)
ck("...before any A is pressed on that menu",
   loop.index("ONE USE PER OP") < loop.index('U.tap(G, "a")'))
ck("...but not in the middle of a teach's forget list", "and not t.newMoveId" in loop)
ne = ui[ui.index("-- ...AND ONLY WHEN THE POKEMON AND THE BAG AGREE."):]
ck("a no-effect message is believed only when the party and the bag did not move",
   ne.index('return true, ("used %s on %s:%s HP %d -> %d%s")')
   < ne.index('" and NOTHING HAPPENED — the game said'))
ck("a use that worked says what it did to whom",
   ui.count('("used %s on %s:%s HP %d -> %d%s")') == 2
   and ui.count('(mon.level ~= _pre.level) and (" L"') == 2)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
