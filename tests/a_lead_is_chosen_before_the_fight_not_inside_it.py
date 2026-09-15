"""Who walks in is decided in the overworld, where it is free.

SLOT 1 STARTS EVERY BATTLE and nothing outside a faint prompt reorders the
party, so the Pokemon the last fight chewed up leads the next one too —
through a gym's whole chain of trainers and into its leader. The policy's
only answer was `switch`, which brings someone in mid-fight at the cost of
the turn and a free hit for the foe, and v7 spent 200 of them doing exactly
that across the arena tests (user, 2026-09-15: "before facing a gym leader
or elite four member it should be pausing and choosing who to put first").

`lead` settles it on the step before the press, where it costs nothing. It
also means there is no foe on screen when it is decided, so the orders read
your own side only and no type rule is offered here — it would have nothing
to read, the same reason `replacement`'s type orders fall back to health
outside a fight.

What stays the model's: the order, and whether to have one at all.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as B                                  # noqa: E402

checks = []
def ck(name, cond): checks.append((name, bool(cond)))

EXE = (ROOT / "planner" / "executor.py").read_text()
PA = (ROOT / "planner" / "policy_author.py").read_text()

# a party after a gym's trainers: the lead is nearly dead, the bench is not
PARTY = [{"species": "CHARIZARD", "hp": 20, "max_hp": 120, "level": 41},
         {"species": "NIDOKING", "hp": 100, "max_hp": 110, "level": 38},
         {"species": "FARFETCHD", "hp": 60, "max_hp": 60, "level": 32},
         {"species": "EEVEE", "hp": 0, "max_hp": 70, "level": 30}]
OBS = {"party": PARTY}


def lead(order, kind="trainer", **kw):
    return B.choose_lead(OBS, {"lead": dict(order=order, **kw)}, kind)


ck("healthiest leads with the one the last fight did not chew up",
   lead("healthiest") == 3)
ck("most_hp leads with the biggest body still standing",
   lead("most_hp") == 2)
ck("highest_level leads with the strongest, hurt or not",
   lead("highest_level") == 1)
ck("first_alive is the game's own behaviour, written down",
   lead("first_alive") == 1)
ck("a fainted member never leads",
   all(lead(o) != 4 for o in B.LEAD_ORDERS))

# ---- the floor, and never an empty bench ------------------------------
ck("a floor keeps a nearly-dead one from leading",
   lead("healthiest", min_hp_frac=0.9) == 3)
ck("...and is ignored rather than obeyed into leading with nobody",
   B.choose_lead({"party": [{"hp": 5, "max_hp": 100, "level": 9},
                            {"hp": 4, "max_hp": 100, "level": 9}]},
                 {"lead": {"order": "healthiest", "min_hp_frac": 0.9}}) == 1)

# ---- when it does not fire -------------------------------------------
ck("a trainer rule says nothing about a wild encounter",
   lead("healthiest", kind="wild") is None)
ck("...and vs any covers both", lead("healthiest", vs="any",
                                     kind="wild") == 3)
ck("a spec with no lead rule leaves the party alone",
   B.choose_lead(OBS, {}) is None)
ck("one Pokemon standing is not a choice",
   B.choose_lead({"party": [PARTY[0], {"hp": 0, "max_hp": 9}]},
                 {"lead": {"order": "healthiest"}}) is None)

# ---- what the spec may say -------------------------------------------
ck("a lead rule is a valid spec",
   B.validate_spec({"lead": {"order": "healthiest", "vs": "trainer",
                             "min_hp_frac": 0.4}}) == [])
ck("a type order is refused, because there is no foe to read",
   any("order one of" in p for p in
       B.validate_spec({"lead": {"order": "resists"}})))
ck("every spec on disk is still valid",
   all(B.validate_spec(B.load_spec(q)) == []
       for q in sorted((ROOT / "plans").glob("policy_model_v*.json"))))

# ---- and it is carried out where it is free --------------------------
ck("the swap happens on the step before an interact",
   "obs = self._lead_before_a_fight(obs, step, sg, trace)" in EXE
   and EXE.index("_lead_before_a_fight(obs, step") < EXE.index(
       'here_r = self._where(obs)'))
ck("...only against a trainer, never a sign or a shopkeeper",
   'kinds.get(name) != "trainer"' in EXE)
ck("...through the party_swap op, not by fighting for it",
   '_send_safe("party_swap", a=1, b=want)' in EXE)
ck("...and the trace says who leads and why",
   "your policy's lead rule" in EXE)
ck("a failure to arrange the party never costs the round",
   "a lead is never worth the round" in EXE)
ck("the model is offered the rule in its own brief",
   '"vs": "trainer"|"wild"|"any", "min_hp_frac"' in PA
   and "costs NO TURN" in PA)

# ---- and a switch may name an order too -------------------------------
# A SLOT NUMBER IS A POSITION, NOT A POKEMON. v7 named slot 3 and it was a
# PIDGEY at Pewter, a PIDGEOTTO at Vermilion and a FARFETCH'D at Celadon:
# one rule meaning three unrelated things. Mid-fight the foe IS on screen,
# which is when the type orders have something to read.
MV = [{"index": 1, "id": "SCRATCH", "pp": 20, "type": "NORMAL",
       "power": 40, "accuracy": 100, "category": "physical"}]
KC = [{"index": 1, "id": "KARATE_CHOP", "pp": 25, "type": "FIGHTING",
       "power": 50, "accuracy": 100, "category": "physical"}]
ROOM = [{"species": "CHARMANDER", "hp": 30, "max_hp": 40, "level": 12,
         "types": ["FIRE"], "moves": MV},
        {"species": "NIDORAN_M", "hp": 35, "max_hp": 38, "level": 11,
         "types": ["POISON"], "moves": MV},
        {"species": "PIDGEY", "hp": 30, "max_hp": 34, "level": 10,
         "types": ["NORMAL", "FLYING"], "moves": MV},
        {"species": "MANKEY", "hp": 42, "max_hp": 45, "level": 15,
         "types": ["FIGHTING"], "moves": KC}]
FIGHT = {"party": ROOM,
         "battle": {"kind": "trainer", "me": ROOM[0],
                    "foe": {"species": "ONIX", "hp": 50,
                            "types": ["ROCK", "GROUND"]}}}


def sw(to):
    return B.should_switch(FIGHT, {"switch": [{"to": to, "first_turns": 2}]},
                           {"turn": 1})


ck("a switch may name an order, and it finds the counter",
   sw("best_matchup") == 4 and sw("resists") == 4)
ck("...while a raw slot still means that slot",
   sw(3) == 3)
ck("an order nobody defined is refused",
   any("resists/best_matchup" in p for p in
       B.validate_spec({"switch": [{"to": "strongest"}]})))
ck("a slot out of the party is still refused",
   any("[1,6]" in p for p in B.validate_spec({"switch": [{"to": 9}]})))
ck("both forms are valid specs",
   B.validate_spec({"switch": [{"to": "best_matchup"}]}) == []
   and B.validate_spec({"switch": [{"to": 3}]}) == [])

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad
      else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)
