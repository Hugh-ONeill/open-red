#!/usr/bin/env python3
"""The new-species question shows the type and species legs ahead, not only
the level legs; and a catch target that got away is remembered with where it
was met while a leg it would answer is still unmet.

Run of record 12 (2026-09-27) said no to every new species through the
ticket stretch, each answer weighing the level legs, the only legs the
question showed, with 22 Poke Balls in the bag. Its one ABRA took a ball
and teleported, and nothing kept it: the battle ended on a throw, which was
read as a catch, so it was not even recorded as leaving (user: "its made
this one stretch easier at the cost of making the next much harder" ... "it
should do both").

Pinned: the question lists the legs still unmet and says which this species
would answer, or none, and that a Pokemon can be left in the PC; with no such
legs it says nothing; a wild that leaves on a throw that caught nothing is
recorded; a catch target that left is kept with its level and map, and
persisted; the page names it while a leg it answers is unmet and forgets it
once one of its kind is owned. Synthetic.
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


GOALS = [{"pos": 29, "leg": "the party holds a FIRE or PSYCHIC type",
          "types": {"FIRE", "PSYCHIC"}, "species": set()},
         {"pos": 51, "leg": "the party holds a WATER or ELECTRIC type",
          "types": {"WATER", "ELECTRIC"}, "species": set()}]
real = E.outline_ahead.catch_goals_ahead
E.outline_ahead.catch_goals_ahead = lambda *a, **k: list(GOALS)
ex = object.__new__(E.Executor)
ex._species_names = lambda: set()

w = ex._party_type_legs_words([], "CLEFAIRY", ["NORMAL"])
ck("the question lists the legs still unmet",
   'leg 29: "the party holds a FIRE or PSYCHIC type"' in w and "leg 51" in w, w)
ck("...says when this one answers none of them", "THIS ONE would answer none of them" in w)
ck("...and that a Pokemon can be left in the PC",
   "left in the PC at any Pokemon Center" in w and "counts only the Pokemon in the party" in w)
w = ex._party_type_legs_words([], "DROWZEE", ["PSYCHIC"])
ck("...and names the leg one would answer", "THIS ONE would answer leg 29" in w, w)
E.outline_ahead.catch_goals_ahead = lambda *a, **k: []
ck("with no such legs it says nothing", ex._party_type_legs_words([], "X", []) == "")
E.outline_ahead.catch_goals_ahead = lambda *a, **k: list(GOALS)

src = (ROOT / "planner/executor.py").read_text()
ck("the question carries it after the level legs",
   '+ self._party_type_legs_words(party, sp, foe.get("types"))' in src)
ck("a wild that leaves on a throw that caught nothing is recorded as leaving",
   'and not (name == "throw_ball" and _caught)' in src
   and '_pc0 = len((obs or {}).get("pc_mons") or [])' in src)
ck("a catch target that left is kept with its level and map, and persisted",
   'if ctx.get("intent") == "catch":\n                GOT_AWAY[' in src
   and '"got_away": GOT_AWAY,' in src and 'GOT_AWAY.update(data.get("got_away") or {})' in src)

E.GOT_AWAY.clear()
E.GOT_AWAY["ABRA"] = {"level": 10, "map": "ROUTE_24", "types": ["PSYCHIC"]}
line = ex._got_away_line({"party": [{"species": "IVYSAUR"}]})
ck("the page names it while a leg it answers is unmet",
   "ABRA L10 on ROUTE_24 (would answer leg 29" in line
   and "whether to look is yours" in line, line)
ck("...and forgets it once one of its kind is owned",
   ex._got_away_line({"party": [{"species": "ABRA"}]}) == ""
   and ex._got_away_line({"party": [], "pc_mons": [{"species": "ABRA"}]}) == "")
E.outline_ahead.catch_goals_ahead = lambda *a, **k: [GOALS[1]]
ck("...and once no leg ahead needs its kind", ex._got_away_line({"party": []}) == "")
E.outline_ahead.catch_goals_ahead = real
E.GOT_AWAY.clear()

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
