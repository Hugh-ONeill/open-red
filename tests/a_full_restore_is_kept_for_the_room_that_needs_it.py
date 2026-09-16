#!/usr/bin/env python3
"""A Full Restore is kept for the room that needs it.

The real-path league (2026-09-15) spent all five FULL_RESTOREs on
LORELEI's DEWGONG and BRUNO's ONIX — three and two, every trial — and
walked into LANCE with nothing, exactly like the run it was copied from.
Both rooms were won by the arm with no items at all. `max_uses` is per
battle and starts over with every trainer; nothing in the spec could say
"keep some" or "five for the whole way". Now a rule can carry a
`reserve` (never fire if it would leave fewer than this in the bag) and a
`max_uses_run` (a cap across every battle until the party is next made
whole), and the executor and the arena runner keep the ledger.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import battle_policy as bp    # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


def obs(bag, hp=40, max_hp=200):
    return {"mode": "battle", "bag": dict(bag),
            "party": [{"species": "LAPRAS", "level": 55, "hp": hp, "max_hp": max_hp}],
            "battle": {"kind": "trainer", "partyIndex": 0, "enemyIndex": 0,
                       "me": {"species": "LAPRAS", "level": 55, "hp": hp, "max_hp": max_hp,
                              "types": ["WATER", "ICE"], "status": None,
                              "moves": [{"index": 1, "id": "BODY_SLAM", "pp": 15,
                                         "type": "NORMAL", "power": 85}]},
                       "foe": {"species": "DEWGONG", "level": 54, "hp": 180, "max_hp": 180,
                               "types": ["WATER", "ICE"], "status": None, "moves": []}}}


def spec(rule):
    return dict(bp.DEFAULT_SPEC, name="t", battle_items=[rule])


def fires(rule, bag, ctx=None, hp=40):
    ctx = ctx if ctx is not None else {"turn": 1, "intent": "traversal"}
    bp.reset_run_budget()
    r = bp.choose(obs(bag, hp=hp), spec(rule), ctx)
    return r.get("op") == "battle_item"


HEAL = {"item": "heal", "hp_below": 0.4, "max_uses": 3}

# ---- reserve: what you do not spend here ----------------------------------
ck("without a reserve, a low mon with five Full Restores heals",
   fires(HEAL, {"FULL_RESTORE": 5}))
ck("a reserve of 2 still fires with five in the bag",
   fires(dict(HEAL, reserve=2), {"FULL_RESTORE": 5}))
ck("...and with three (leaving two)",
   fires(dict(HEAL, reserve=2), {"FULL_RESTORE": 3}))
def spend_all(rule, bag, turns=12):
    """Keep a mon under the line for a whole fight; how many go, how many
    stay. One ledger from the start, as a run between Centers has."""
    bp.reset_run_budget()
    bag = dict(bag)
    c = {"turn": 1, "intent": "traversal"}
    used = 0
    for turn in range(1, turns + 1):
        c["turn"] = turn
        r = bp.choose(obs(bag), spec(dict(rule, max_uses=99)), c)
        if r.get("op") == "battle_item":
            used += 1
            bag[r["item"]] -= 1
    return used, bag


# A RESERVE HOLDS BACK AT MOST HALF OF WHAT THE BAG HELD AT THE LAST CENTER
# (2026-09-16): run 26's BULBASAUR lost to GEODUDE twice with its only
# POTION unspendable under v13's reserve 2.
ck("the only POTION is used under a reserve of 2",
   fires(dict(HEAL, reserve=2), {"POTION": 1}))
ck("with two and a reserve of 2, one is spent and one is kept",
   spend_all(dict(HEAL, reserve=2), {"FULL_RESTORE": 2})
   == (1, {"FULL_RESTORE": 1}))
ck("with five and a reserve of 2, three are spent and two are kept",
   spend_all(dict(HEAL, reserve=2), {"FULL_RESTORE": 5})
   == (3, {"FULL_RESTORE": 2}))
ck("a reserve on a class counts every rung together",
   spend_all(dict(HEAL, reserve=2), {"POTION": 2, "SUPER_POTION": 2})[0] == 2)
ck("a reserve on a named item counts that item, capped at half",
   spend_all({"item": "FULL_RESTORE", "hp_below": 0.4, "reserve": 4},
             {"FULL_RESTORE": 4}) == (2, {"FULL_RESTORE": 2}))
ck("the count at the last Center is the measure, not the count now",
   spend_all(dict(HEAL, reserve=3), {"FULL_RESTORE": 8})
   == (5, {"FULL_RESTORE": 3}))
ck("a reserve of 0 is no reserve", fires(dict(HEAL, reserve=0), {"FULL_RESTORE": 1}))

# ---- no reserve against the leader (user, 2026-09-16) ---------------------
# "we dont need the reserve *after* fighting the gym leader, just to
# preserve health on the way to them in the first place, same thing with the
# e4 and champion"
def spend_vs(rule, bag, leader, turns=12):
    bp.reset_run_budget()
    bag = dict(bag)
    c = {"turn": 1, "intent": "traversal"}
    used = 0
    for turn in range(1, turns + 1):
        c["turn"] = turn
        o = obs(bag)
        o["battle"]["leader"] = leader
        r = bp.choose(o, spec(dict(rule, max_uses=99)), c)
        if r.get("op") == "battle_item":
            used += 1
            bag[r["item"]] -= 1
    return used, bag


ck("against a gym leader or the Champion, a reserve holds nothing back",
   spend_vs(dict(HEAL, reserve=3), {"FULL_RESTORE": 5}, True)
   == (5, {"FULL_RESTORE": 0}))
ck("...against their trainers and the four rooms before, it still does",
   spend_vs(dict(HEAL, reserve=3), {"FULL_RESTORE": 5}, False)
   == (3, {"FULL_RESTORE": 2}))
ck("...and a leader fight still keeps its per-fight and per-run caps",
   spend_vs(dict(HEAL, reserve=3, max_uses_run=2), {"FULL_RESTORE": 5},
            True)[0] == 2)
_shim = (ROOT / "harness/shim.lua").read_text()
ck("the shim marks a leader by the engine's badge-fight flag or the Champion",
   "o.battle.leader = (top.isGymLeader == true)" in _shim
   and 'top.trainer.id == "OPP_RIVAL3"' in _shim)
_bs = (Path.home() / "Developer/gen1recomp/src/battle/BattleState.lua").read_text()
ck("...and the engine still sets that flag for badge fights",
   "self.isGymLeader = isBoss" in _bs and '"OPP_RIVAL3"' in _bs)

# ---- the Dewgong fight, replayed with a reserve ---------------------------
bp.reset_run_budget()
bag = {"FULL_RESTORE": 5}
ctx = {"turn": 1, "intent": "traversal"}
spent = 0
for turn in range(1, 8):
    ctx["turn"] = turn
    r = bp.choose(obs(bag), spec(dict(HEAL, reserve=3)), ctx)
    if r.get("op") == "battle_item":
        spent += 1
        bag["FULL_RESTORE"] -= 1
ck("under 40% against Dewgong with a reserve of 3, five Full Restores keep "
   "two (half of five, rounded down), not three",
   spent == 3 and bag["FULL_RESTORE"] == 2)

# ---- max_uses_run: a cap across battles until the party is made whole ----
RUN = dict(HEAL, max_uses_run=2)
bp.reset_run_budget()
c1 = {"turn": 1, "intent": "traversal"}
a = bp.choose(obs({"FULL_RESTORE": 9}), spec(RUN), c1).get("op") == "battle_item"
c1["turn"] = 2
b = bp.choose(obs({"FULL_RESTORE": 9}), spec(RUN), c1).get("op") == "battle_item"
c1["turn"] = 3
c = bp.choose(obs({"FULL_RESTORE": 9}), spec(RUN), c1).get("op") == "battle_item"
ck("a run cap of 2 fires twice in the first battle and not a third time",
   a and b and not c)
c2 = {"turn": 1, "intent": "traversal"}           # the next trainer: a fresh ctx
d = bp.choose(obs({"FULL_RESTORE": 9}), spec(RUN), c2).get("op") == "battle_item"
ck("...and not in the next battle either: the ledger outlives the battle", not d)
ck("the ledger is the module's, so a ctx without one is handed it",
   c2.get("items_used_run") is bp.RUN_BUDGET and bp.RUN_BUDGET.get("#0:heal") == 2)
bp.reset_run_budget()
c3 = {"turn": 1, "intent": "traversal"}
e = bp.choose(obs({"FULL_RESTORE": 9}), spec(RUN), c3).get("op") == "battle_item"
ck("made whole, the run starts over and the rule fires again", e)
# a cleaner per-battle check: max_uses 1 → once per ctx, twice across two ctxs
bp.reset_run_budget()
cx = {"turn": 1, "intent": "traversal"}
f1 = bp.choose(obs({"FULL_RESTORE": 9}), spec(dict(HEAL, max_uses=1)), cx).get("op") == "battle_item"
cx["turn"] = 2
f2 = bp.choose(obs({"FULL_RESTORE": 9}), spec(dict(HEAL, max_uses=1)), cx).get("op") == "battle_item"
cy = {"turn": 1, "intent": "traversal"}
f3 = bp.choose(obs({"FULL_RESTORE": 9}), spec(dict(HEAL, max_uses=1)), cy).get("op") == "battle_item"
ck("max_uses 1 with no run cap: once a battle, again next battle", f1 and not f2 and f3)

# ---- the field heal honours a reserve too ---------------------------------
FIELD = {"mode": "overworld", "bag": {"FULL_RESTORE": 2},
         "party": [{"species": "LAPRAS", "level": 55, "hp": 40, "max_hp": 200}]}
fh = dict(bp.DEFAULT_SPEC, field_heal={"item": "heal", "hp_below": 0.5})
ck("a field heal fires with two in the bag and no reserve",
   bp.should_field_heal(FIELD, fh) == ("FULL_RESTORE", 1))
fh2 = dict(bp.DEFAULT_SPEC, field_heal={"item": "heal", "hp_below": 0.5, "reserve": 2})
ck("...and not when it would dip under the reserve", bp.should_field_heal(FIELD, fh2) is None)

# ---- the validator knows the fields ---------------------------------------
ok = dict(bp.DEFAULT_SPEC, name="ok", battle_items=[dict(HEAL, reserve=2, max_uses_run=4)],
          field_heal={"item": "heal", "hp_below": 0.5, "reserve": 1})
ck("a spec with a reserve and a run cap validates", not bp.validate_spec(ok))
bad1 = dict(bp.DEFAULT_SPEC, name="bad", battle_items=[dict(HEAL, reserve=-1)])
bad2 = dict(bp.DEFAULT_SPEC, name="bad", battle_items=[dict(HEAL, max_uses_run=0)])
bad3 = dict(bp.DEFAULT_SPEC, name="bad", field_heal={"item": "heal", "hp_below": 0.5, "reserve": "2"})
ck("...and a negative reserve, a zero run cap or a string reserve do not",
   bp.validate_spec(bad1) and bp.validate_spec(bad2) and bp.validate_spec(bad3))

# ---- the executor and the runner keep the ledger --------------------------
EX = (ROOT / "planner/executor.py").read_text()
PA = (ROOT / "planner/policy_author.py").read_text()
ck("every battle is handed the run's ledger",
   '"items_used_run": battle_policy.RUN_BUDGET' in EX)
ck("a blackout or a Center heal starts it over",
   'if kind == "blackout" or (kind == "heal_done" and kw.get("ok")):' in EX
   and "battle_policy.reset_run_budget()" in EX)
ck("an arena trial is a fresh bag, in both gauntlet scorers",
   PA.count("battle_policy.reset_run_budget()") >= 2
   and all(PA.index("battle_policy.reset_run_budget()", PA.index(m)) - PA.index(m) < 3000
           for m in ("def eval_spec_gym", "def eval_spec_e4")))
ck("the model is told about both fields, and why",
   "max_uses_run" in PA and '"reserve"' in PA and "ONE bag" in PA)

failed = [n for n, ok_ in checks if not ok_]
for n, ok_ in checks:
    print(("ok   " if ok_ else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
