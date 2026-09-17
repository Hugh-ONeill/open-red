#!/usr/bin/env python3
"""A buy from a floor with no counter says it climbed, and is refused where
it stands once the counter it would climb to is on record without the item.

Run 27, 2026-09-17, Celadon Mart: "I will now check the service counter on
the 1st floor" -> the buy climbed to 2F (the lobby has no counter that
trades), was refused off CLERK1's shelf, and the run came back down to try
1F again, nine rounds (user: "its looping itself a bit because its trying
to buy from the service counter which brings it up to 2F automatically").

Pinned: the shim's refusal names the floor the buy left and that nothing
there trades; the executor refuses a lobby buy in place when the climbed-to
counter's shelf is on record without the item, and still lets a named
counter be walked to. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


shim = (ROOT / "harness/shim.lua").read_text()
buy = shim[shim.index("function OPS.buy(G, c)"):]
buy = buy[:buy.index("\nfunction OPS.", 10)]
ck("the shim remembers the floor a buy climbed from",
   "climbed_from = from_mid" in buy and "ow.map.id ~= from_mid" in buy)
ck("...and its refusal says so, before the shelf",
   '"no counter on " .. climbed_from .. " trades' in buy
   and buy.index("climbed_from\n        and") < buy.index("'s shelf, which holds: "))

ex = object.__new__(E.Executor)
ex._shelves = {"CELADON_MART_2F": ["GREAT_BALL", "SUPER_POTION", "REVIVE"]}
obs = {"map": {"id": "CELADON_MART_1F"}}
got = ex._buy_from_lobby_refusal(obs, {"op": "buy", "item": "FRESH_WATER", "count": 1})
ck("a lobby buy for a thing the climbed-to counter lacks is refused in place",
   got and got.startswith("buy(FRESH_WATER): REFUSED — no counter on CELADON_MART_1F trades")
   and "CELADON_MART_2F" in got and "GREAT_BALL, SUPER_POTION, REVIVE" in got, got)
ck("...a thing that counter sells is not",
   ex._buy_from_lobby_refusal(obs, {"op": "buy", "item": "REVIVE", "count": 1}) is None)
ck("...a named counter is still walked to",
   ex._buy_from_lobby_refusal(obs, {"op": "buy", "item": "FRESH_WATER", "count": 1,
                                    "clerk": "CELADONMART2F_CLERK2"}) is None)
ck("...a floor that is not a lobby is not touched",
   ex._buy_from_lobby_refusal({"map": {"id": "CELADON_MART_2F"}},
                              {"op": "buy", "item": "FRESH_WATER", "count": 1}) is None)
ex._shelves = {}
ck("...and no record, no refusal",
   ex._buy_from_lobby_refusal(obs, {"op": "buy", "item": "FRESH_WATER", "count": 1}) is None)
src = (ROOT / "planner/executor.py").read_text()
ck("the macro loop asks before every buy",
   "_lr = self._buy_from_lobby_refusal(obs, step)" in src
   and src.index("_lr = self._buy_from_lobby_refusal") < src.index('if op == "buy" and step.get("item") in self._cant_afford'))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:220]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
