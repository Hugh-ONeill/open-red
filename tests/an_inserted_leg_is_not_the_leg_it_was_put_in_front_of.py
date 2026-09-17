#!/usr/bin/env python3
"""A leg the missing rung put in front of another is not that other leg
under a new name.

Run 27, 2026-09-16: "Obtain the FRESH WATER" was inserted in front of
"Reach Celadon City", and the author's first step for it was
go_to_celadon_city: {"map": "CELADON_CITY"} — the whole of the leg it was
put ahead of, three attempts failed. It happened to work (the run found
Rock Tunnel on the way) and the user did not want it anyway: "we shouldnt
be just casually letting the author set the first goal in the new leg to
be the entire previously failed leg".

Pinned: the chain's own insert record names the displaced leg, under this
wording or an earlier one; that leg's own words give what it ends on (a
map, a badge, an item); any step of the inserted leg's plan that makes
that true is refused with the fact named, in validate(); a map the game
names after the town counts; the author's page says it up front. Steps
that stay clear are untouched, and a leg nobody inserted is never asked.
Synthetic.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


tmp = Path(tempfile.mkdtemp())
ins = tmp / "outline_inserts"
ins.write_text("LEG=Traverse Mt. Moon|Traverse Viridian Forest\n"
               "LEG=Reach Celadon City|Obtain the FRESH WATER\n"
               "LEG=Retrieve the Silph Scope from the Rocket Game Corner|"
               "Obtain the Lift Key\n"
               "LEG=Defeat Erika for the Rainbow Badge|Buy a POTION\n")
A.OUTLINE_INSERTS = ins
RENAMED = "Obtain the FRESH WATER from the Cerulean City Mart"
A._reword_chain = (lambda g: [("Obtain the FRESH WATER", RENAMED)]
                   if A._norm_obj(g) == A._norm_obj(RENAMED) else [])

ck("a leg's words say what it ends on: a map",
   A.leg_condition("Reach Celadon City") == {"map": "CELADON_CITY"})
ck("...a badge", A.leg_condition("Defeat Erika for the Rainbow Badge").get("badge") == "RAINBOWBADGE")
ck("...an item",
   A.leg_condition("Retrieve the Silph Scope from the Rocket Game Corner").get("item") == "SILPH_SCOPE")
ck("...and nothing for a deed that names none",
   A.leg_condition("every party member is at least level 40") == {})

ck("the displaced leg is read from the chain's record",
   A.displaced_by("Obtain the FRESH WATER") == "Reach Celadon City")
ck("...under a later wording of the inserted leg too",
   A.displaced_by(RENAMED) == "Reach Celadon City")
ck("a leg nobody inserted has none", A.displaced_by("Defeat Erika for the Rainbow Badge") is None)


def plan(goal, *dws):
    return {"goal": goal, "subgoals": [
        {"id": f"s{i}", "goal_text": "step", "done_when": dw}
        for i, dw in enumerate(dws)]}


p = A.inserted_leg_problems(plan("Obtain the FRESH WATER",
                                 {"map": "CELADON_CITY"},
                                 {"map": "CELADON_MART_1F"},
                                 {"has_item": {"FRESH_WATER": 1}}))
ck("a step that IS the displaced leg is refused", len(p) == 2, p)
ck("...naming the leg and why", all("'Reach Celadon City'" in x and "PUT IN FRONT OF" in x for x in p), p)
ck("...and a building the game names after the town counts",
   any("CELADON_MART_1F, which the game names after CELADON_CITY" in x for x in p), p)
ck("...while the step for the leg's own deed is untouched", not any("s2" in x for x in p), p)
ck("steps that stay clear of it are untouched",
   A.inserted_leg_problems(plan("Obtain the FRESH WATER", {"map": "ROUTE_9"},
                                {"map": "LAVENDER_TOWN"})) == [])
ck("a step holding the displaced leg's item is refused",
   len(A.inserted_leg_problems(plan("Obtain the Lift Key", {"has_item": {"SILPH_SCOPE": 1}}))) == 1)
ck("...its own item is not",
   A.inserted_leg_problems(plan("Obtain the Lift Key", {"has_item": {"LIFT_KEY": 1}})) == [])
ck("a step wearing the displaced leg's badge is refused",
   len(A.inserted_leg_problems(plan("Buy a POTION", {"badge": "RAINBOWBADGE"}))) == 1)
ck("a leg nobody inserted is never asked",
   A.inserted_leg_problems(plan("Reach Celadon City", {"map": "CELADON_CITY"})) == [])
A._AUTHORING_GOAL = "Obtain the FRESH WATER"
ck("a draft with no goal field is judged under main's --goal",
   len(A.inserted_leg_problems({"subgoals": plan("x", {"map": "CELADON_CITY"})["subgoals"]})) == 1)
A._AUTHORING_GOAL = None

v = A.validate(plan("Obtain the FRESH WATER", {"map": "CELADON_CITY"},
                    {"has_item": {"FRESH_WATER": 1}}))
ck("validate() carries the refusal", any("PUT IN FRONT OF" in x for x in v), v)
ck("the author's page says it up front",
   "'Reach Celadon City'" in A.inserted_leg_note("Obtain the FRESH WATER")
   and A.inserted_leg_note("Reach Celadon City") == "")
src = (ROOT / "planner/author.py").read_text()
ck("...on every authoring round", "+ _shown + inserted_leg_note(goal) + (" in src)
ck("main remembers --goal for drafts without one",
   "_AUTHORING_GOAL = args.goal" in src and '_AUTHORING_GOAL = _pl.get("goal") or args.goal' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
