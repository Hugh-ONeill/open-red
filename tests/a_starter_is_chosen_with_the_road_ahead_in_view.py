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

# ---- the other balls on the table ---------------------------------------------
# Run 20 took the first ball it pressed "to satisfy the future goal of
# having a FIRE type", with the two beside it on screen and unpressed
# (user, 2026-09-16: "add the other balls line").
ex._last_overworld_map = "OAKS_LAB"
ex._last_overworld_items = ["ITEM_OAKS_LAB_6_3", "ITEM_OAKS_LAB_7_3",
                            "ITEM_OAKS_LAB_8_3"]
ex._tried_objs = {"OAKS_LAB|4,1": {"OAKSLAB_OAK1"}}
ex._last_press = ("OAKS_LAB", "ITEM_OAKS_LAB_6_3")
lpage2 = L.render([], ex, box)
ck("the other balls standing on the map are named",
   "standing on this map: ITEM_OAKS_LAB_7_3, ITEM_OAKS_LAB_8_3." in lpage2)
ck("...not the one whose question is on screen",
   "ITEM_OAKS_LAB_6_3" not in lpage2.split("standing on this map:", 1)[1])
ck("...and saying no is said to leave it where it is",
   "answering no to this one leaves it where it is" in lpage2)
ck("which ball to press is not said",
   "BULBASAUR" not in lpage2 and "SQUIRTLE" not in lpage2)
# run 21 pressed all three before Oak walked in, when each only said
# "Those are POKé BALLs"; they still stand, and are still named
ex._tried_objs = {"OAKS_LAB|4,1": {"ITEM_OAKS_LAB_6_3", "ITEM_OAKS_LAB_7_3",
                                   "ITEM_OAKS_LAB_8_3"}}
ck("balls pressed before the offer are still named",
   "standing on this map: ITEM_OAKS_LAB_7_3, ITEM_OAKS_LAB_8_3."
   in L.render([], ex, box))
ex._last_overworld_items = ["ITEM_OAKS_LAB_6_3"]
ck("with no other ball standing, no line",
   "standing on this map" not in L.render([], ex, box))
ex._last_overworld_items = ["ITEM_OAKS_LAB_6_3", "ITEM_OAKS_LAB_7_3",
                            "ITEM_OAKS_LAB_8_3"]
ex._tried_objs = {}
ck("the yes/no asker's page names them too",
   "standing on this map: ITEM_OAKS_LAB_7_3, ITEM_OAKS_LAB_8_3."
   in ex._question_text(OBS, SG, STARTER))

# ---- offers only (user, 2026-09-16: "narrow it to offers") -----------------
# Every question in the game's text table that names a Pokemon, as it reads
# on screen (escapes and {RAM:...} names filled in).
OFFERS = [
    "So! You want the plant POKéMON, BULBASAUR?",
    "So! You want the water POKéMON, SQUIRTLE?",
    "You want the hard kicking HITMONLEE?",
    "You want the piston punching HITMONCHAN?",
    "MAN: Hello, there! Have I got a deal just for you! I'll let you have a "
    "swell MAGIKARP for just ¥500! What do you say?",
    "So, you want PORYGON?",
    "I'm looking for ABRA! Wanna trade one for MR.MIME?",
    "Hello there! Do you want to trade your POLIWHIRL for JYNX?",
    "Hi! Do you have SPEAROW? Want to trade it for FARFETCH'D?",
]
MENTIONS = [
    "CATERPIE evolves into BUTTERFREE?",
    "POLIWAG evolves 3 times?",
    "Good! Then listen up! My favorite RAPIDASH... It...cute... lovely..."
    "smart... plus...amazing... you think so?",
    "How's your POKéDEX coming, pal? I just caught a CUBONE! I can't find "
    "the grown-up MAROWAK yet! I doubt there are any left! Well, I better "
    "get going! I've got a lot to accomplish, pal! Smell ya later!",
    "My GROWLITHE... Why did you die?",
    "You came from MT. MOON? May I have a CLEFAIRY?",
    "RATTATA may be small, but its bite is wicked! Did you get one?",
    "My EEVEE evolved into FLAREON! But, a friend's EEVEE turned into a "
    "VAPOREON! I wonder why?",
    "Do you want to give a nickname to CHARMANDER?",
    "What? That's not ABRA! If you get one, come back here!",
    "You want the HELIX FOSSIL?",
]
for w in OFFERS:
    ck(f"an offer carries the road ahead: {w[-40:]}",
       HEAD in L.render([], ex, dict(box, recent_text=w)))
for w in MENTIONS:
    ck(f"a mention does not: {w[:40]}",
       HEAD not in L.render([], ex, dict(box, recent_text=w)))

# ---- every ball on the table is asked before any is taken -------------------
# Runs 20-22 each pressed the leftmost ball first, read CHARMANDER's
# question and said yes, with the other two unread (user, 2026-09-16:
# "forcing it to press through with no and reveal each pokemon before
# presenting it with its ultimate choice").
QUESTIONS = {"ITEM_OAKS_LAB_6_3": "So! You want the fire POKéMON, CHARMANDER?",
             "ITEM_OAKS_LAB_7_3": "So! You want the water POKéMON, SQUIRTLE?",
             "ITEM_OAKS_LAB_8_3": "So! You want the plant POKéMON, BULBASAUR?"}
sent = []


def fake_send(op, **kw):
    sent.append((op, kw))
    if op == "interact":
        w = QUESTIONS[kw["name"]]
        return {"mode": "ui", "recent_text": w,
                "result": {"ok": True, "detail": f"{kw['name']} {E.ASKING} — \"{w}\""}}
    return {"mode": "overworld"}


class T(E.Executor):
    pass


tx = object.__new__(T)
tx._send_safe = fake_send
tx.settle = lambda: {"mode": "overworld", "party": []}
tx.logged = []
tx.log = lambda k, **kw: tx.logged.append((k, kw))
tx._last_overworld_map = "OAKS_LAB"
tx._last_overworld_items = list(QUESTIONS)
(run / "outline_leg").write_text("0\n")
opened = {"mode": "ui", "recent_text": QUESTIONS["ITEM_OAKS_LAB_6_3"], "party": []}
line = tx._survey_offer_table({"id": "pick_starter"}, "interact",
                              {"name": "ITEM_OAKS_LAB_6_3", "answer": "yes"},
                              opened)
ck("the first question is answered no before anything else",
   sent and sent[0] == ("tap", {"btn": "b"}))
ck("each other ball is pressed and answered no",
   [s for s in sent if s[0] == "interact"]
   == [("interact", {"name": "ITEM_OAKS_LAB_7_3"}),
       ("interact", {"name": "ITEM_OAKS_LAB_8_3"})]
   and sum(1 for s in sent if s == ("tap", {"btn": "b"})) == 3)
ck("nothing is ever answered yes by the survey",
   not any(s[0] == "tap" and s[1].get("btn") == "a" for s in sent)
   and not any(s[1].get("answer") for s in sent))
ck("the round hands back all three offers",
   line and all(f'"{w}"' in line for w in QUESTIONS.values()))
ck("...says nothing has been taken and each still stands",
   line and "nothing has been taken and each still stands" in line)
ck("...says how to take one, and leaves which to the model",
   line and '"answer":"yes"' in line and "Which, if any, is yours." in line)
ck("...with the outline's goals",
   line and HEAD in line and "  5. the party holds a WATER or GRASS type" in line)
ck("...and no 'also standing' line, since all of them are named",
   line and "Also standing on this map" not in line)
ck("the survey is logged with what each asked",
   tx.logged and tx.logged[-1][0] == "offer_table_surveyed"
   and len(tx.logged[-1][1]["asked"]) == 3)
sent.clear()
ck("a table is surveyed once",
   tx._survey_offer_table({"id": "pick_starter"}, "interact",
                          {"name": "ITEM_OAKS_LAB_7_3", "answer": "yes"},
                          dict(opened, recent_text=QUESTIONS["ITEM_OAKS_LAB_7_3"]))
   is None and not sent)
tx2 = object.__new__(T)
tx2._send_safe = fake_send
tx2._last_overworld_map = "MT_MOON_B2F"
tx2._last_overworld_items = ["ITEM_MT_MOON_B2F_5_6", "ITEM_MT_MOON_B2F_6_6"]
ck("a fossil's question is not an offer table",
   tx2._survey_offer_table({"id": "x"}, "interact",
                           {"name": "ITEM_MT_MOON_B2F_5_6"},
                           {"recent_text": "You want the DOME FOSSIL?"}) is None)
tx3 = object.__new__(T)
tx3._send_safe = fake_send
tx3._last_overworld_map = "OAKS_LAB"
tx3._last_overworld_items = ["ITEM_OAKS_LAB_8_3"]
ck("a ball with nothing beside it is not a table",
   tx3._survey_offer_table({"id": "x"}, "interact",
                           {"name": "ITEM_OAKS_LAB_8_3"},
                           {"recent_text": QUESTIONS["ITEM_OAKS_LAB_8_3"]}) is None)
ck("the survey runs where the macro stops for a question",
   "self._survey_offer_table(sg, op, step, obs)" in
   (ROOT / "planner/executor.py").read_text())

E.PLANS = live_plans
E.bind_run(live_run)
failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
