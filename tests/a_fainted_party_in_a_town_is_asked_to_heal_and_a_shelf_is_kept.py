#!/usr/bin/env python3
"""Fainted members in a town with a Center are asked about; a shelf a buy
refusal names is kept, and the buy is asked again with it.

Run 27 walked out of Vermilion toward Route 12 with three of four Pokemon at
0 HP past a Center it had used, and three times the street buy asked for
POTION and REVIVE, walked into a mart that sells neither, and left with
nothing — the refusal named the shelf each time and nobody kept it (user,
2026-09-16: "it also keeps revolving its way into the shop but doesnt buy
anything despite a lack of potions and plenty of cash, its also not healing
its several fainting mons despite being in a city with a center").

Synthetic: a stubbed bridge and model; no game.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import executor as E          # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


class X(E.Executor):
    pass


def make(reply):
    ex = object.__new__(X)
    ex.model = "m"
    ex.logged, ex.sent = [], []
    ex.log = lambda k, **kw: ex.logged.append((k, kw))
    ex._save_memory = lambda: None
    ex._shelves, ex._shelf_reads, ex._cant_afford = {}, {}, {}
    ex.settle = lambda: None
    E.brock_probe.chat = lambda msgs, model: reply(msgs)
    return ex


PARTY = [{"species": "PIDGEOTTO", "level": 30, "hp": 0, "max_hp": 82},
         {"species": "GRAVELER", "level": 30, "hp": 0, "max_hp": 79},
         {"species": "IVYSAUR", "level": 30, "hp": 89, "max_hp": 89}]
STREET = {"mode": "overworld", "party": PARTY, "money": 13932, "bag": {},
          "map": {"id": "VERMILION_CITY", "outdoor": True, "warps": [
              {"x": 11, "y": 3, "dest": "VERMILION_POKECENTER", "seen": True,
               "reachable": True},
              {"x": 23, "y": 13, "dest": "VERMILION_MART", "seen": True,
               "reachable": True}]}}

# ---- the heal question ---------------------------------------------------
asked = []
ex = make(lambda msgs: (asked.append(msgs[-1]["content"])
                        or '{"why": "three have fainted", "heal": true}'))
ex._send_safe = lambda op, **kw: (ex.sent.append(op)
                                  or {"result": {"ok": True}})
ex._ask_heal_street(STREET, {"id": "reach_route_12", "goal_text": "Reach Route 12"})
ck("fainted members in a town with a seen Center are asked about",
   asked and "FAINTED: PIDGEOTTO, GRAVELER (2 of 3)" in asked[0]
   and "VERMILION_POKECENTER at 11,3" in asked[0])
ck("...and a yes sends the heal op", ex.sent == ["heal"])
ck("...logged as a heal, so the run's item ledger starts over",
   any(k == "heal_done" and kw.get("where") == "street" for k, kw in ex.logged))
asked.clear(); ex.sent.clear()
ex._ask_heal_street(STREET, {"id": "reach_route_12"})
ck("asked once per street visit", not asked and not ex.sent)

ex2 = make(lambda msgs: '{"why": "pressing on", "heal": false}')
ex2._send_safe = lambda op, **kw: (ex2.sent.append(op) or {"result": {"ok": True}})
ex2._ask_heal_street(STREET, {"id": "x"})
ck("a no heals nothing", ex2.sent == [])
healthy = dict(STREET, party=[dict(p, hp=p["max_hp"]) for p in PARTY])
ex3 = make(lambda msgs: (_ for _ in ()).throw(AssertionError("asked")))
ex3._send_safe = lambda op, **kw: {}
ck("nobody fainted, no question",
   ex3._ask_heal_street(healthy, {"id": "x"}) is healthy)
nodoor = {**STREET, "map": {**STREET["map"], "warps": [
    dict(STREET["map"]["warps"][0], seen=False)]}}
ck("a Center door never on screen, no question",
   ex3._ask_heal_street(nodoor, {"id": "x"}) is nodoor)
SRC = (ROOT / "planner/executor.py").read_text()
ck("the counter heal question is still its own, and both are asked",
   SRC.count("def _ask_heal(self, obs, sg):") == 1
   and "start = self._ask_heal(start, sg) or start" in SRC
   and "start = self._ask_heal_street(start, sg) or start" in SRC)

# ---- the shelf a refusal names -------------------------------------------
replies = ['{"why": "no potions", "buy": [{"item": "POTION", "count": 10}]}',
           '{"why": "super potions", "buy": [{"item": "SUPER_POTION", "count": 5}]}']
pages = []


def buy_reply(msgs):
    pages.append(msgs[-1]["content"])
    return replies.pop(0) if replies else '{"why": "x", "buy": []}'


ex4 = make(buy_reply)
ex4._policy_unmet = lambda obs: (["POTION"], [])
ex4._shop_street = lambda obs: STREET["map"]["warps"][1]


def buy_send(op, **kw):
    ex4.sent.append((op, kw))
    if kw.get("item") == "POTION":
        return {"result": {"ok": False, "detail": (
            "POTION is not on VERMILIONMART_CLERK's shelf, which holds: "
            "POKE_BALL, SUPER_POTION, ICE_HEAL, AWAKENING, PARLYZ_HEAL, REPEL")}}
    return {"result": {"ok": True, "detail": "bought"}}


ex4._send_safe = buy_send
ex4._ask_buy(STREET, {"id": "x"})
ck("the shelf a refusal names is kept for that mart",
   ex4._shelves.get("VERMILION_MART") == ["POKE_BALL", "SUPER_POTION",
                                          "ICE_HEAL", "AWAKENING",
                                          "PARLYZ_HEAL", "REPEL"])
ck("...the buy is asked again, and the second page shows the shelf",
   len(pages) == 2 and "SUPER_POTION" in pages[1])
ck("...and what the second answer asked for is bought",
   ("buy", {"item": "SUPER_POTION", "count": 5, "clerk": ""}) in ex4.sent)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
