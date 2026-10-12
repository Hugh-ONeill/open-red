#!/usr/bin/env python3
"""{"has_item": {"COIN": n}} is read off the Coin Case's count, not the bag.

COIN is an item id this game defines, so the validator passed run 53's
"gamble_for_coins: has_item COIN 2000" and "buy_coins" steps; but coins are
their own field in the observation and no bag ever holds COIN, so those steps
could only be carried past, never met (2026-10-12).
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
import types  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


bag = {"COIN_CASE": 1, "POKE_BALL": 6}
ck("2000 coins meets COIN 2000", E.pred_holds({"has_item": {"COIN": 2000}},
                                             {"bag": bag, "coins": 2000}))
ck("190 coins does not", not E.pred_holds({"has_item": {"COIN": 2000}},
                                          {"bag": bag, "coins": 190}))
ck("no coin count reads as none", not E.pred_holds({"has_item": {"COIN": 1}}, {"bag": bag}))
ck("the string and list shapes read the same way",
   E.pred_holds({"has_item": "COIN"}, {"bag": bag, "coins": 5})
   and E.pred_holds({"has_item": ["COIN", "COIN_CASE"]}, {"bag": bag, "coins": 5}))
ck("an item beside COIN is still read off the bag",
   not E.pred_holds({"has_item": {"COIN": 10, "SECRET_KEY": 1}}, {"bag": bag, "coins": 50}))
ck("other items are unchanged",
   E.pred_holds({"has_item": {"POKE_BALL": 6}}, {"bag": bag, "coins": 0})
   and not E.pred_holds({"has_item": {"POKE_BALL": 7}}, {"bag": bag, "coins": 0}))

# THE SAME COUNT, IN WHAT WAS SAID. "A COIN CASE is required!" also named COIN
# (each name searched the whole sentence), and COIN was looked for in the bag.
X = E.Executor
f = types.SimpleNamespace(NEED_WORDS=X.NEED_WORDS, _item_word_patterns=X._item_word_patterns,
                          _same_kind_held=lambda nm, b: "")
case = ['interact(name=V): it said: "A COIN CASE is required!"']
ck("a COIN CASE demand with the case held says nothing",
   X._spoken_item_note(f, case, {"bag": {"COIN_CASE": 1}, "coins": 90}) == "")
w = X._spoken_item_note(f, case, {"bag": {"POTION": 1}, "coins": 0})
ck("...without it names the COIN_CASE alone", "COIN_CASE" in w and "of COIN," not in w, w)
need = ['interact(name=S): it said: "You need some COINS to play!"']
ck("a demand for coins with none counted names COIN",
   "spoke of COIN," in X._spoken_item_note(f, need, {"bag": {"COIN_CASE": 1}, "coins": 0}))
ck("...and with coins counted says nothing",
   X._spoken_item_note(f, need, {"bag": {"COIN_CASE": 1}, "coins": 50}) == "")
ck("the CARD KEY demand still names CARD_KEY",
   "CARD_KEY" in X._spoken_item_note(f, ['it said: "Darn! It needs a CARD KEY!"'],
                                     {"bag": {"LIFT_KEY": 1}, "coins": 0}))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
