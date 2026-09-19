#!/usr/bin/env python3
"""The battle policy's `train` block decides how a level step's trainee
meets a wild: it fights for itself, hands the fight over and keeps its
share, or runs.

Until 2026-09-19 the harness owned this with one constant: in a slot_level
step it switched the trainee IN on turn one of every wild battle (5,128
times across the runs), the weak member eating the free hit. Two tactics
are each right in different fights (user): a trainee that would lose leads
and switches OUT on turn one, still earning its share; a trainee that wins
cleanly just fights, with no wasted turn, no split and no switch-in hit.

Pinned: the block validates; the plan names the trainee (slot_level pinned
to the Pokemon, lead_level, the lowest of party_min_level); a trainee in
front that passes fight_if is left to the ordinary rules; one that fails
goes out to the named order or runs; its HP falling under min_hp_frac
mid-fight sends it out too; a trainee not in front is brought in only for
a wild it can take; a trainer battle is never a training battle; the
policy loop sends the switch; a spec with no block keeps the old
switch-in. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as bp  # noqa: E402
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def mon(sp, lv, hp, mx, types, moves, **kw):
    return dict({"species": sp, "level": lv, "hp": hp, "max_hp": mx,
                 "types": types,
                 "moves": [{"index": i + 1, "id": m, "type": t, "power": pw,
                            "pp": 20}
                           for i, (m, t, pw) in enumerate(moves)]}, **kw)


MACHOP = mon("MACHOP", 24, 70, 74, ["FIGHTING"],
             [("KARATE_CHOP", "NORMAL", 50), ("LOW_KICK", "FIGHTING", 50)])
LAPRAS = mon("LAPRAS", 55, 240, 250, ["WATER", "ICE"],
             [("SURF", "WATER", 95), ("ICE_BEAM", "ICE", 95)])
PIDGEOT = mon("PIDGEOT", 52, 160, 170, ["NORMAL", "FLYING"],
              [("WING_ATTACK", "FLYING", 35)])


def battle(party, out, foe, kind="wild"):
    me = dict(party[out - 1])
    me["maxhp"] = me.pop("max_hp")
    me["slot"] = out
    return {"mode": "battle", "party": party,
            "battle": {"kind": kind, "me": me, "foe": foe}}


GEODUDE = {"species": "GEODUDE", "level": 24, "hp": 60, "maxhp": 60,
           "types": ["ROCK", "GROUND"]}
GOLBAT = {"species": "GOLBAT", "level": 40, "hp": 120, "maxhp": 120,
          "types": ["POISON", "FLYING"]}

HYBRID = {"train": {"lead": True,
                    "fight_if": {"min_level_ratio": 0.9, "min_hp_frac": 0.5},
                    "else": "switch", "to": "highest_level"}}

# ------------------------------------------------------------ validation
ck("a train block validates", bp.validate_spec(HYBRID) == [])
ck("...null is no block", bp.validate_spec({"train": None}) == [])
bad = bp.validate_spec({"train": {"lead": 1, "else": "hide",
                                  "fight_if": {"min_lvl": 1},
                                  "to": 3, "who": "MACHOP"}})
ck("...and a bad one says each thing wrong with it", len(bad) == 5, bad)
ck("the seed spec has no block", bp.DEFAULT_SPEC.get("train") is None)

# ---------------------------------------------------- the plan names who
party = [LAPRAS, PIDGEOT, MACHOP]
ck("a slot condition names its slot",
   E.trainee_of({"slot_level": {"slot": 3, "min": 30}}, party) == (3, 30))
pinned = {"slot_level": {"slot": 1, "min": 30,
                         "who": {"species": "MACHOP", "dvs": {"hp": 3},
                                 "otId": 9}}}
p2 = [LAPRAS, PIDGEOT, dict(MACHOP, dvs={"hp": 3}, otId=9)]
ck("...a pinned one follows the Pokemon", E.trainee_of(pinned, p2) == (3, 30))
ck("...and one already there names nobody",
   E.trainee_of({"slot_level": {"slot": 3, "min": 20}}, party) == (None, None))
ck("a lead condition is whoever is in front",
   E.trainee_of({"lead_level": 60}, party) == (1, 60))
ck("every-member-at-least is waiting on the lowest still short",
   E.trainee_of({"party_min_level": 53}, party) == (3, 53))
ck("...never a fainted one",
   E.trainee_of({"party_min_level": 53},
                [LAPRAS, dict(PIDGEOT), dict(MACHOP, hp=0)]) == (2, 53))
ck("a place step has no trainee",
   E.trainee_of({"map": "ROUTE_1"}, party) == (None, None))

# --------------------------------------------------------- the decision
led = [MACHOP, LAPRAS, PIDGEOT]
ctx = {"trainee": 1, "turn": 1}
ck("a trainee that can take the wild is left to fight it",
   bp.train_turn(battle(led, 1, GEODUDE), HYBRID, ctx) is None)
ctx = {"trainee": 1, "turn": 1}
r = bp.train_turn(battle(led, 1, GOLBAT), HYBRID, ctx)
ck("one that cannot goes out to the named order",
   r and r["do"] == "switch" and r["slot"] == 2, r)
ck("...and the reason says what failed", r and "L24 against L40" in r["why"], r)
r2 = bp.train_turn(battle(led, 2, GOLBAT), HYBRID, dict(ctx, turn=2))
ck("...after which it has its share and the fight just ends", r2 is None, r2)
hurt = [dict(MACHOP, hp=30), LAPRAS, PIDGEOT]
r = bp.train_turn(battle(hurt, 1, GEODUDE), HYBRID, {"trainee": 1, "turn": 3})
ck("its HP falling under the floor mid-fight sends it out too",
   r and r["do"] == "switch" and "hp" in r["why"], r)
FLEE = {"train": {"lead": True, "fight_if": {"min_level_ratio": 0.9},
                  "else": "flee"}}
r = bp.train_turn(battle(led, 1, GOLBAT), FLEE, {"trainee": 1, "turn": 1})
ck("else flee runs instead", r and r["do"] == "flee", r)
NEVER = {"train": {"lead": True, "fight_if": False}}
r = bp.train_turn(battle(led, 1, GEODUDE), NEVER, {"trainee": 1, "turn": 1})
ck("fight_if false never fights, whatever walks out",
   bp.validate_spec(NEVER) == [] and r and r["do"] == "switch", r)
PLOW = {"train": {"lead": True}}
ck("no fight_if means it fights everything",
   bp.train_turn(battle(led, 1, GOLBAT), PLOW, {"trainee": 1, "turn": 1}) is None)
MATCH = {"train": {"lead": True, "fight_if": {"min_matchup": 2}}}
ck("a matchup condition reads the moves it holds",
   bp.train_turn(battle(led, 1, GEODUDE), MATCH, {"trainee": 1, "turn": 1}) is None
   and (bp.train_turn(battle(led, 1, GOLBAT), MATCH,
                      {"trainee": 1, "turn": 1}) or {}).get("do") == "switch")
SEEN = {"train": {"fight_if": {"seen_ko_hits": 2}}}
jr = {bp.journal_key("LOW_KICK", "GEODUDE", 24): [33, 40]}
ck("a seen-damage condition reads the journal",
   bp.train_turn(battle(led, 1, GEODUDE), SEEN,
                 {"trainee": 1, "turn": 1, "journal": jr}) is None
   and (bp.train_turn(battle(led, 1, GEODUDE), SEEN,
                      {"trainee": 1, "turn": 1, "journal": {}}) or {}
        ).get("do") == "switch")
# not in front
bench = [LAPRAS, PIDGEOT, MACHOP]
r = bp.train_turn(battle(bench, 1, GEODUDE), HYBRID, {"trainee": 3, "turn": 1})
ck("a trainee on the bench is brought in for a wild it can take",
   r and r["do"] == "bring" and r["slot"] == 3, r)
ck("...and left there for one it cannot",
   bp.train_turn(battle(bench, 1, GOLBAT), HYBRID,
                 {"trainee": 3, "turn": 1}) is None)
ck("...and never after the first turn",
   bp.train_turn(battle(bench, 1, GEODUDE), HYBRID,
                 {"trainee": 3, "turn": 2}) is None)
ck("a trainer battle is never a training battle",
   bp.train_turn(battle(led, 1, GOLBAT, kind="trainer"), HYBRID,
                 {"trainee": 1, "turn": 1}) is None)
ck("a fainted trainee has nothing decided for it",
   bp.train_turn(battle([dict(MACHOP, hp=0), LAPRAS], 2, GOLBAT), HYBRID,
                 {"trainee": 1, "turn": 1}) is None)
ck("no block, no say",
   bp.train_turn(battle(led, 1, GOLBAT), {"train": None},
                 {"trainee": 1, "turn": 1}) is None)
solo = [MACHOP]
ck("nobody to hand over to: it fights",
   bp.train_turn(battle(solo, 1, GOLBAT), HYBRID,
                 {"trainee": 1, "turn": 1}) is None)
old_obs = battle(led, 1, GOLBAT)
old_obs["battle"]["me"].pop("slot")
ck("an observation without the slot is matched on what both screens show",
   bp.active_slot(old_obs) == 1)


# -------------------------- the ordinary switch rule reaches a wild too
# (TODO 2026-09-18: "check only_if_lead and vs: wild actually fire")
WILD_RULE = {"switch": [{"to": 2, "vs": "wild", "only_if_lead": 1}]}
ck("a switch rule written for wilds fires in a wild battle",
   bp.should_switch(battle(led, 1, GOLBAT), WILD_RULE,
                    {"turn": 1, "started_as": 1}) == 2)
ck("...only for the lead it names",
   bp.should_switch(battle(led, 1, GOLBAT), WILD_RULE,
                    {"turn": 1, "started_as": 3}) is None)
ck("...and never against a trainer",
   bp.should_switch(battle(led, 1, GOLBAT, kind="trainer"), WILD_RULE,
                    {"turn": 1, "started_as": 1}) is None)

# ------------------------------------------------ the loop sends the switch
class Bridge:
    def __init__(self, first):
        self.cur, self.sent = first, []

    def send(self, op, **kw):
        self.sent.append((op, kw))
        if op == "battle_switch":
            self.cur = battle(led, kw["slot"], GOLBAT)
            return dict(self.cur, result={"ok": True})
        self.cur = {"mode": "overworld", "party": led}
        return dict(self.cur, result={"ok": True})

    def obs(self):
        return self.cur


E.SCORE_BATTLES = False
rows = []
b = Bridge(battle(led, 1, GOLBAT))
E._run_policy(dict(bp.DEFAULT_SPEC, **HYBRID), b, b.cur,
              lambda k, **kw: rows.append((k, kw)), 20, trainee=1)
ck("the policy loop sends the trainee out on turn one",
   b.sent and b.sent[0] == ("battle_switch", {"slot": 2}), b.sent[:2])
ck("...logged as a train switch",
   any(k == "battle_turn" and kw.get("train") == "switch" for k, kw in rows))
ck("...and then plays the fight with who came in",
   len(b.sent) > 1 and b.sent[1][0] == "battle_move", b.sent[:3])
b = Bridge(battle(led, 1, GOLBAT))
E._run_policy(dict(bp.DEFAULT_SPEC, **HYBRID), b, b.cur,
              lambda k, **kw: None, 20)
ck("outside a level step the block is never asked",
   b.sent and b.sent[0][0] == "battle_move", b.sent[:2])

src = (ROOT / "planner/executor.py").read_text()
ck("a spec with no block keeps the old switch-in",
   "want_slot = (not _train_block" in src and '"train_switch_in"' in src)
ck("...and one with a block hands the trainee to the policy",
   '_pol_kw["trainee"] = _trainee' in src)
ck("the shim says which slot is out",
   "if pm == mon then d.slot = i break end"
   in (ROOT / "harness/shim.lua").read_text())

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
