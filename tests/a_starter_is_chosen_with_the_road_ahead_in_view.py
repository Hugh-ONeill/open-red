#!/usr/bin/env python3
"""A question that names a Pokemon is put to the model with its own
outline's party goals still ahead on the page.

Run 18's starter was not a choice: after rounds of pressing balls, the
model pressed the one at 6,3, the game asked "So! You want the fire
POKéMON, CHARMANDER?", and it said yes to a page that carried nothing of
its own outline — which asked for a WATER or GRASS type before Brock,
GRASS or ELECTRIC before Misty and GROUND before Surge, three of which
one BULBASAUR answers and CHARMANDER none. Leg 5 then went looking for
grass that is not there (user, 2026-09-16: "if its taking into account
further type requirments it might actually choose an easier starter that
can fulfil that").

Pinned here: the goals appear when the question names a species the game
knows, not otherwise; only the legs ahead of the run's mark, only the
ones a Pokemon answers, and none the party in hand already meets; the
rest of the page is as it was. Which goal a species answers is never
said — that is the model's to know.

Synthetic: no game, no model.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import executor as E           # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


OUTLINE = """Choose a starter Pokémon
Retrieve the Poké Ball from the Pallet Town resident
the party has at least 2 Pokemon
Reach Pewter City
the party holds a WATER or GRASS type
every party member is at least level 12
Defeat Brock for the Boulder Badge
the party holds a GRASS or ELECTRIC type
Defeat Misty for the Cascade Badge
the party holds a GROUND type
the party holds a FIRE or PSYCHIC type
"""

tmp = Path(tempfile.mkdtemp(prefix="starter_ahead_"))
plans, run = tmp / "plans", tmp / "run"
plans.mkdir()
run.mkdir()
(plans / "outline.txt").write_text(OUTLINE)
(run / "outline_leg").write_text("0\n")

live_plans, live_run = E.PLANS, E.RUN
E.PLANS = plans
E.bind_run(run)

ex = object.__new__(E.Executor)
SG = {"id": "pick_starter", "goal_text": "Choose a starter Pokemon"}
OBS = {"mode": "ui", "map": {"id": "OAKS_LAB"}, "party": [],
       "bag": {}}

STARTER = "So! You want the fire POKéMON, CHARMANDER?"
page = ex._question_text(OBS, SG, STARTER)
HEAD = "YOUR OWN OUTLINE, STILL AHEAD, ASKS THE PARTY TO BECOME:"
ck("the starter question carries the road ahead", HEAD in page)
ck("the type legs ahead are on it, numbered as the outline numbers them",
   "  5. the party holds a WATER or GRASS type" in page
   and "  8. the party holds a GRASS or ELECTRIC type" in page
   and "  10. the party holds a GROUND type" in page
   and "  11. the party holds a FIRE or PSYCHIC type" in page)
ck("a level leg is not on it", "level 12" not in page)
ck("a badge is not on it", "Brock" not in page)
ck("'at least 2 Pokemon' is not on it", "at least 2 Pokemon" not in page)
ck("which goal CHARMANDER answers is not said",
   "FIRE or PSYCHIC" in page and "CHARMANDER answers" not in page
   and "Charmander is" not in page)
ck("the judgement is left where it belongs",
   "is yours to judge" in page)
ck("the rest of the page is as it was",
   f'THE QUESTION ON SCREEN:\n"{STARTER}"' in page
   and "WHERE YOU ARE: OAKS_LAB" in page
   and "YOUR PARTY: no Pokemon" in page
   and "YOUR BAG: an empty bag" in page
   and page.rstrip().endswith("Answer it."))
ck("the road ahead sits before the closing line",
   page.index(HEAD) < page.index("Saying yes and saying no"))

ck("a question that names no Pokemon carries no outline",
   HEAD not in ex._question_text(OBS, SG, "Kid, do you want to play?"))
ck("nor does the fossil's",
   HEAD not in ex._question_text(OBS, SG, "You want the HELIX FOSSIL?"))
ck("the Dojo's HITMONLEE gets the same page",
   HEAD in ex._question_text(OBS, SG,
                             "You want the hard kicking HITMONLEE?"))

# a party in hand: what it already meets is not asked for again
with_char = {**OBS, "party": [{"species": "CHARMANDER", "level": 5,
                               "types": ["FIRE"]}]}
page2 = ex._question_text(with_char, SG,
                          "You want the water POKéMON, SQUIRTLE?")
ck("a goal the party meets is not on the page",
   "FIRE or PSYCHIC" not in page2 and "WATER or GRASS" in page2)

# the mark moves: legs behind it are gone
(run / "outline_leg").write_text("8\n")
page3 = ex._question_text(OBS, SG, STARTER)
ck("legs behind the run's mark are not ahead",
   "WATER or GRASS" not in page3 and "GRASS or ELECTRIC" not in page3
   and "GROUND type" in page3)

# nothing ahead: no empty heading
(run / "outline_leg").write_text("11\n")
ck("an outline with nothing ahead adds nothing",
   HEAD not in ex._question_text(OBS, SG, STARTER))

# ---- the escalation page's box-up line carries it too -----------------------
# Run 19's starter was answered INSIDE an escalation round, with
# menu(index=1), from ledger.render's "a box is up, saying" line; the
# yes/no asker above never ran (2026-09-16).
import ledger as L                                            # noqa: E402
(run / "outline_leg").write_text("0\n")
box = {"mode": "ui", "map": {}, "party": [],
       "recent_text": STARTER}
lpage = L.render([], ex, box)
ck("the escalation page's box line carries the road ahead",
   f'a box is up, saying: "{STARTER}"' in lpage and HEAD in lpage
   and "  5. the party holds a WATER or GRASS type" in lpage)
ck("...and a box naming no Pokemon does not",
   HEAD not in L.render([], ex, dict(box, recent_text="Kid, do you want to play?")))

E.PLANS = live_plans
E.bind_run(live_run)
failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
