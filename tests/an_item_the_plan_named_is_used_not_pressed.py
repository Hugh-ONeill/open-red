#!/usr/bin/env python3
"""A round whose plan says "use the <item>" and whose ops only pressed A is
told which op uses an item.

Run 27, 2026-09-17, Route 12: "I have the Poké Flute. I will return to
Route 12, use the Poké Flute on Snorlax" — and the macro was cross,
interact(ROUTE12_SNORLAX), cross, three rounds running, each answered "A
sleeping POKéMON blocks the way!" (user: "keeps on interacting with snorlax
instead of using the pokeflute, even though its thinking is saying 'use
the poke flute'").

Pinned: only an item the plan named with a using verb, only one the bag
holds, only in a round that pressed something and used nothing; the note
names the op and says it acts where you stand; it rides the round's
feedback beside the go note. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ex = object.__new__(E.Executor)
BAG = {"bag": {"POKE_FLUTE": 1, "POTION": 3}}
MACRO = [{"op": "cross", "dir": "east"},
         {"op": "interact", "name": "ROUTE12_SNORLAX", "answer": "yes"},
         {"op": "cross", "dir": "west"}]
PLAN = "I have the Poké Flute. I will return to Route 12, use the Poké Flute on Snorlax to wake it up."
got = ex._use_item_would_have(MACRO, PLAN, BAG)
ck("an item named with 'use' in a round that pressed A is told the op",
   got.startswith("(You said use the POKE FLUTE; this round pressed A on ROUTE12_SNORLAX and used no item.")
   and '{"op":"use_item","item":"POKE_FLUTE"}' in got and "where you stand" in got, got)
ck("...the accent in the plan's spelling does not matter",
   ex._use_item_would_have(MACRO, "I will play the Poke Flute next to it", BAG) != "")
ck("a round that used an item is left alone",
   ex._use_item_would_have(MACRO + [{"op": "use_item", "item": "POKE_FLUTE"}], PLAN, BAG) == "")
ck("a travel-only round is left alone (the use may be later)",
   ex._use_item_would_have([{"op": "cross", "dir": "east"}], PLAN, BAG) == "")
ck("an item the bag does not hold is not offered",
   ex._use_item_would_have(MACRO, PLAN, {"bag": {"POTION": 3}}) == "")
ck("naming an item without a using verb says nothing",
   ex._use_item_would_have(MACRO, "I have the Poke Flute in my bag. I will talk to Snorlax.", BAG) == "")
ck("no plan words, nothing", ex._use_item_would_have(MACRO, "", BAG) == "")
src = (ROOT / "planner/executor.py").read_text()
ck("it rides the round's feedback beside the go note",
   "_ui_note = self._use_item_would_have(" in src
   and src.index("_ui_note = self._use_item_would_have(") > src.index("_go_note = self._go_would_have(macro, self._plan_said)"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:240]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
