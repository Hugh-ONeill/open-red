#!/usr/bin/env python3
"""A prize handed over is not something that refused you for want of it.

Run 58 (2026-10-17): Route 24's Rocket said "PIXEL received a NUGGET! / By
the way, would you like to join TEAM ROCKET? ..." and a demand word later in
the speech made the whole hint read as a refusal: "something shut there
refused for want of NUGGET, which your bag holds NOW". The model went back
to Route 24 to trade the Nugget for HM CUT. The demand and the item must
share a sentence, and a sentence that hands something over is not a demand.

Synthetic.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(name, ok, d=""): checks.append((name, bool(ok), d))

x = object.__new__(E.Executor)
x.hints = {
    "ROUTE_24|4,4": ["someone: Congratulations! You beat our 5 contest trainers! / You just "
                     "earned a fabulous prize! / PIXEL received a NUGGET! / By the way, would "
                     "you like to join TEAM ROCKET? We're a group dedicated to evil using "
                     "POKeMON! Want to join? Are you sure? Come on, join us! You must join!"],
    "SILPH_CO_3F|1,1": ["someone: Darn! It needs a CARD KEY!"],
    "GIFT|0,0": ["someone: You must be tired. You obtained a NUGGET!"],
}
r = x._shut_asked_for_held("ROUTE_24|4,4", {"bag": {"NUGGET": 1}})
ck("the Rocket's prize speech is not a refusal for want of the prize", r == "", r)
r = x._shut_asked_for_held("SILPH_CO_3F|1,1", {"bag": {"CARD_KEY": 1}})
ck("a lock that asks for a key still says so", "CARD_KEY" in r, r)
r = x._shut_asked_for_held("GIFT|0,0", {"bag": {"NUGGET": 1}})
ck("a sentence that hands an item over is not a demand for it", r == "", r)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
