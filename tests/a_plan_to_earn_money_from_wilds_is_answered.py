#!/usr/bin/env python3
"""A plan that means to earn money by fighting wild Pokemon is answered
where the plan is read.

Run 29 stood on Route 2 with 93 yen and wrote it eight rounds running: "I
will grind for money by fighting wild Pokemon on Route 2 until I have
sufficient funds to reach the goal of 5 Poke Balls and 3 Potions." Wild
Pokemon pay nothing. Nothing in the harness had told it otherwise — and
the harness HAS the sentence: "Earn money (trainers pay, wild battles do
not) or move on without it" sits on a `buy` refused for want of funds. The
run never issued that buy. It read the price, decided it was short, and
walked to the grass, so the one place the correction lived was never
reached (user, 2026-09-21: "we want to prevent it from happening in the
first place because its a wrong fact that we might be promoting").

The claim is in the plan's own words, so the answer goes where the other
plan-words answers go, beside the one for a claim to hold what the bag does
not hold. The run's own purse leads. PAY DAY scatters coins in any battle,
so the plain fact is held back while a party member knows it.

Pinned: a plan to grind wilds for money is answered and the sentence is
quoted back; merely being short of money is not answered; nor is a plan to
fight TRAINERS for it; the purse is the run's own count; PAY_DAY in the
party drops the flat claim and keeps the count; it rides with the other
plan-words notes. Measured on run 29's own 162 plans: 19 fire, every one a
plan to earn money from wilds, and every plan that only says it is short
stays quiet. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def note(said, pay=(24, 0), moves=("TACKLE", "VINE_WHIP")):
    ex = E.Executor.__new__(E.Executor)
    ex._wild_pay = list(pay)
    return ex._money_from_wilds_note(said, {"party": [
        {"species": "BULBASAUR", "moves": [{"id": m} for m in moves]}]})


REAL = ("I need more money to buy 3 Poke Balls and 1 Potion at the Pewter "
        "City Mart. I currently have 93 yen. I will grind for money by "
        "fighting wild Pokemon on Route 2 until I have sufficient funds.")
n = note(REAL)
ck("the plan run 29 wrote eight times is answered", n, n)
ck("...with its own sentence quoted back, so it is clear what is answered",
   "I will grind for money by fighting wild Pokemon on Route 2" in n, n)
ck("...and the purse leads, as the run's own count",
   "over this run, 24 wild encounter(s) have paid 0 in total" in n, n)
ck("...and the plain fact follows it",
   n.rstrip().endswith("trainers pay, wild battles do not."), n)

ck("a fresh run with nothing counted yet still answers",
   "trainers pay" in note(REAL, pay=(0, 0))
   and "have paid" not in note(REAL, pay=(0, 0)))
ck("a run that has taken money from wilds says so",
   "8 wild encounter(s) have paid 66 in total" in note(REAL, pay=(8, 66)))

ck("PAY DAY in the party drops the flat claim",
   "trainers pay" not in note(REAL, moves=("TACKLE", "PAY_DAY")), 
   note(REAL, moves=("TACKLE", "PAY_DAY")))
ck("...and keeps the count, which is true either way",
   "24 wild encounter(s) have paid 0" in note(REAL, moves=("PAY_DAY",)))

for quiet in (
        "I am in the Pewter City Mart, but I cannot afford Poke Balls with "
        "my current money (93).",
        "I need 3 more Poke Balls to meet the goal. I currently have 93 "
        "money, which is not enough for 3 Poke Balls.",
        "I will decline the museum entry since it costs 50 yen and I only "
        "have 93.",
        "I will grind on Route 2 until every party member is at least "
        "level 12.",
        "I will walk north to Route 2 and look for the forest entrance.",
        ""):
    ck(f"quiet: {quiet[:52] or '(no plan at all)'}", not note(quiet),
       note(quiet))

ck("a plan to fight TRAINERS for money is not answered",
   not note("I will battle the trainers on Route 3 to earn money for "
            "Poke Balls."), 
   note("I will battle the trainers on Route 3 to earn money for Poke Balls."))
ck("...but one that names both is, because half of it is wrong",
   note("I will head south to Route 2 to grind for money from wild Pokemon "
        "and trainers."))
ck("only the first such sentence is answered, not every one",
   note(REAL + " I will then grind wild Pokemon for cash again.").count(
       "THE MONEY IN THAT PLAN") == 1)

SRC = (ROOT / "planner/executor.py").read_text()
ck("it rides with the other plan-words notes, on the same observation",
   "_coin = self._money_from_wilds_note(self._plan_said, _obs_now)" in SRC
   and SRC.index("_held = self._held_claim_note(self._plan_said, _obs_now)")
   < SRC.index("_coin = self._money_from_wilds_note("))
ck("...and a failure to build it never costs the round",
   "except Exception:\n                _held, _spoke = \"\", \"\"" in SRC)
ck("the sentence is the one the harness already used, not a second one",
   SRC.count("trainers pay, wild battles do not") == 2)

failed = [nm for nm, ok, _ in checks if not ok]
for nm, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + nm + ("" if ok or not d else f"  {str(d)[:220]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
