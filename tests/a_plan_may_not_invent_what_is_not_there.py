#!/usr/bin/env python3
"""A plan may not dress a leg up with something the game does not have.

The false-fact guard screened the two places the chain edits its OUTLINE, a
rewrite and an insert, and nothing screened what the PLAN author writes on
top of a leg. Run 32's leg 2 is "Retrieve the Poké Ball from the Pallet
Town resident", already one of this outline's own false facts, and the plan
turned it into "Obtain Poke Balls from the Pallet Town resident (MARTY) to
enable catching Pokemon". There is no Marty. Seven proposals went looking
for him through Blue's house, the town centre and Oak's lab (2026-09-22,
user: "never seen this hallucination before, funny but ultimately
harmless"). Harmless there because the finish line was holding five balls
and the Viridian mart sells them; not harmless as a habit.

Pinned: a plan that invents one is refused; a clean plan is not; a leg
whose own wording the outline already carries is NOT made unwritable,
because that wording is the outline's business and refusing it would leave
the leg with no plan at all; the refusal is a form refusal that never says
which part is wrong; and it joins the other plan validators rather than
replacing one. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def plan(goal, *subgoal_texts, key="goal_text"):
    return {"goal": goal,
            "subgoals": [{"id": f"s{i}", key: t}
                         for i, t in enumerate(subgoal_texts, 1)]}


MARTY = ("Obtain Poke Balls from the Pallet Town resident (MARTY) to "
         "enable catching Pokemon")
BALLS = "the party holds 5 POKE_BALL"

p = A.false_fact_problems(plan(BALLS, "Walk to the Viridian mart", MARTY))
ck("run 32's own invention is refused", len(p) == 1, p)
ck("...naming the subgoal and the field, not the fact",
   "subgoal[s2]" in p[0] and "goal_text" in p[0]
   and "MARTY" not in p[0] and "Pallet" not in p[0], p)
ck("...and telling it what to do instead, in form only",
   "say what the step DOES" in p[0] and "only what you have seen" in p[0])

ck("a plan that says what it does is not refused",
   A.false_fact_problems(
       plan(BALLS, "Buy 5 POKE_BALL at the Viridian mart")) == [])
ck("...nor one whose steps name nothing at all",
   A.false_fact_problems(plan(BALLS, "Explore the town", "Heal")) == [])

CARRIED = "Retrieve the Poké Ball from the Pallet Town resident"
ck("a leg whose OWN wording the outline carries is left writable",
   A.false_fact_problems(plan(CARRIED, CARRIED)) == [],
   "else the leg could never get a plan at all")
# THE LIMIT, STATED RATHER THAN PAPERED OVER: when the LEG ITSELF is one of
# the table's false facts, this pass steps aside entirely, so an invention
# added on top of such a leg goes unrefused. That is the price of keeping
# the leg writable at all, and it is exactly the case that produced MARTY.
# Closing it needs the outline's own falsehood dealt with first, which is
# the open TODO item on screening a banked outline.
ck("a plan on top of an ALREADY-false leg is not screened, and that is "
   "the known hole",
   A.false_fact_problems(plan(CARRIED, MARTY)) == [])

ck("the `goal` field is read as well as `goal_text`",
   len(A.false_fact_problems(
       plan(BALLS, MARTY, key="goal"))) == 1)
ck("one subgoal is named once, however many ways it is wrong",
   len(A.false_fact_problems(plan(BALLS, MARTY))) == 1)
ck("every subgoal that invents one is named",
   len(A.false_fact_problems(
       plan(BALLS, MARTY, "Defeat Erika for the Grass Badge"))) == 2)

SRC = (ROOT / "planner/author.py").read_text()
ck("it joins the other plan validators rather than replacing one",
   "or through_a_place_problems(plan)\n                 "
   "or false_fact_problems(plan))" in SRC)
ck("it reads the same tables the judge counts",
   "def false_fact_problems" in SRC
   and SRC.index("def false_fact_problems") < SRC.index("def says_a_false_fact"))
ck("the reason is written where the check is",
   "A PLAN MAY NOT DRESS A LEG UP" in SRC and "MARTY" in SRC)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
