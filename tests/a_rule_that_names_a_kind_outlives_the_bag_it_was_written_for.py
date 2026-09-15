"""A healing rule may name a KIND, and then the bag supplies the name.

Every battle policy the run has ever had was authored inside one arena and
named the items that arena's party happened to hold. v1 was written at
Pewter, where POTION is what a bag has, and named POTION in both of its
healing rules; twenty legs later the bag held three SUPER_POTIONs, neither
rule could reach them, and CHARIZARD went into Erika at 17 of 116 and the
run blacked out (2026-09-15, user: "it didnt use the three super potions it
had to heal char and instead died to erika"). v6 was written at the Elite
Four and names HYPER_POTION, which no early party has seen; it would die at
Brock in the other direction, and its own trial record says it did.

The decision in those rules — heal below this fraction, spend at most this
many, bring a body back while one is down — is not stage-specific at all.
Only the NAMES are (user, 2026-08-24: "ONE BATTLE POLICY ACROSS STAGES, not
one per stage ... What is stage-specific is the item NAMES, not the
decisions"). So a rule may name a class, and the ladder is resolved against
the bag at the moment the rule fires.

What stays the model's: whether to name a class at all, which threshold it
fires at, and WHICH RUNG to take — the strongest thing in the bag, the
weakest, or the smallest one that covers what is actually missing. The
harness knows only what each item says on its own description screen.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as B                                  # noqa: E402
import executor as E                                       # noqa: E402

checks = []
def ck(name, cond): checks.append((name, bool(cond)))


MOVES = [{"index": 1, "id": "SCRATCH", "pp": 20, "type": "NORMAL",
          "power": 40, "accuracy": 100, "category": "physical"}]


def battle(hp, mx, bag, party=None, kind="trainer"):
    return {"mode": "battle", "bag": dict(bag),
            "party": party if party is not None
            else [{"species": "CHARIZARD", "hp": hp, "max_hp": mx}],
            "battle": {"kind": kind,
                       "me": {"species": "CHARIZARD", "hp": hp, "maxhp": mx,
                              "types": ["FIRE"], "moves": MOVES},
                       "foe": {"species": "VICTREEBEL", "hp": 80,
                               "types": ["GRASS"]}}}


def field(hp, mx, bag, status=None):
    mon = {"species": "CHARIZARD", "hp": hp, "max_hp": mx}
    if status:
        mon["status"] = status
    return {"mode": "overworld", "bag": dict(bag), "party": [mon]}


PEWTER = {"POTION": 4}
CELADON = {"SUPER_POTION": 3}
LEAGUE = {"FULL_RESTORE": 2, "MAX_REVIVE": 1}

# One spec, written once, in the shape the TODO asks for.
CLASSED = {"battle_items": [{"item": "heal", "hp_below": 0.4, "max_uses": 3},
                            {"item": "revive", "target": "fainted",
                             "max_uses": 2}],
           "field_heal": {"item": "heal", "hp_below": 0.6},
           "field_cure": [{"status": "PSN", "item": "cure"}],
           "catch": {"ball": "ball"}}
V1_SHAPED = {"battle_items": [{"item": "POTION", "hp_below": 0.4}],
             "field_heal": {"item": "POTION", "hp_below": 0.6}}


def fought(spec, obs):
    return B.choose(obs, spec, {"turn": 2})


# ---- the same spec, three stages of one game ---------------------------
for where, bag, want in (("Pewter", PEWTER, "POTION"),
                         ("Celadon", CELADON, "SUPER_POTION"),
                         ("the League", LEAGUE, "FULL_RESTORE")):
    op = fought(CLASSED, battle(17, 116, bag))
    ck(f"one rule heals in a fight at {where} (with {want})",
       op.get("op") == "battle_item" and op.get("item") == want)
    fh = B.should_field_heal(field(17, 116, bag), CLASSED)
    ck(f"...and on the walk out of {where} too",
       fh and fh[0] == want and fh[1] == 1)

# the run that actually happened, for contrast
ck("the rule v1 wrote is dead at Celadon, in a fight",
   fought(V1_SHAPED, battle(17, 116, CELADON)).get("op") == "battle_move")
ck("...and dead on the walk, which is how Erika won",
   B.should_field_heal(field(17, 116, CELADON), V1_SHAPED) is None)
ck("a named rule still fires where its name is right",
   fought(V1_SHAPED, battle(17, 116, PEWTER)).get("item") == "POTION")

# ---- which rung: the model's choice, not the harness's -----------------
SHELF = {"POTION": 1, "SUPER_POTION": 1, "HYPER_POTION": 1}
ck("weakest_sufficient covers the deficit and no more (30 missing)",
   B.resolve_item("heal", SHELF, missing=30) == "SUPER_POTION")
ck("...and takes the biggest held when nothing covers it",
   B.resolve_item("heal", SHELF, missing=900) == "HYPER_POTION")
ck("...and is the default when the spec says nothing",
   B.resolve_item("heal", SHELF, missing=10) == "POTION")
ck("best_available takes the strongest in the bag",
   B.resolve_item("heal", SHELF, "best_available", missing=10)
   == "HYPER_POTION")
ck("weakest_available takes the weakest, deficit or no",
   B.resolve_item("heal", SHELF, "weakest_available", missing=900)
   == "POTION")
ck("the deficit read in a fight is the ACTIVE mon's, not the party's",
   fought(dict(CLASSED, battle_items=[{"item": "heal", "hp_below": 0.9}]),
          battle(100, 300, SHELF)).get("item") == "HYPER_POTION")

# ---- classes that are not HP -------------------------------------------
ck("a cure takes the dedicated one and saves the FULL_RESTORE",
   B.should_field_cure(field(50, 100,
                             {"ANTIDOTE": 1, "FULL_RESTORE": 1}, "PSN"),
                       CLASSED) == ("ANTIDOTE", 1))
ck("...and falls through to FULL_HEAL when it is gone",
   B.should_field_cure(field(50, 100, {"FULL_HEAL": 1}, "PSN"),
                       CLASSED) == ("FULL_HEAL", 1))
ck("a cure rule reads its OWN status, not another rule's",
   B.should_field_cure(field(50, 100, {"PARLYZ_HEAL": 1}, "PSN"),
                       CLASSED) is None)
DOWN = [{"species": "PIKACHU", "hp": 0, "max_hp": 60},
        {"species": "CHARIZARD", "hp": 90, "max_hp": 116}]
op = fought(CLASSED, battle(90, 116, {"REVIVE": 1, "MAX_REVIVE": 1},
                            party=DOWN))
ck("a revive brings a body back, the cheap one first",
   op.get("op") == "battle_item" and op.get("item") == "REVIVE"
   and op.get("target") == "fainted")
ck("the one-of-a-kind ball is not a rung any ladder climbs",
   "MASTER_BALL" not in B.BALL_LADDER
   and "SAFARI_BALL" not in B.BALL_LADDER
   and not B.resolve_item("ball", {"MASTER_BALL": 1}))
ck("a thrown ball carries the item, never the word for the kind",
   (B.choose(battle(90, 116, {"GREAT_BALL": 5}, kind="wild"), CLASSED,
             {"turn": 2, "intent": "catch"}) or {}).get("ball")
   == "GREAT_BALL")

# ---- a budget is spent by the rule, not by each rung -------------------
ctx = {"turn": 1}
spec1 = {"battle_items": [{"item": "heal", "hp_below": 0.9, "max_uses": 2}]}
bag2 = {"POTION": 5, "SUPER_POTION": 5}
fired = []
for _ in range(4):
    o = B.choose(battle(10, 300, bag2), spec1, ctx)
    if o.get("op") == "battle_item":
        fired.append(o["item"])
ck("max_uses 2 on a class rule is two heals, not two of each",
   len(fired) == 2)
twice_named = {"battle_items": [{"item": "POTION", "hp_below": 0.9,
                                 "max_uses": 1},
                                {"item": "POTION", "hp_below": 0.9,
                                 "max_uses": 1}]}
ctx2, named_fired = {"turn": 1}, 0
for _ in range(4):
    if B.choose(battle(10, 300, {"POTION": 9}), twice_named,
                ctx2).get("op") == "battle_item":
        named_fired += 1
ck("two rules naming one item still share that item's budget as before",
   named_fired == 1)

# ---- what the spec is allowed to say -----------------------------------
ck("a class in every slot is a valid spec", B.validate_spec(CLASSED) == [])
ck("every old spec on disk is still valid",
   all(B.validate_spec(B.load_spec(p)) == []
       for p in sorted((ROOT / "plans").glob("policy_model_v*.json"))))
ck("an unknown preference is refused",
   any("prefer" in p for p in B.validate_spec(
       {"field_heal": {"item": "heal", "prefer": "cheapest"}})))
ck("a preference on a named item is refused as confused",
   any("names one item" in p for p in B.validate_spec(
       {"field_heal": {"item": "POTION", "prefer": "best_available"}})))

# ---- and the page tells the truth about a class rule -------------------
def line(spec, bag):
    E.set_active_spec(spec)
    return E.Executor._policy_heal_line(type("S", (), {})(),
                                        {"bag": bag}).strip()


ck("a class rule is never called dead while the bag holds a rung",
   line(CLASSED, CELADON) == "")
ck("...and the run that blacked out WAS told, under the old shape",
   "CANNOT HEAL" in line(V1_SHAPED, CELADON))
ck("an empty shelf is named by the shelf, not by the word for the kind",
   "POTION" in line(CLASSED, {"REPEL": 3})
   and " heal " not in line(CLASSED, {"REPEL": 3}))

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad
      else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)
