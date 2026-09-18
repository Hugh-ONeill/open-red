#!/usr/bin/env python3
"""A gift a full bag refused is remembered, and listed while the bag has
room.

Run 27, 2026-09-18: ERIKA was beaten with 20 kinds in the bag and said "You
should make room for this." instead of handing over TM21; a beaten leader
hands it over when spoken to again, but nothing kept the line, and the run
never went back (user: "something that would get the bot to cycle back to
a gift with a non-full bag").

Pinned: a no-room line after a won fight is recorded against the trainer
and the map; a pressed thing that answered "No more room for items!" is
read from the hints; both are listed only while the bag has room, with the
distance, and drop off once a thing arrived from that giver or the ball is
gone; the move-slot question is not a gift; the record is saved and
loaded. Synthetic.
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


def fake():
    ex = object.__new__(E.Executor)
    ex._refused_gifts = {}
    ex._item_from = {}
    ex._gone = {}
    ex.hints = {}
    ex.visits = {"CELADON_GYM|0,1": 3, "SILPH_CO_10F|8,0": 2, "SAFARI_ZONE_WEST|26,0": 4}
    ex._where = lambda o: "FUCHSIA_CITY|2,2"
    ex._route = lambda a, b: [None] * 12
    ex._save_memory = lambda: None
    ex.log = lambda *a, **k: None
    ex._last_overworld_map = "CELADON_GYM"
    return ex


ex = fake()
before = {"battle": {"trainer": "ERIKA", "leader": True, "foe": {"species": "VILEPLUME", "level": 29}}}
after = {"mode": "overworld", "party": [{"species": "VENUSAUR", "hp": 50}],
         "recent_text": "ERIKA: Oh! I concede defeat. / You should make room for this.",
         "map": {"id": "CELADON_GYM"}}
import tempfile
_j = tempfile.NamedTemporaryFile("w+", suffix=".jsonl", delete=False)
ex.logf = _j                      # the recap reads its fight from the journal
ex._EFF_WORDS = getattr(E.Executor, "_EFF_WORDS", {})
ex._note_fight(before, after, 0)
ck("a no-room line after a won fight is recorded against the trainer and map",
   ex._refused_gifts.get("CELADON_GYM|ERIKA", {}).get("said") == "You should make room for this.", ex._refused_gifts)

ex.hints = {"SILPH_CO_10F|8,0": ["ITEM_SILPH_CO_10F_5_11: No more room for items!"],
            "DIGLETTS_CAVE|4,4": ["grind: ROCKY is trying to learn HARDEN! Delete an older move to make room for HARDEN?"]}
room = {"bag": {f"X{i}": 1 for i in range(18)}}
line = ex._refused_gifts_line(room)
ck("with room in the bag, the refused gifts are listed with the distance",
   line.startswith("THINGS YOUR FULL BAG REFUSED, and the bag has room now (18 of 20 kinds): ")
   and 'ERIKA in CELADON_GYM said "You should make room for this." after the fight — 12 walked leg(s) away' in line
   and "a ball at (5,11) in SILPH_CO_10F" in line, line)
ck("...the move-slot question is not a gift", "HARDEN" not in line)
ck("with the bag full, nothing is listed", ex._refused_gifts_line({"bag": {f"X{i}": 1 for i in range(20)}}) == "")
ex._gone = {"SILPH_CO_10F|8,0": {"ITEM_SILPH_CO_10F_5_11"}}
ex._item_from = {"TM_MEGA_DRAIN": {"who": "CELADONGYM_ERIKA", "at": "CELADON_GYM|0,1", "said": "..."}}
ck("a gift that has since arrived, and a ball that is gone, drop off", ex._refused_gifts_line(room) == "",
   ex._refused_gifts_line(room))

src = (ROOT / "planner/executor.py").read_text()
ck("it rides the page beside the PC lines", "_rs_line = (self._refused_gifts_line(obs)" in src)
ck("the record is saved and loaded",
   '"refused_gifts": getattr(self, "_refused_gifts", {}),' in src
   and 'self._refused_gifts = data.get("refused_gifts") or {}' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
