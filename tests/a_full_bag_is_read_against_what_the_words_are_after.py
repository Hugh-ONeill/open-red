#!/usr/bin/env python3
"""A full bag is read against what the round's own words are after, on the
page and as a question at a PC.

Run 27, 2026-09-18: the step was "enter the Cinnabar Gym" while every round
said "I need the Secret Key"; the full-bag line was on the page, and the
run walked out of the Center at 20/20 on the hunt for the key (user: "its
walking out of the center with a full bag on a quest for an item"; "its not
in the plan, just in the thinking, is the thing").

Pinned: the items the words need and the bag lacks are read with the need
tally's rule; at 20/20 the bag line opens with them; at a PC with a full
bag they draw one question per visit, and the chosen items are stored;
no words, no PC, or room in the bag, no question. Synthetic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


FULL = {k: 1 for k in ("BICYCLE", "CALCIUM", "CARBOS", "CARD_KEY", "ESCAPE_ROPE", "FRESH_WATER",
                       "HM_CUT", "HM_STRENGTH", "HM_SURF", "IRON", "LIFT_KEY", "MASTER_BALL",
                       "MAX_POTION", "NUGGET", "OLD_ROD", "POKE_FLUTE", "RARE_CANDY",
                       "SILPH_SCOPE", "TM_BLIZZARD", "TM_PSYCHIC_M")}
WORDS = "The Cinnabar Gym is locked. I need the Secret Key, which is located in the Pokemon Mansion."
ex = object.__new__(E.Executor)
ck("the words' needed item the bag lacks is read", ex._words_want_items(WORDS, FULL) == ["SECRET_KEY"])
ck("...a held item is not", ex._words_want_items("I need the Silph Scope.", FULL) == [])
ck("...and no need word, nothing", ex._words_want_items("The Secret Key is somewhere.", FULL) == [])

ex = object.__new__(E.Executor)
ex._plan_said = WORDS
ex.plan = {"subgoals": []}
ex._usable_on_a_mon = lambda spare: []
ex._where_the_slot_goes = lambda obs: ""
line = ex._bag_line({"bag": FULL, "key_items": [], "map": {"objects": []}}, {"done_when": {"map": "CINNABAR_GYM"}})
ck("at 20/20 the bag line opens with what the words are after",
   line.startswith("\nYOUR OWN WORDS SAY YOU ARE AFTER SECRET_KEY, and a full bag will refuse it when you find it."), line[:200])

asked, sent = [], []


def fake(answer):
    ex = object.__new__(E.Executor)
    ex._plan_said = WORDS
    ex.model = "m"
    ex.log = lambda *a, **k: None
    ex._where = lambda o: "CINNABAR_POKECENTER|0,3"
    ex.settle = lambda: None
    ex._send_safe = lambda op, **kw: (sent.append((op, kw)) or {"result": {"ok": True}})
    E.brock_probe.chat = lambda msgs, model: (asked.append(msgs[1]["content"]) or json.dumps(answer))
    return ex


PC = {"mode": "overworld", "bag": FULL, "key_items": ["CARD_KEY", "LIFT_KEY"],
      "map": {"objects": [{"name": "PC", "reachable": True}]}}
ex = fake({"why": "the key needs a slot", "store": ["nugget", "TM_BLIZZARD", "NOT_HELD"]})
ex._ask_store_for_room(PC, {"id": "enter_cinnabar_gym"})
ck("at a PC with a full bag, the words' want draws a question",
   asked and "WHAT YOUR OWN WORDS SAY YOU ARE AFTER: SECRET_KEY" in asked[-1] and "CARD_KEY x1 (key item)" in asked[-1], asked[-1:])
ck("...and the chosen items it holds are stored",
   sent == [("store_item", {"item": "NUGGET"}), ("store_item", {"item": "TM_BLIZZARD"})], sent)
n = len(asked)
ex._ask_store_for_room(PC, {"id": "enter_cinnabar_gym"})
ck("...once per visit", len(asked) == n)
for why, o, words in (("no PC", dict(PC, map={"objects": []}), WORDS),
                      ("room in the bag", dict(PC, bag={"POTION": 1}), WORDS),
                      ("no item in the words", PC, "I will explore the basement.")):
    ex = fake({"store": ["NUGGET"]}); ex._plan_said = words; n = len(asked)
    ex._ask_store_for_room(o, {"id": "x"})
    ck(f"no question with {why}", len(asked) == n)
src = (ROOT / "planner/executor.py").read_text()
ck("it is asked at the round boundary beside the standing order",
   "start = self._stow_at_pc(start, sg) or start\n            start = self._ask_store_for_room(start, sg) or start" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
