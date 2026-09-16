#!/usr/bin/env python3
"""A shop you have seen is a walk from the street, and nothing more.

Three changes (user, 2026-09-16: "make buy work the way heal does so
buying in a town just directs you to the mart if youve seen the mart
already ... celadon defaults to 2F clerk1"):
  * the shim's shop walk only goes through a door that has been on screen,
    the rule OPS.heal already keeps; it used to read an unvisited map and
    walk the body in, the one place the harness read ahead of the walk;
  * in Celadon the street door is a lobby with a receptionist, so the walk
    climbs to 2F and a buy or sell that names no clerk trades with
    CELADONMART2F_CLERK1;
  * the buy question, which only ever fired beside a counter, is also
    asked in a town street when a seen shop door is in reach and the bag
    holds no rung of the heal ladder. A yes walks in.
No game here: the executor side runs against a fake, the shim side is
read from its source.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E          # noqa: E402
import brock_probe            # noqa: E402

checks = []


def ck(n, ok):
    checks.append((n, bool(ok)))


def street(bag=None, money=1500, seen=True, reachable=True, dest="PEWTER_MART",
           outdoor=True, mode="overworld", map_id="PEWTER_CITY", extra=None):
    warps = [{"x": 11, "y": 17, "dest": "PEWTER_POKECENTER", "look": "door",
              "reachable": True, "seen": True},
             {"x": 23, "y": 17, "dest": dest, "look": "door",
              "reachable": reachable, "seen": seen}] + list(extra or [])
    return {"mode": mode, "money": money, "bag": dict(bag or {}),
            "map": {"id": map_id, "outdoor": outdoor, "objects": [], "warps": warps},
            "party": [{"species": "CHARMANDER", "level": 12, "hp": 20, "max_hp": 35}]}


def fake(answer='{"why":"no potions and Brock is next","buy":[{"item":"POTION","count":3}]}'):
    o = types.SimpleNamespace(sent=[], logged=[], model="stub", _shelves={}, _shelf_reads={},
                              _cant_afford={})
    o._send_safe = lambda op, **kw: (o.sent.append((op, kw)) or
                                     {"result": {"ok": True, "detail": "bought"}})
    o.settle = lambda: None
    o.log = lambda kind, **kw: o.logged.append((kind, kw))
    o._where = E.Executor._where
    o._clerk_here = E.Executor._clerk_here
    o._policy_unmet = E.Executor._policy_unmet
    o._policy_heal_line = types.MethodType(E.Executor._policy_heal_line, o)
    for k in ("BUY_SYS", "BUY_STREET_SYS", "BUY_MAX_ENTRIES", "BAG_SLOTS", "SHOP_COUNTER_FLOOR"):
        setattr(o, k, getattr(E.Executor, k))
    o._shop_street = types.MethodType(E.Executor._shop_street, o)
    o._ask_buy = types.MethodType(E.Executor._ask_buy, o)
    o.prompts = []
    def chat(msgs, model):
        o.prompts.append(msgs)
        return answer
    brock_probe.chat = chat
    return o


E.set_active_spec({"battle_items": [{"item": "heal", "hp_below": 0.3}]})
SG = {"id": "defeat_brock", "goal_text": "Defeat Brock"}

# ---- the street question fires, and a yes walks in -----------------------
o = fake()
o._ask_buy(street(), SG)
ck("in a town with a seen mart door and no healing in the bag, the question is asked",
   len(o.prompts) == 1)
ck("...with the street's own framing", o.prompts and o.prompts[0][0]["content"] == E.Executor.BUY_STREET_SYS)
ck("...naming the door it would walk to",
   o.prompts and "THE SHOP: the door into PEWTER_MART at 23,17" in o.prompts[0][1]["content"])
ck("a yes sends a buy with no clerk named, which the shim walks in for",
   o.sent == [("buy", {"item": "POTION", "count": 3, "clerk": ""})])
ck("the question is logged as asked from the street",
   any(k == "buy_asked" and kw.get("where") == "street" for k, kw in o.logged))

# ---- once per visit ------------------------------------------------------
o._ask_buy(street(), SG)
ck("asked once per visit to the street, not every round", len(o.prompts) == 1)
o._ask_buy({"mode": "overworld", "money": 1500, "bag": {}, "map": {"id": "PEWTER_POKECENTER", "outdoor": False, "objects": [], "warps": []}, "party": []}, SG)
o._ask_buy(street(), SG)
ck("...and again after the party has been somewhere else and come back", len(o.prompts) == 2)

# ---- the gates -----------------------------------------------------------
for name, obs in [
    ("a bag with a Potion in it", street(bag={"POTION": 1})),
    ("a bag with any rung of the heal ladder", street(bag={"HYPER_POTION": 2})),
    ("a shop door never on screen", street(seen=False)),
    ("a shop door a walk cannot reach", street(reachable=False)),
    ("no money", street(money=0)),
    ("indoors", street(outdoor=False)),
    ("not in the overworld", street(mode="battle")),
    ("a street with no mart", street(dest="PEWTER_MUSEUM_1F")),
]:
    f = fake()
    f._ask_buy(obs, SG)
    ck(f"not asked with {name}", not f.prompts and not f.sent)

f = fake()
f._ask_buy(street(bag={"POKE_BALL": 5, "ANTIDOTE": 1}), SG)
ck("balls and cures are not healing: still asked", len(f.prompts) == 1)

# ---- Celadon: the lobby door, the 2F counter -----------------------------
f = fake()
f._shelves = {"CELADON_MART_2F": ["GREAT_BALL", "SUPER_POTION", "REVIVE"]}
cel = street(map_id="CELADON_CITY", dest="CELADON_MART_5F",
             extra=[{"x": 10, "y": 13, "dest": "CELADON_MART_1F", "look": "door",
                     "reachable": True, "seen": True}])
f._ask_buy(cel, SG)
body = f.prompts[0][1]["content"] if f.prompts else ""
ck("in Celadon the lobby door is offered, not the 5F warp",
   "the door into CELADON_MART_1F at 10,13" in body)
ck("...and the question says it is the first counter on the second floor",
   "first counter on the second floor" in body)
ck("...with the shelf that counter was seen to sell, filed under 2F",
   "WHAT IT WAS SEEN TO SELL: GREAT_BALL, SUPER_POTION, REVIVE" in body)

# ---- the counter question beside a clerk is unchanged ---------------------
f = fake()
f._ask_buy({"mode": "overworld", "money": 900, "bag": {"POTION": 2},
            "map": {"id": "PEWTER_MART", "outdoor": False, "warps": [],
                    "objects": [{"name": "PEWTERMART_CLERK", "reachable": True}]},
            "party": []}, SG)
ck("beside a counter the question is still asked, with healing in the bag",
   len(f.prompts) == 1 and f.prompts[0][0]["content"] == E.Executor.BUY_SYS
   and f.sent and f.sent[0][1]["clerk"] == "PEWTERMART_CLERK")

# ---- the shim --------------------------------------------------------------
SH = (ROOT / "harness/shim.lua").read_text()
es = SH[SH.index("local function enter_shop(G)"):SH.index("local UNSEEN_SHOP")]
ck("the shop walk only goes through a door that has been on screen",
   'seen[w.x .. "," .. w.y]' in es and 'return false, unseen and "unseen" or nil' in es)
ck("Celadon's lobby climbs to 2F", 'CELADON_MART_1F = { floor = "CELADON_MART_2F"' in SH
   and "climb_to_counter" in es)
ck("a lobby door is preferred over any other shop door on the street",
   "local cands = (#via > 0) and via or plain" in es)
ck("a buy or sell that names no clerk on 2F trades with CLERK1",
   'DEFAULT_CLERK = { CELADON_MART_2F = "CELADONMART2F_CLERK1" }' in SH
   and SH.count("pick_clerk(ow, wanted_clerk(ow, c))") == 4)
ck("both buy and sell say so when the shop door has never been on screen",
   SH.count('if shop_why == "unseen" then return false, UNSEEN_SHOP end') == 2)
ck("the door hint names only a door that has been on screen",
   '_seen[w.x .. "," .. w.y]' in SH[SH.index("local function shop_door_hint(G)"):SH.index("local function shop_door_hint(G)") + 1200])
ck("each published door says whether it has been on screen",
   "seen = ((SEEN[map.id] or {})[w.x .. \",\" .. w.y])" in SH)

# THE SHOP MUST BE UNDER THE PARTY BEFORE ITS CLERK IS PRESSED (run 27,
# 2026-09-16: "couldn't reach PEWTERMART_CLERK — no tile beside (0,5)... it
# is fenced in", the clerk's shop cell read against the street's tiles)
_es = SH[SH.index("local function enter_shop(G)"):]
_es = _es[:_es.index("\nlocal UNSEEN_SHOP")]
_cc = SH[SH.index("local function climb_to_counter(G, mid)"):]
_cc = _cc[:_cc.index("\nend\n")]
ck("walking into a shop waits for the shop floor before anything is pressed",
   "local function settle_off(G, from)" in SH
   and _es.index("OPS.use_warp") < _es.index("settle_off(G, mid)")
   < _es.index("climb_to_counter(G, w.destMap)"))
ck("...and so does the climb to a counter upstairs",
   "settle_off(G, mid)" in _cc)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
