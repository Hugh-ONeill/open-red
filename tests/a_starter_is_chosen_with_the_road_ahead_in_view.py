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


asked_pages = []


def fake_chat(msgs, model):
    asked_pages.append(msgs)
    return '{"why": "It covers the grass legs.", "take": "ITEM_OAKS_LAB_7_3"}'


E.brock_probe.chat = fake_chat
tx = object.__new__(T)
tx.model = "test"
tx._last_overworld_pos = (5, 5)
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
presses = [s for s in sent if s[0] == "interact"]
ck("each other ball is pressed and answered no",
   presses[:2] == [("interact", {"name": "ITEM_OAKS_LAB_7_3"}),
                   ("interact", {"name": "ITEM_OAKS_LAB_8_3"})]
   and sum(1 for s in sent if s == ("tap", {"btn": "b"})) == 3)
ck("the survey itself answers nothing yes",
   not any(s[0] == "tap" and s[1].get("btn") == "a" for s in sent)
   and not any(s[1].get("answer") for s in presses[:2]))
ck("the party walks back to where the model stood before choosing",
   ("walk_to", {"x": 5, "y": 5}) in sent
   and sent.index(("walk_to", {"x": 5, "y": 5}))
   < sent.index(presses[-1]))
page = asked_pages[-1][1]["content"] if asked_pages else ""
ck("the choice is asked as its own question, with every offer",
   asked_pages and all(f'"{w}"' in page for w in QUESTIONS.values())
   and "take" in asked_pages[-1][0]["content"])
ck("...and the outline's goals", HEAD in page
   and "  5. the party holds a WATER or GRASS type" in page)
ck("...and no 'also standing' line, since all of them are named",
   "Also standing on this map" not in page)
ck("the model's pick is pressed with yes, and only its pick",
   presses[-1] == ("interact", {"name": "ITEM_OAKS_LAB_7_3", "answer": "yes"})
   and len(presses) == 3)
ck("the round says what was chosen and why",
   line and 'you chose ITEM_OAKS_LAB_7_3: "It covers the grass legs."' in line)
_surv = [kw for k, kw in tx.logged if k == "offer_table_surveyed"]
ck("the survey is logged with what each asked and the order shown",
   _surv and len(_surv[-1]["asked"]) == 3
   and sorted(_surv[-1]["order"]) == sorted(QUESTIONS))
_ch = [kw for k, kw in tx.logged if k == "offer_choice"]
ck("the choice is logged with its reason and the order it saw",
   _ch and _ch[-1]["take"] == "ITEM_OAKS_LAB_7_3"
   and _ch[-1]["why"] == "It covers the grass legs."
   and page.index(_ch[-1]["order"][0]) < page.index(_ch[-1]["order"][-1]))
# the order is shuffled: over many surveys, every ball is shown first
import random as _rnd
firsts = set()
for _i in range(40):
    _t = object.__new__(T)
    _t.model = "test"
    _t._send_safe = fake_send
    _t.settle = lambda: {"mode": "overworld", "party": []}
    _t.logged = []
    _t.log = lambda k, _l=_t.logged, **kw: _l.append((k, kw))
    _t._last_overworld_map = "OAKS_LAB"
    _t._last_overworld_items = list(QUESTIONS)
    _t._survey_offer_table({"id": "p"}, "interact",
                           {"name": "ITEM_OAKS_LAB_6_3"}, opened)
    firsts.add([kw for k, kw in _t.logged
                if k == "offer_table_surveyed"][-1]["order"][0])
ck("the offers are not always listed in the same order", len(firsts) == 3)


def none_chat(msgs, model):
    return '{"why": "Not yet.", "take": "none"}'


E.brock_probe.chat = none_chat
sent.clear()
_t = object.__new__(T)
_t.model = "test"
_t._send_safe = fake_send
_t.settle = lambda: {"mode": "overworld", "party": []}
_t.log = lambda k, **kw: None
_t._last_overworld_map = "OAKS_LAB"
_t._last_overworld_items = list(QUESTIONS)
_nl = _t._survey_offer_table({"id": "p"}, "interact",
                             {"name": "ITEM_OAKS_LAB_6_3"}, opened)
ck("'none' takes nothing", _nl and "you said none" in _nl
   and not any(s[1].get("answer") for s in sent))


def junk_chat(msgs, model):
    return "I'd like the fire one please"


E.brock_probe.chat = junk_chat
_t2 = object.__new__(T)
_t2.model = "test"
_t2._send_safe = fake_send
_t2.settle = lambda: {"mode": "overworld", "party": []}
_t2.log = lambda k, **kw: None
_t2._last_overworld_map = "OAKS_LAB"
_t2._last_overworld_items = list(QUESTIONS)
_jl = _t2._survey_offer_table({"id": "p"}, "interact",
                              {"name": "ITEM_OAKS_LAB_6_3"}, opened)
ck("an unreadable answer hands the offers to the round instead",
   _jl and '"answer":"yes"' in _jl and "Which, if any, is yours." in _jl
   and HEAD in _jl)
sent.clear()
ck("a table is surveyed once",
   tx._survey_offer_table({"id": "pick_starter"}, "interact",
                          {"name": "ITEM_OAKS_LAB_7_3", "answer": "yes"},
                          dict(opened, recent_text=QUESTIONS["ITEM_OAKS_LAB_7_3"]))
   is None and not sent)
# the fossils too (user, 2026-09-16), and ONLY the balls beside the one
# that asked: B2F's HP_UP and TM lie on the same floor and a press takes them
FOSSILS = {"ITEM_MT_MOON_B2F_12_6": "You want the DOME FOSSIL?",
           "ITEM_MT_MOON_B2F_13_6": "You want the HELIX FOSSIL?"}
fsent = []


def fossil_send(op, **kw):
    fsent.append((op, kw))
    if op == "interact":
        w = FOSSILS.get(kw["name"], "Found HP_UP!")
        return {"mode": "ui", "recent_text": w,
                "result": {"ok": True,
                           "detail": (f"{kw['name']} {E.ASKING} — \"{w}\""
                                      if kw["name"] in FOSSILS else "ok")}}
    return {"mode": "overworld"}


E.brock_probe.chat = lambda m, mo: '{"why": "x", "take": "none"}'
tx2 = object.__new__(T)
tx2.model = "test"
tx2._send_safe = fossil_send
tx2.settle = lambda: {"mode": "overworld", "party": []}
tx2.log = lambda k, **kw: None
tx2._last_overworld_map = "MT_MOON_B2F"
tx2._last_overworld_items = ["ITEM_MT_MOON_B2F_12_6", "ITEM_MT_MOON_B2F_13_6",
                             "ITEM_MT_MOON_B2F_25_21", "ITEM_MT_MOON_B2F_29_5"]
fl = tx2._survey_offer_table({"id": "x"}, "interact",
                             {"name": "ITEM_MT_MOON_B2F_12_6"},
                             {"recent_text": "You want the DOME FOSSIL?"})
ck("the fossils are a table too",
   fl and '"You want the DOME FOSSIL?"' in fl
   and '"You want the HELIX FOSSIL?"' in fl)
ck("...and the HP_UP and the TM on the same floor are never pressed",
   [s[1]["name"] for s in fsent if s[0] == "interact"]
   == ["ITEM_MT_MOON_B2F_13_6"])
ck("...and no goals block rides on a fossil",
   fl and HEAD not in fl)
tx3 = object.__new__(T)
tx3._send_safe = fake_send
tx3._last_overworld_map = "OAKS_LAB"
tx3._last_overworld_items = ["ITEM_OAKS_LAB_8_3"]
ck("a ball with nothing beside it is not a table",
   tx3._survey_offer_table({"id": "x"}, "interact",
                           {"name": "ITEM_OAKS_LAB_8_3"},
                           {"recent_text": QUESTIONS["ITEM_OAKS_LAB_8_3"]}) is None)
# THE FOSSILS AS THE PAGE NAMES THEM (run 27, 2026-09-16): not ITEM_x_y
# balls but MTMOONB2F_DOME_FOSSIL / MTMOONB2F_HELIX_FOSSIL, found by cell
NAMED = {"MTMOONB2F_DOME_FOSSIL": "You want the DOME FOSSIL?",
         "MTMOONB2F_HELIX_FOSSIL": "You want the HELIX FOSSIL?"}
nsent = []


def named_send(op, **kw):
    nsent.append((op, kw))
    if op == "interact":
        w = NAMED.get(kw["name"])
        if w:
            return {"mode": "ui", "recent_text": w,
                    "result": {"ok": True, "detail": f"{kw['name']} {E.ASKING}"}}
        return {"mode": "ui", "recent_text": "Hey!", "result": {"ok": True,
                                                                "detail": "ok"}}
    return {"mode": "overworld"}


E.brock_probe.chat = lambda m, mo: '{"why": "x", "take": "none"}'
tn = object.__new__(T)
tn.model = "test"
tn._send_safe = named_send
tn.settle = lambda: {"mode": "overworld", "party": []}
tn.log = lambda k, **kw: None
tn._last_overworld_map = "MT_MOON_B2F"
tn._last_overworld_items = ["ITEM_MT_MOON_B2F_25_21", "ITEM_MT_MOON_B2F_29_5"]
tn._last_overworld_objs = [("MTMOONB2F_DOME_FOSSIL", 12, 6),
                           ("MTMOONB2F_HELIX_FOSSIL", 13, 6),
                           ("MTMOONB2F_SUPER_NERD", 12, 8),
                           ("ITEM_MT_MOON_B2F_25_21", 25, 21)]
nl = tn._survey_offer_table({"id": "x"}, "interact",
                            {"name": "MTMOONB2F_DOME_FOSSIL"},
                            {"recent_text": "You want the DOME FOSSIL?"})
ck("fossils named for what they are are surveyed by where they stand",
   nl and '"You want the HELIX FOSSIL?"' in nl
   and [s[1]["name"] for s in nsent if s[0] == "interact"]
   == ["MTMOONB2F_HELIX_FOSSIL"])
tg = object.__new__(T)
tg.model = "test"
tg._send_safe = named_send
tg._last_overworld_map = "GAME_CORNER_PRIZE_ROOM"
tg._last_overworld_objs = [("GAMECORNERPRIZEROOM_CLERK1", 4, 2),
                           ("GAMECORNERPRIZEROOM_CLERK2", 5, 2)]
ck("the prize counter's offer is not a table to survey",
   tg._survey_offer_table({"id": "x"}, "interact",
                          {"name": "GAMECORNERPRIZEROOM_CLERK1"},
                          {"recent_text": "So, you want PORYGON?"}) is None)
_src = (ROOT / "planner/executor.py").read_text()
ck("the room sweep runs the survey when a press is left asking",
   '_tbl = self._survey_offer_table(\n                                sg, "interact", {"name": name}, o2)'
   in _src)
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
