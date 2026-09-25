#!/usr/bin/env python3
"""No balls with catches still ahead, or a stronger ball or heal on a shelf
the run has read, is a shop question, and the answer may sell the old.

Run of record 4, 2026-09-25: the last POKE_BALL went at 09:19, and from
09:56 to 10:02 the run met twenty-one ABRA on Route 24/25 with a
FIRE-or-PSYCHIC leg ahead, a mart in Cerulean and money in hand. The
street shop question fired only for a bag with no medicine (user: "i
thought we just added prompts for buying balls? ... buy best balls
available when catch targets still exist, maybe sell off older less
effective balls"; then: "we should do the same with potions/heals when
better is available, we can sell the old stuff and take the new").

Pinned: with catches ahead the street question fires at no more balls
than the catch reserve, or when the shelf sells a stronger ball than any
in the bag, and not otherwise; no catches ahead, no ball question; a
stronger heal on a read shelf asks too; the question names the catch
legs, the balls held, the ladders and what on the shelf is stronger, and
says why it is asked; an answer may sell, sales go first, and a sale of
something the bag does not hold sends nothing; both framings offer
selling. No game: a fake executor, the catch goals stubbed."""
from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E          # noqa: E402
import brock_probe            # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


GOALS = [{"pos": 14, "leg": "the party holds a FIRE or PSYCHIC type",
          "types": {"FIRE", "PSYCHIC"}, "species": set()}]
_goals = {"v": GOALS}
E.outline_ahead.catch_goals_ahead = lambda *a, **k: list(_goals["v"])


def street(bag, shelf=None):
    o = {"mode": "overworld", "money": 3000, "bag": dict(bag),
         "map": {"id": "CERULEAN_CITY", "outdoor": True, "objects": [],
                 "warps": [{"x": 25, "y": 25, "dest": "CERULEAN_MART",
                            "look": "door", "reachable": True, "seen": True}]},
         "party": [{"species": "IVYSAUR", "level": 24, "hp": 60, "max_hp": 70,
                    "types": ["GRASS", "POISON"]}]}
    return o


def fake(shelf=None, answer='{"why":"no","buy":[]}'):
    o = types.SimpleNamespace(sent=[], logged=[], model="stub",
                              _shelves={"CERULEAN_MART": list(shelf)} if shelf else {},
                              _shelf_reads={}, _cant_afford={})
    o._send_safe = lambda op, **kw: (o.sent.append((op, kw)) or
                                     {"result": {"ok": True, "detail": "done"}})
    o.settle = lambda: None
    o.log = lambda kind, **kw: o.logged.append((kind, kw))
    o._where = E.Executor._where
    o._clerk_here = E.Executor._clerk_here
    o._policy_unmet = E.Executor._policy_unmet
    o._policy_heal_line = types.MethodType(E.Executor._policy_heal_line, o)
    o._species_names = lambda: set()
    for k in ("BUY_SYS", "BUY_STREET_SYS", "BUY_MAX_ENTRIES", "BAG_SLOTS",
              "SHOP_COUNTER_FLOOR", "CATCH_AHEAD_RESERVE"):
        setattr(o, k, getattr(E.Executor, k))
    for k in ("_shop_street", "_ask_buy", "_ball_need", "_ball_lines",
              "_heal_upgrade", "_heal_lines"):
        setattr(o, k, types.MethodType(getattr(E.Executor, k), o))
    o.prompts = []

    def chat(msgs, model):
        o.prompts.append(msgs)
        return answer
    brock_probe.chat = chat
    return o


E.set_active_spec({"battle_items": [{"item": "heal", "hp_below": 0.3}]})
SG = {"id": "travel_to_vermilion", "goal_text": "Reach Vermilion City"}

o = fake()
o._ask_buy(street({"POTION": 3}), SG)
p = o.prompts[0][1]["content"] if o.prompts else ""
ck("medicine in the bag, no balls, catches ahead: the street asks", len(o.prompts) == 1)
ck("...naming the catch legs and the balls held",
   "CATCHES STILL AHEAD ON YOUR OUTLINE: leg 14: the party holds a FIRE or PSYCHIC type" in p
   and "BALLS IN YOUR BAG: none" in p, p[-600:])
ck("...the ladder, strongest last",
   "POKE_BALL < GREAT_BALL < ULTRA_BALL — a stronger ball catches more easily" in p)
ck("...and why it is asked", "WHY YOU ARE ASKED: what is below." in p)
o = fake()
o._ask_buy(street({"POTION": 3, "POKE_BALL": 5}), SG)
ck("more balls than the reserve and nothing stronger on the shelf: not asked",
   not o.prompts)
o = fake(shelf=["POKE_BALL", "GREAT_BALL", "SUPER_POTION"])
o._ask_buy(street({"SUPER_POTION": 3, "POKE_BALL": 5}), SG)
p = o.prompts[0][1]["content"] if o.prompts else ""
ck("a stronger ball on the read shelf asks, and says which",
   "ON THIS SHELF, STRONGER THAN ANY BALL YOU CARRY: GREAT_BALL" in p, p[-500:])
_goals["v"] = []
o = fake()
o._ask_buy(street({"POTION": 3}), SG)
ck("no catches ahead: no ball question", not o.prompts)
o = fake(shelf=["POTION", "SUPER_POTION"])
o._ask_buy(street({"POTION": 3}), SG)
p = o.prompts[0][1]["content"] if o.prompts else ""
ck("a stronger heal on the read shelf asks, catches or not",
   "HEALING IN YOUR BAG: POTION x3" in p
   and "ON THIS SHELF, STRONGER THAN ANY HEAL YOU CARRY: SUPER_POTION" in p
   and "POTION < SUPER_POTION" in p, p[-500:])
o = fake(shelf=["POTION", "SUPER_POTION"])
o._ask_buy(street({"SUPER_POTION": 2}), SG)
ck("...and not when the bag already holds the strongest it sells", not o.prompts)

_goals["v"] = GOALS
o = fake(shelf=["POKE_BALL", "GREAT_BALL"], answer=(
    '{"why":"trade up","sell":[{"item":"POKE_BALL","count":5},'
    '{"item":"ULTRA_BALL","count":1}],"buy":[{"item":"GREAT_BALL","count":4}]}'))
o._ask_buy(street({"POTION": 1, "POKE_BALL": 5}), SG)
ck("an answer may sell, and the sale goes before the buy",
   [op for op, _ in o.sent] == ["sell", "buy"]
   and o.sent[0][1]["item"] == "POKE_BALL" and o.sent[0][1]["count"] == 5
   and o.sent[1][1]["item"] == "GREAT_BALL", o.sent)
ck("...and a sale of something the bag does not hold sends nothing",
   not any(kw.get("item") == "ULTRA_BALL" for _, kw in o.sent))
ck("both framings offer selling",
   '"sell"' in E.Executor.BUY_STREET_SYS and '"sell"' in E.Executor.BUY_SYS)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
