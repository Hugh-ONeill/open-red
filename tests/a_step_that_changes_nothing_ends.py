#!/usr/bin/env python3
"""A step fails fast when its rounds change nothing.

Run 36, 2026-10-03: leg 27 rode Celadon's store floors and streets for a
dozen rounds a step, half an hour a plan, with no flag, item or badge
changing; each first sign press earned a bonus round (user: "shouldnt it be
failing fast because its not walking any new ground or doing anything new").

Pinned: (1) news counts people, items and real ground, not signs, vending
text or machines, nor a handful of cells; (2) six rounds in a row with the
same world mark, nothing new and only maps already stood on this step end
the step, and the rewrite's journal says so."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
ex = object.__new__(E.Executor)
ex.explored = {}
ex._tried_objs = {"CELADON_MART_2F|1,1": {"CELADONMART2F_CLERK1"}}
obs = {"map": {"id": "CELADON_MART_2F", "seen": {"n": 100}}}
before = ex._news_snapshot(obs)
ex._tried_objs["CELADON_MART_2F|1,1"] |= {"SIGN_CELADON_MART_2F_14_1",
                                          "TEXT_CELADONMART2F_CLERK2"}
ck("a sign and vending text pressed for the first time are not news",
   ex._round_news(before, obs) == "", ex._round_news(before, obs))
ex._tried_objs["CELADON_MART_2F|1,1"] |= {"CELADONMART2F_SUPER_NERD"}
ck("a person pressed for the first time is",
   "1 person/thing(s) pressed" in ex._round_news(before, obs), ex._round_news(before, obs))
before2 = ex._news_snapshot(obs)
obs8 = {"map": {"id": "CELADON_MART_2F", "seen": {"n": 108}}}
ck("eight new cells are not news", ex._round_news(before2, obs8) == "")
obs30 = {"map": {"id": "CELADON_MART_2F", "seen": {"n": 130}}}
ck("thirty are", "30 cell(s) newly on screen" in ex._round_news(before2, obs30))
ck("slot machines and the PC are fixtures",
   ex._fixture_name("SLOT_MACHINE_3") and ex._fixture_name("CELADON_POKECENTER_PC")
   and not ex._fixture_name("GAMECORNER_ROCKET"))
src = (ROOT / "planner/executor.py").read_text()
ck("six idle rounds end the step", "IDLE_STREAK_END = 6" in src
   and "if self._idle_streak >= self.IDLE_STREAK_END:" in src and "spent = rounds" in src)
ck("idle means same world, nothing new, a map already stood on this step",
   "if (_same_world and _seen_map" in src
   and "_news_now = self._round_news(self._round0_news, start)" in src
   and "if (_same_world and _seen_map and not _news_now" in src)
# a grind round changes no badge, flag or bag kind, and still is not idle
# (run 36's grind_haunter was ended after thousands of exp, 2026-10-04)
ck("a round that gained experience or levels is not idle",
   "and not _trained):" in src
   and "self._round0_exp = self._party_exp(start)" in src)
_o1 = {"party": [{"species": "HAUNTER", "level": 30, "exp": 20000}]}
_o2 = {"party": [{"species": "HAUNTER", "level": 30, "exp": 21845}]}
ck("...where experience is read from the party itself",
   E.Executor._party_exp(_o1) != E.Executor._party_exp(_o2)
   and E.Executor._party_exp(_o1) == E.Executor._party_exp(dict(_o1)))
au = (ROOT / "planner/author.py").read_text()
ck("the rewrite's journal says the step was ended for it", 'k == "step_idle_end"' in au)
failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
sys.exit(1 if failed else 0)
