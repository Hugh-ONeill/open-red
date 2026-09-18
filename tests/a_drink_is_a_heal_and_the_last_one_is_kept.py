#!/usr/bin/env python3
"""The drinks are heals, and while a thirsty gate is on the record the last
of each is not spent by a rule.

2026-09-18: FRESH_WATER, SODA_POP and LEMONADE restore 50, 60 and 80 HP
(the engine's ItemEffects), but the heal ladder held only the potions, so
the two FRESH_WATERs the run carried were invisible to every heal rule
(user: "should we count freshwater/sodapop/lemonade as healing items?
because they are, they just also have a story purpose").

Pinned: the drinks sit in the heal ladder and amount table by what they
restore; a heal rule reaches for one; the executor holds the last of each
back while an uncleared blocker said it was thirsty, and not otherwise.
Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as bp  # noqa: E402
import executor as E        # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


L = bp.HEAL_LADDER
ck("the drinks are on the heal ladder, ordered by what they restore",
   L.index("POTION") < L.index("FRESH_WATER") < L.index("SODA_POP") < L.index("LEMONADE") < L.index("HYPER_POTION"))
ck("...with their amounts", bp.HEAL_AMOUNT["FRESH_WATER"] == 50 and bp.HEAL_AMOUNT["SODA_POP"] == 60
   and bp.HEAL_AMOUNT["LEMONADE"] == 80)


def fight(bag, hp=40):
    bp.reset_run_budget()
    o = {"mode": "battle", "bag": dict(bag),
         "party": [{"species": "LAPRAS", "level": 43, "hp": hp, "max_hp": 185},
                   {"species": "KADABRA", "level": 52, "hp": 100, "max_hp": 118}],
         "battle": {"kind": "trainer", "partyIndex": 0, "enemyIndex": 0,
                    "me": {"species": "LAPRAS", "level": 43, "hp": hp, "maxhp": 185, "types": ["WATER"],
                           "moves": [{"index": 1, "id": "SURF", "type": "WATER", "power": 95, "pp": 15}]},
                    "foe": {"species": "RATICATE", "level": 40, "hp": 90, "maxhp": 90, "types": ["NORMAL"], "moves": []}}}
    spec = dict(bp.DEFAULT_SPEC, name="t", battle_items=[{"item": "heal", "hp_below": 0.4, "max_uses": 3}])
    return bp.choose(o, spec, {"turn": 1, "intent": "traversal"})


bp.HOLD_LAST.clear()
r = fight({"FRESH_WATER": 2})
ck("a heal rule reaches for a drink when that is what the bag holds",
   r.get("op") == "battle_item" and r.get("item") == "FRESH_WATER", r)
bp.HOLD_LAST.update(bp.DRINKS)
r = fight({"FRESH_WATER": 2})
ck("with the last one held, one of two can still be spent", r.get("item") == "FRESH_WATER", r)
r = fight({"FRESH_WATER": 1})
ck("...but not the last one", r.get("op") != "battle_item", r)
ck("spendable() takes one of each held item out and leaves the rest",
   bp.spendable({"FRESH_WATER": 1, "SODA_POP": 3, "POTION": 2}) == {"SODA_POP": 2, "POTION": 2})
bp.HOLD_LAST.clear()

ex = object.__new__(E.Executor)
ex.blockers = {"ROUTE_6_GATE|3,0|3,0": {"what": "\"I'm on guard duty. Gee, I'm thirsty, though!\"", "cleared": False}}
ex._hold_drinks()
ck("an uncleared thirsty blocker holds the last drink of each kind", bp.HOLD_LAST == set(bp.DRINKS))
ex.blockers["ROUTE_6_GATE|3,0|3,0"]["cleared"] = True
ex._hold_drinks()
ck("...and a cleared one releases them", bp.HOLD_LAST == set())
src = (ROOT / "planner/executor.py").read_text()
ck("the hold is set before every battle", "        self._hold_drinks()\n        _ahead = self._catch_ahead(" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:240]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
