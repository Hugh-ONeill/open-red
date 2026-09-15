"""Out of PP against a Ghost is not a fight, it is a wall.

When every move is at 0 PP the game hands you Struggle. Struggle is
NORMAL and NORMAL does nothing at all to a GHOST. Gen 1 enemy Pokemon do
not Struggle either (user, 2026-09-15: "i forgot that enemy mons dont use
struggle in gen1"), so a foe that has also run dry simply stops taking
turns. VAPOREON ran empty against AGATHA's GENGAR and the two of them
stood there for fifty minutes, foe HP frozen at 74/151, with five on the
bench and one of them untouched.

The policy had no way to say "leave". `switch` reads hp_below, vs,
only_if_lead — nothing about having run dry. And the turn gate defaults
to the first turn, so the obvious rule would have read correctly and
never fired once, because running dry arrives late by definition.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "planner"))
import battle_policy as BP

checks = []


def ck(name, ok):
    checks.append((name, bool(ok)))
    print(("  ok   " if ok else "  FAIL ") + name)


def mon(hp, maxhp=200, species="X", pps=(10, 10, 10, 10)):
    return {"species": species, "hp": hp, "max_hp": maxhp, "maxhp": maxhp,
            "level": 50, "types": ["WATER"],
            "moves": [{"index": i + 1, "id": f"M{i}", "pp": pp}
                      for i, pp in enumerate(pps)]}


def obs(pps):
    return {"battle": {"kind": "trainer",
                       "me": mon(12, species="VAPOREON", pps=pps),
                       "foe": {"species": "GENGAR", "hp": 74,
                               "types": ["GHOST", "POISON"]}},
            "party": [mon(12, species="VAPOREON", pps=pps),
                      mon(204, species="CHARIZARD")]}


DRY = (0, 0, 0, 0)
RULE = {"switch": [{"to": 2, "out_of_pp": True, "max_uses": 1}]}

ck("a mon with nothing left leaves",
   BP.should_switch(obs(DRY), RULE, {"turn": 30}) == 2)
ck("...and one with a move left stays",
   BP.should_switch(obs((0, 0, 3, 0)), RULE, {"turn": 30}) is None)
ck("...even one PP is a move left",
   BP.should_switch(obs((0, 0, 0, 1)), RULE, {"turn": 30}) is None)

# the trap the default turn gate would have set
ck("running dry late still fires, with no first_turns written",
   BP.should_switch(obs(DRY), RULE, {"turn": 88}) == 2)
ck("...but a first_turns you wrote yourself is still obeyed",
   BP.should_switch(obs(DRY),
                    {"switch": [{"to": 2, "out_of_pp": True,
                                 "first_turns": 3}]},
                    {"turn": 30}) is None)
ck("...and an ordinary rule is still gated to turn one",
   BP.should_switch(obs(DRY), {"switch": [{"to": 2}]}, {"turn": 30}) is None
   and BP.should_switch(obs(DRY), {"switch": [{"to": 2}]}, {"turn": 1}) == 2)

# it composes with the conditions already there
ck("it still answers to the other conditions",
   BP.should_switch(obs(DRY),
                    {"switch": [{"to": 2, "out_of_pp": True,
                                 "vs": "wild"}]}, {"turn": 30}) is None)
ck("...and an order name still resolves",
   BP.should_switch(obs(DRY),
                    {"switch": [{"to": "healthiest", "out_of_pp": True}]},
                    {"turn": 30}) == 2)

# the spec language admits it
ck("the validator accepts the key",
   not BP.validate_spec({"switch": [{"to": 2, "out_of_pp": True}]}))
ck("...and rejects a non-boolean",
   any("out_of_pp" in p for p in
       BP.validate_spec({"switch": [{"to": 2, "out_of_pp": "yes"}]})))

# the model is told it exists, and why
import policy_author as P
ck("the spec language shown to the model carries it",
   '"out_of_pp"' in P.DSL_DOC)
ck("...with the reason it is not gated to turn one",
   "running\n     dry arrives late" in P.DSL_DOC
   or "running dry arrives late" in P.DSL_DOC.replace("\n     ", " "))
ck("...and what Struggle does to a Ghost",
   "NORMAL\n     does nothing at all to a GHOST" in P.DSL_DOC
   or "does nothing at all to a GHOST" in P.DSL_DOC)
ck("...and that the enemy will not Struggle back",
   "do not\n     Struggle" in P.DSL_DOC or "do not Struggle"
   in P.DSL_DOC.replace("\n     ", " "))

bad = [n for n, ok in checks if not ok]
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad
      else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)
