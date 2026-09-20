#!/usr/bin/env python3
"""The outline's STAGES are asked whether the run can take them in that
order, and a stage moves whole; and the hand-pick judge counts a town
reached before the town that opens it.

Run 28's outline was nearly ideal except for its order (user, 2026-09-20:
"if you ignore the out of order bits the outline is pretty ideal" …
"basically the ordering issue here was in which towns were included in
which stages"). It grouped "Celadon & Saffron City" before "Lavender &
Fuchsia City": Lavender gates the road to Celadon, Celadon sells the drink
Saffron's guards want, so the run spent an afternoon at a shut gate and the
ladder then tore the list apart one leg at a time.

It hid because the BADGE order was perfect, Boulder through Earth (user:
"its hard to tell in this case because badge order is correct"). Only a
town with no badge was out of place, so the judge now reads the order the
towns are ARRIVED in against the order the game lets a run reach them.

Pinned: the stage question asks only about order; a null answer leaves the
list alone; an answer that is not the same stages back is refused; a real
answer moves whole stages with their objectives in their own order; the
judge flags Celadon and Saffron before Lavender, ranks a draft with that
fault below one without, and says the badge order can be perfect while it
is wrong. Synthetic."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import brock_probe  # noqa: E402
import compare_outlines as C  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


LEGS = ["Reach Celadon City", "Defeat Erika for the Rainbow Badge",
        "Reach Saffron City", "Defeat Sabrina for the Marsh Badge",
        "Reach Lavender Town", "Clear the Pokemon Tower",
        "Reach Fuchsia City", "Defeat Koga for the Soul Badge"]
STAGES = {LEGS[0]: "Celadon & Saffron", LEGS[1]: "Celadon & Saffron",
          LEGS[2]: "Celadon & Saffron", LEGS[3]: "Celadon & Saffron",
          LEGS[4]: "Lavender & Fuchsia", LEGS[5]: "Lavender & Fuchsia",
          LEGS[6]: "Lavender & Fuchsia", LEGS[7]: "Lavender & Fuchsia"}
THIRD = {"Reach Cinnabar Island": "Cinnabar"}
LEGS3 = LEGS + ["Reach Cinnabar Island"]
ST3 = dict(STAGES, **THIRD)


def ask(answer, legs=LEGS3, stages=ST3):
    brock_probe.chat = lambda msgs, model, **kw: json.dumps(answer)
    return A._stage_order("Become the Champion", legs, stages, "m")


ck("the question is about the order of the stages and nothing else",
   "ORDER OF THE STAGES" in A.STAGE_ORDER_SYS
   and "not rewriting anything" in " ".join(A.STAGE_ORDER_SYS.split())
   and '"order": ["<stage>", "<stage>",' in A.STAGE_ORDER_SYS)

ck("the blocks are the stages in the order the list does them",
   [nm for nm, _ in A._stage_blocks(LEGS3, ST3)]
   == ["Celadon & Saffron", "Lavender & Fuchsia", "Cinnabar"])

ck("a null answer leaves the list exactly as it was",
   ask({"why": "it is fine", "order": None}) == LEGS3)
ck("...and so does an answer that drops a stage",
   ask({"why": "x", "order": ["Lavender & Fuchsia", "Cinnabar"]}) == LEGS3)
ck("...or invents one",
   ask({"why": "x", "order": ["Lavender & Fuchsia", "Celadon & Saffron",
                              "Cinnabar", "Indigo"]}) == LEGS3)
ck("...or gives back the order it already had",
   ask({"why": "x", "order": ["Celadon & Saffron", "Lavender & Fuchsia",
                              "Cinnabar"]}) == LEGS3)

moved = ask({"why": "Lavender opens the road to Celadon",
             "order": ["Lavender & Fuchsia", "Celadon & Saffron", "Cinnabar"]})
ck("a real answer moves the stage whole",
   moved[:4] == LEGS[4:8] and moved[4:8] == LEGS[0:4]
   and moved[8] == "Reach Cinnabar Island", moved)
ck("...with each stage's own objectives in their own order",
   moved.index("Reach Lavender Town") < moved.index("Clear the Pokemon Tower")
   and moved.index("Reach Celadon City")
   < moved.index("Defeat Erika for the Rainbow Badge"))
ck("nothing is added or dropped", sorted(moved) == sorted(LEGS3))

src = (ROOT / "planner/author.py").read_text()
ck("the pass runs before the stage-missing question",
   src.index("_ordered = _stage_order(")
   < src.index("_dedupe_outline(_stage_missing(goal, legs, stages, model))"))
ck("...and the stages are taken again after a move",
   "stages = _stage_outline(legs, model) or stages" in src)

# --------------------------------------------------- the judge's column
BAD = ["Reach Cerulean City", "Reach Vermilion City", "Reach Celadon City",
       "Reach Saffron City", "Reach Lavender Town", "Reach Fuchsia City"]
GOOD = ["Reach Cerulean City", "Reach Vermilion City", "Reach Lavender Town",
        "Reach Celadon City", "Reach Saffron City", "Reach Fuchsia City"]
jb, jg = C.judge(BAD), C.judge(GOOD)
ck("a town reached before the one that opens it is flagged",
   ("celadon", "lavender") in jb["reach_bad"]
   and ("saffron", "lavender") in jb["reach_bad"], jb["reach_bad"])
ck("...and the right order is not", jg["reach_bad"] == [], jg["reach_bad"])
ck("the flag says which way round it has to be",
   any("Celadon is reached before Lavender" in f for f in jb["flags"]),
   jb["flags"][:3])
ck("a draft with the fault ranks below one without",
   C.rank(jg) < C.rank(jb) and C.rank(jb)[1] == 2 and C.rank(jg)[1] == 0)
ck("the badge order alone cannot show it",
   jb["badges"] == jg["badges"] == "")
ck("the order the towns open in is named once",
   C.REACH_ORDER.index("lavender") < C.REACH_ORDER.index("celadon")
   < C.REACH_ORDER.index("saffron") < C.REACH_ORDER.index("fuchsia")
   < C.REACH_ORDER.index("cinnabar"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
