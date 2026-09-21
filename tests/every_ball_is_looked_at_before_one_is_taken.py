#!/usr/bin/env python3
"""The offer question makes the model say what EACH ball would answer before
it names the one it takes.

Asked for a reason and a name, the starter pick was decided by which ball
was listed first. Forty asks of the executor's own question against run
28's authored outline at leg 0 (2026-09-21, no game): BULBASAUR listed first
-> BULBASAUR 13 of 13 ("satisfies both the water/grass and grass/electric
requirements"); anything else first -> CHARMANDER 27 of 27 ("fulfills the
requirement for a FIRE type"); SQUIRTLE never. One in three, the shuffle's
odds, and the record agreed: three CHARMANDER to two BULBASAUR in five
starts (user: "i kind of want to trust the model to usually be able to pick
bulba on the notion that it clears two objectives"). It could — it only
looked when BULBASAUR was the first thing it read.

With the reply made to carry an "each" object, one entry per ball saying
which of the numbered objectives that ball would answer, the same forty
asks took BULBASAUR 36, SQUIRTLE 4 (it answers two legs as well) and
CHARMANDER 0, in every list order. No fact is added: the objectives and the
judgment are the model's, given once per ball.

Pinned: the each-format is used when there are objectives to hold the balls
against and the plain one when there are none; the wording is the wording
that was measured; it names no Pokemon and no type; the pick is still read
from "take"; what was said of each ball is journalled, listed balls only; a
reply with no "each" still counts; none is still none; junk is still handed
back to the round. Synthetic."""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ORDER = [("ITEM_OAKS_LAB_7_3", "So! You want the water POKéMON, SQUIRTLE?"),
         ("ITEM_OAKS_LAB_6_3", "So! You want the fire POKéMON, CHARMANDER?"),
         ("ITEM_OAKS_LAB_8_3", "So! You want the plant POKéMON, BULBASAUR?")]
GOALS = ("\nYOUR OWN OUTLINE, STILL AHEAD, ASKS THE PARTY TO BECOME:\n"
         "  6. the party holds a WATER or GRASS type\n"
         "  11. the party holds a GRASS or ELECTRIC type\n"
         "  23. the party holds a FIRE or PSYCHIC type\n"
         "Which of those each of these Pokemon would answer is yours to "
         "judge; the party in hand answers none of them yet.")
seen = {}


def new():
    ex = E.Executor.__new__(E.Executor)
    ex.logf = io.StringIO()
    ex.t0 = time.time()
    ex.model = "m"
    return ex


def ask(reply, goals=GOALS):
    def chat(msgs, model, **kw):
        seen["sys"], seen["user"] = msgs[0]["content"], msgs[1]["content"]
        return reply if isinstance(reply, str) else json.dumps(reply)
    E.brock_probe.chat = chat
    ex = new()
    got = ex._ask_offer_choice({"id": "pick_starter"}, {"party": []},
                               ORDER, goals)
    rows = [json.loads(l) for l in ex.logf.getvalue().splitlines()]
    return got, rows


EACH = {"ITEM_OAKS_LAB_7_3": "6", "ITEM_OAKS_LAB_6_3": "23",
        "ITEM_OAKS_LAB_8_3": "6 and 11", "ITEM_OAKS_LAB_9_9": "everything"}
got, rows = ask({"each": EACH, "why": "two of them", "take": "ITEM_OAKS_LAB_8_3"})
S = E.Executor.OFFER_CHOICE_EACH_SYS
ck("with objectives on the page, every ball is asked about",
   seen["sys"] == S and '"each"' in S)
ck("...one entry for every ball listed, before the reason and the pick",
   "one entry for every ball listed" in S
   and S.index('"each"') < S.index('"why"') < S.index('"take"'))
ck("the wording is the wording that was measured",
   "<which of the numbered objectives below this one would answer, or none>"
   in S)
ck("it names no Pokemon and no type, and tells nothing to pick",
   not any(w in S.upper() for w in ("BULBASAUR", "CHARMANDER", "SQUIRTLE",
                                    "GRASS", "FIRE", "WATER", "MOST",
                                    "BEST", "SHOULD")))
ck("the objectives it points at are on the page it is asked on",
   "  6. the party holds a WATER or GRASS type" in seen["user"]
   and all(n in seen["user"] for n, _ in ORDER))
ck("the pick is still read from take",
   got == ("ITEM_OAKS_LAB_8_3", "two of them"), got)
_row = [r for r in rows if r["kind"] == "offer_choice"][-1]
ck("what it said of each ball is kept beside the pick",
   _row["each"].get("ITEM_OAKS_LAB_8_3") == "6 and 11"
   and _row["each"].get("ITEM_OAKS_LAB_6_3") == "23", _row)
ck("...for the balls that were listed and no others",
   "ITEM_OAKS_LAB_9_9" not in _row["each"] and len(_row["each"]) == 3)
ck("...with the order they were listed in, as before",
   _row["order"] == [n for n, _ in ORDER])

got, rows = ask({"why": "x", "take": "ITEM_OAKS_LAB_6_3"})
ck("a reply that leaves each out still counts",
   got == ("ITEM_OAKS_LAB_6_3", "x")
   and [r for r in rows if r["kind"] == "offer_choice"][-1]["each"] == {})
got, rows = ask({"each": "all of them", "why": "x", "take": "ITEM_OAKS_LAB_6_3"})
ck("...and so does one that writes it as something else",
   got == ("ITEM_OAKS_LAB_6_3", "x"))
got, rows = ask({"each": EACH, "why": "not yet", "take": "None"})
ck("none is still none", got == ("none", "not yet"), got)
got, rows = ask({"each": EACH, "why": "x", "take": "the green one"})
ck("a name that is no ball is still handed back to the round",
   got is None and any(r["kind"] == "offer_choice_unparsed" for r in rows))
got, rows = ask("I would take Bulbasaur.")
ck("...and so is a reply that is not an object", got is None)

got, rows = ask({"why": "x", "take": "ITEM_OAKS_LAB_7_3"}, goals="")
ck("with no objectives on the page, the plain question is asked",
   seen["sys"] == E.Executor.OFFER_CHOICE_SYS
   and '"each"' not in E.Executor.OFFER_CHOICE_SYS
   and "numbered objectives" not in seen["sys"])
ck("...and answered as it always was", got == ("ITEM_OAKS_LAB_7_3", "x"))

SRC = (ROOT / "planner/executor.py").read_text()
ck("the survey still shuffles the list and logs the order",
   "_random.shuffle(order)" in SRC and 'self.log("offer_table_surveyed"' in SRC)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
