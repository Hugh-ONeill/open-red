#!/usr/bin/env python3
"""A party menu over a fight whose Pokemon is still standing owes no pick,
and the policy never "switches" to the one already out.

Run 28 (2026-10-02, the new base): a menu over the fight reported the fight
with no `me`. The out-of-PP switch rule read "no moves shown" as "dry" and
switched to best_matchup, the Pokemon already out; the game said "already
out!" and left its party menu up; the executor read that menu, still with
no `me`, as a faint's forced pick and sent the same slot six times a fight,
a hundred times across BROCK's gym and ROUTE 3. Each pass logged an empty
fight_recap, and the event feed said "beat a trainer" for every one (user:
"something odd in the gym its trying to switch or get out of a switch",
"now its stuck again in a battle state").
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
sys.path.insert(0, str(ROOT / "tools"))
import battle_policy as P     # noqa: E402
import executor as E          # noqa: E402

checks = []
def ck(name, ok): checks.append((name, bool(ok)))

party = [{"species": "BULBASAUR", "hp": 41, "max_hp": 41, "level": 14,
          "types": ["GRASS", "POISON"], "moves": [{"id": "VINE_WHIP", "pp": 9}]},
         {"species": "PIKACHU", "hp": 34, "max_hp": 34, "level": 12,
          "types": ["ELECTRIC"], "moves": [{"id": "THUNDERSHOCK", "pp": 30}]}]
foe = {"species": "GEODUDE", "level": 12, "hp": 31, "maxhp": 33,
       "types": ["ROCK", "GROUND"], "moves": []}
me = {"species": "BULBASAUR", "level": 14, "hp": 41, "maxhp": 41, "slot": 1,
      "types": ["GRASS", "POISON"],
      "moves": [{"index": 1, "id": "VINE_WHIP", "pp": 9, "type": "GRASS", "power": 35}]}
spec = {"switch": [{"to": "best_matchup", "out_of_pp": True}]}

# 1. no moves shown is not out of PP
blind = {"mode": "battle", "party": party,
         "battle": {"kind": "trainer", "behind_a_menu": "ChoiceBox", "foe": foe}}
ck("the out-of-PP rule does not fire when no moves are shown",
   P.should_switch(blind, spec, {"turn": 3}) is None)

# 2. never to the slot already out, even when the species check cannot tell
dry = dict(me, moves=[dict(me["moves"][0], pp=0)], species=None)
o = {"mode": "battle", "party": party,
     "battle": {"kind": "trainer", "me": dry, "foe": foe}}
ck("a switch never names the slot the screen marks as out",
   P.should_switch(o, spec, {"turn": 3}) != 1)

# 3. a party menu over a standing Pokemon is not a forced pick
sent = []
standing = {"mode": "battle", "party": party,
            "battle": {"kind": "trainer", "behind_a_menu": "PartyMenu",
                       "me": me, "foe": foe}}
class Bridge:
    def send(self, op, **kw):
        sent.append((op, kw))
        return {"result": {"ok": True, "detail": "battle ended"},
                "mode": "overworld", "party": party}
    def obs(self):
        return {"mode": "overworld", "party": party}
E._run_policy({}, Bridge(), dict(standing), lambda k, **kw: None, 3,
              intent="fight")
ck("no pick_party is sent while the Pokemon out is standing",
   not any(op == "pick_party" for op, _ in sent))

# ...while a fainted one under the menu still owes its pick
sent.clear()
down = {"mode": "battle", "party": [dict(party[0], hp=0), party[1]],
        "battle": {"kind": "trainer", "behind_a_menu": "PartyMenu",
                   "me": dict(me, hp=0), "foe": foe}}
class Bridge2(Bridge):
    def send(self, op, **kw):
        sent.append((op, kw))
        return {"result": {"ok": True}, "mode": "overworld", "party": party}
E._run_policy({}, Bridge2(), dict(down), lambda k, **kw: None, 3, intent="fight")
ck("a fainted Pokemon under the menu still gets its replacement",
   [kw.get("slot") for op, kw in sent if op == "pick_party"] == [2])

# 4. the shim says who is out under a menu, and refuses the one already out
shim = (ROOT / "harness/shim.lua").read_text()
ck("the menu-over-a-fight branch reports both sides",
   "o.battle.me = battle_side(G, _bf.player, true)" in shim)
ck("battle_switch refuses the Pokemon already out before pressing anything",
   '.. " is already out"' in shim)

# 5. an unread fight is not a fight won
src = (ROOT / "planner/executor.py").read_text()
ck("a fight with no foe, no move and no loss is logged as unread",
   'self.log("fight_unread"' in src and "if not (parts or foes_seen or lost):" in src)

bad = [n for n, ok in checks if not ok]
for n, ok in checks: print(("ok  " if ok else "FAIL"), n)
sys.exit(1 if bad else 0)
