#!/usr/bin/env python3
"""A lead is picked for what it can hurt, a fight spends a share of the
bag, and the model is told what its medicine was worth.

Three pre-v14 changes (user, 2026-09-15: "do the pre-14 steps you
outlined"):
  * best_matchup weighs a member's strongest damaging move — power, STAB,
    chart — over what the foe's types do to it. By multiplier alone
    KABUTOPS read "double" into DEWGONG on a 20-power ABSORB, tied LAPRAS
    and led for forty turns.
  * max_share caps a heal rule in one battle at a share of what the bag
    held of it when the battle began, so five FULL_RESTOREs and ten
    POTIONs are different numbers under one rule.
  * the arena's trial lines say what was spent and what was left, and
    with --stripped the round also scores the spec with its item rules
    cut out and tells the model the margin; ties break on it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import battle_policy as bp    # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


def mon(species, types, moves, hp=150, level=55):
    return {"species": species, "level": level, "hp": hp, "max_hp": hp,
            "types": types,
            "moves": [dict(index=i + 1, id=m, pp=10, type=t, power=p)
                      for i, (m, t, p) in enumerate(moves)]}


DEWGONG = ["WATER", "ICE"]
KABUTOPS = mon("KABUTOPS", ["ROCK", "WATER"],
               [("ABSORB", "GRASS", 20), ("SLASH", "NORMAL", 70),
                ("LEER", "NORMAL", 0), ("HYDRO_PUMP", "WATER", 120)])
LAPRAS = mon("LAPRAS", ["WATER", "ICE"],
             [("BODY_SLAM", "NORMAL", 85), ("CONFUSE_RAY", "GHOST", 0),
              ("ICE_BEAM", "ICE", 95), ("HYDRO_PUMP", "WATER", 120)])
GLOOM = mon("GLOOM", ["GRASS", "POISON"],
            [("PETAL_DANCE", "GRASS", 70), ("SLEEP_POWDER", "GRASS", 0)])

# ---- the matchup weighs power ---------------------------------------------
ck("by multiplier alone, a 20-power Absorb makes Kabutops read double",
   bp.outgoing(KABUTOPS, DEWGONG) == 2.0)
ck("weighed by power, Kabutops's best hit is its resisted Hydro Pump",
   abs(bp.punch(KABUTOPS, DEWGONG) - 0.9) < 1e-6)
ck("...and Lapras's neutral Body Slam is worth about as much",
   abs(bp.punch(LAPRAS, DEWGONG) - 0.9) < 1e-6)
ck("a bare type list still answers the way outgoing did",
   bp.punch(["GRASS"], DEWGONG) == bp.outgoing(["GRASS"], DEWGONG) == 2.0)
_nopower = {"types": ["GRASS"], "moves": [{"id": "X", "type": "GRASS"}]}
ck("a bench whose moves carry no power answers exactly as outgoing does",
   bp.punch(_nopower, DEWGONG) == bp.outgoing(_nopower, DEWGONG))

party = [KABUTOPS, LAPRAS, GLOOM]
obs = {"mode": "battle", "bag": {}, "party": party,
       "battle": {"kind": "trainer", "partyIndex": 0, "enemyIndex": 0,
                  "me": dict(KABUTOPS),
                  "foe": {"species": "DEWGONG", "level": 54, "hp": 169, "max_hp": 169,
                          "types": DEWGONG, "status": None, "moves": []}}}
ck("best_matchup now brings Lapras in against Dewgong, not the Kabutops in front",
   bp.choose_replacement(obs, {"replacement": {"order": "best_matchup"}}) == 2)
ck("...and a turn-one best_matchup switch rule fires for it",
   bp.should_switch(obs, dict(bp.DEFAULT_SPEC, switch=[{"to": "best_matchup", "first_turns": 1,
                                                        "max_uses": 1, "vs": "trainer"}]),
                    {"turn": 1, "intent": "traversal"}) == 2)
ck("the lead order agrees, foe types known",
   bp.choose_lead({"party": party}, dict(bp.DEFAULT_SPEC, lead={"order": "best_matchup", "vs": "trainer"}),
                  foe_types=DEWGONG) == 2)

# ---- max_share: a share of the bag, per battle ----------------------------
def low(bag):
    return {"mode": "battle", "bag": dict(bag),
            "party": [{"species": "LAPRAS", "level": 55, "hp": 40, "max_hp": 200}],
            "battle": {"kind": "trainer", "partyIndex": 0, "enemyIndex": 0,
                       "me": {"species": "LAPRAS", "level": 55, "hp": 40, "max_hp": 200,
                              "types": ["WATER", "ICE"], "status": None,
                              "moves": [{"index": 1, "id": "BODY_SLAM", "pp": 15, "type": "NORMAL", "power": 85}]},
                       "foe": {"species": "DEWGONG", "level": 54, "hp": 180, "max_hp": 180,
                               "types": DEWGONG, "status": None, "moves": []}}}


def spend(rule, bag, turns=6):
    """How many heals one battle spends, the bag draining as it goes."""
    bp.reset_run_budget()
    ctx = {"turn": 1, "intent": "traversal"}
    bag = dict(bag); n = 0
    for t in range(1, turns + 1):
        ctx["turn"] = t
        r = bp.choose(low(bag), dict(bp.DEFAULT_SPEC, name="t", battle_items=[rule]), ctx)
        if r.get("op") == "battle_item":
            n += 1; bag[r["item"]] -= 1
    return n


SHARE = {"item": "heal", "hp_below": 0.4, "max_uses": 6, "max_share": 0.34}
ck("a third of five Full Restores is one, in one fight",
   spend(SHARE, {"FULL_RESTORE": 5}) == 1)
ck("a third of ten Potions is three, under the same rule",
   spend(SHARE, {"POTION": 10}) == 3)
ck("a share never rounds a held item down to nothing",
   spend(dict(SHARE, max_share=0.1), {"FULL_RESTORE": 2}) == 1)
ck("the count cap still applies, and the stricter wins",
   spend(dict(SHARE, max_uses=2), {"POTION": 10}) == 2)
ck("the share is measured from the bag as the battle BEGAN, not as it drains",
   spend(dict(SHARE, max_share=0.5), {"POTION": 10}) == 5)
bp.reset_run_budget()
c = {"turn": 1, "intent": "traversal"}
bp.choose(low({"POTION": 10}), dict(bp.DEFAULT_SPEC, name="t", battle_items=[SHARE]), c)
ck("the battle records the bag it began with", c.get("bag_at_start") == {"POTION": 10})
ck("the validator takes a share in (0,1] and nothing else",
   not bp.validate_spec(dict(bp.DEFAULT_SPEC, name="ok", battle_items=[SHARE]))
   and bp.validate_spec(dict(bp.DEFAULT_SPEC, name="bad", battle_items=[dict(SHARE, max_share=0)]))
   and bp.validate_spec(dict(bp.DEFAULT_SPEC, name="bad", battle_items=[dict(SHARE, max_share=1.5)]))
   and bp.validate_spec(dict(bp.DEFAULT_SPEC, name="bad", battle_items=[dict(SHARE, max_share=True)])))

# ---- the runner tells the model what was spent, and what the medicine was worth
import policy_author as PA    # noqa: E402

PS = (ROOT / "planner/policy_author.py").read_text()
ck("both gauntlet scorers add the spent/unspent line to every trial",
   PS.count("+ self._spent(obs)") == 2)
# THE ROOM'S OWN BAG IS NOT THE POINT, and reading a live one made this
# check a hostage: it asserted "FULL_RESTORE spent 3, unspent 2" off the
# league's five, and the arenas were rebuilt on run 27's save, which walked
# in with two FULL_RESTORE and two MAX_POTION (2026-09-21). What is being
# pinned is the arithmetic, so the bag it works on is written here.
import json as _json, tempfile as _tf
_spec = Path(_tf.mkdtemp()) / "room.json"
_spec.write_text(_json.dumps({"bag": {"FULL_RESTORE": 5, "REVIVE": 2}}))
g = PA.Gym.__new__(PA.Gym)
g.arena_spec = _spec
line = g._spent({"bag": {"FULL_RESTORE": 2}})
ck("the line reads from the arena's starting bag and the screen's ending bag",
   "FULL_RESTORE spent 3, unspent 2" in line)
ck("...and a kind spent to nothing is still counted",
   "REVIVE spent 2, unspent 0" in line)
h = PA.Gym.__new__(PA.Gym)
h.arena_spec = None
ck("a room with no medicine in its bag says nothing", h._spent({"bag": {}}) == "")
r = {"arena": "e4", "rooms": 8, "gauntlet_trials": 2, "blackouts": 2, "agree": 1, "scored": 1,
     "rival_wins": 0, "rival_trials": 0, "pewter": 0, "badge": 0, "dmg_gap": 0.0, "gauntlet_detail": ["beat 4/5"], "stripped": {"fraction": 0.6, "blackouts": 2, "detail": ["beat 3/5"]},
     "medicine_margin": 0.2}
txt = PA.feedback_text("cand", r)
ck("the feedback names the stripped twin and the margin",
   "WITHOUT its item rules: 60%" in txt and "worth +20%" in txt and "without, trial 1: beat 3/5" in txt)
r0 = dict(r, stripped={"fraction": 0.8, "blackouts": 2, "detail": []}, medicine_margin=0.0)
ck("...and says so when the medicine did nothing",
   "did nothing here" in PA.feedback_text("cand", r0))
ck("without --stripped the feedback is unchanged",
   "WITHOUT" not in PA.feedback_text("cand", {k: v for k, v in r.items() if k not in ("stripped", "medicine_margin")}))
ck("the pick breaks ties on the medicine margin, after the points",
   "across[i][0][1].get(\"medicine_margin\"" in PS and "+ cross_key(across[i])[1:]" in PS)
ck("the model is told about max_share and the weighted matchup",
   "max_share" in PA.DSL_DOC and "20-power ABSORB" in PA.DSL_DOC)

failed = [n for n, ok_ in checks if not ok_]
for n, ok_ in checks:
    print(("ok   " if ok_ else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
