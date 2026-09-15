"""A healing rule that names an item you do not carry never fires — and
BOTH of the spec's rules are read, not one.

The battle policy heals with a NAMED item. This run's was authored in a
`partyauthor` evaluation — Pewter and the early rival — where POTION is what
a party holds, and it was never revisited (user, 2026-08-24: "yeah we never
did make that policy v2"). By the Elite Four the rule read `POTION below 30%
HP` against a bag of HYPER_POTION, MAX_POTION and three MAX_REVIVEs, and
`battle_item` had fired ONCE in 6041 battle turns. The party walked into a
gauntlet with no Pokemon Center in it, unable to use its own medicine,
blacked out and paid the toll repeatedly ("its gone through a few times and
lost 90% of its money").

The policy has two of them and this read `battle_items` alone, so a
`field_heal` naming the same missing item was dead in silence: v1 heals
below 30% in a fight and below 60% out of one, both with POTION, against a
bag of three SUPER_POTIONs. The page said the fight rule could not fire
and nothing about the other, and CHARIZARD went from the gym's trainers
into Erika at 17 of 116 (2026-09-15, user: "it didnt use the three super
potions it had to heal char and instead died to erika").

The policy is the model's own file. The harness says only that a rule
cannot fire, what IS carried, and that a rule fires on the item it names.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "planner"))
import executor as E

checks = []


def ck(name, ok):
    checks.append((name, bool(ok)))
    print(("  ok   " if ok else "  FAIL ") + name)


class S:
    pass


def line(spec, bag):
    E.set_active_spec(spec)
    return E.Executor._policy_heal_line(S(), {"bag": bag}).strip()


POTION_RULE = {"battle_items": [{"item": "POTION", "hp_below": 0.3}]}
HELD = {"HYPER_POTION": 2, "MAX_POTION": 1, "MAX_REVIVE": 3, "FULL_HEAL": 1}

l = line(POTION_RULE, HELD)
ck("it says the rule cannot fire", "CANNOT HEAL YOU RIGHT NOW" in l)
ck("...naming the item the rule wants", "POTION in a fight" in l)
ck("...and what is actually carried", "HYPER_POTION" in l and "MAX_REVIVE" in l)
ck("...and that the policy is the model's to change",
   "your own battle policy" in l)
ck("it does not name a substitute to use",
   "use " not in l.lower() and "instead" not in l.lower())

ck("silent when the named item is held",
   line(POTION_RULE, dict(HELD, POTION=3)) == "")
ck("silent when the policy names no items", line({"battle_items": []}, HELD) == "")
ck("silent when one of several rules can still fire",
   line({"battle_items": [{"item": "POTION"}, {"item": "MAX_POTION"}]},
        HELD) == "")
ck("says so plainly when nothing at all is carried",
   "no healing items at all" in line(POTION_RULE, {"BICYCLE": 1}))

# ---- the field rule is read too ------------------------------------------------
FIELD = {"item": "POTION", "hp_below": 0.6}
BOTH = dict(POTION_RULE, field_heal=FIELD)

l = line(BOTH, HELD)
ck("both dead rules are said, the fight one first",
   l.index("CANNOT HEAL YOU RIGHT NOW") < l.index("NOT BETWEEN FIGHTS EITHER"))
ck("...the field one naming its item and its own threshold",
   "reaches for POTION when a party member drops below 60% of its HP" in l)
ck("...and what that means on the walk",
   "nobody is mended on the walk between one fight and the next" in l)
ck("a dead field rule alone is said in full, with what is carried",
   "CANNOT MEND ANYONE BETWEEN FIGHTS" in line({"field_heal": FIELD}, HELD)
   and "HYPER_POTION" in line({"field_heal": FIELD}, HELD))
ck("...and it is not dressed up as the fight rule",
   "CANNOT HEAL YOU RIGHT NOW" not in line({"field_heal": FIELD}, HELD))
ck("a field rule whose item is held says nothing",
   line({"field_heal": FIELD}, dict(HELD, POTION=2)) == "")
ck("a spec with no field rule says nothing about one",
   "BETWEEN FIGHTS" not in line(POTION_RULE, HELD))
ck("a threshold of nothing is not invented",
   "when a party member is hurt" in line({"field_heal": {"item": "POTION"}}, HELD))
ck("the one lever is stated once, and it is the rule's own naming",
   l.count("A rule fires only on the item it NAMES") == 1
   and "A rule fires only on the item it NAMES" in line({"field_heal": FIELD}, HELD))
ck("...and still no substitute is picked for the model",
   not any(f"use {h}" in l for h in HELD) and "instead" not in l.lower())
ck("nothing is said when every rule can fire",
   line(dict(POTION_RULE, field_heal=FIELD), dict(HELD, POTION=1)) == "")

bad = [n for n, ok in checks if not ok]
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad
      else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)
