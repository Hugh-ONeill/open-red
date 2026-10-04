#!/usr/bin/env python3
"""A round that changed the world gets the step one more round, like a find.

Run 36, 2026-10-04, Pokemon Tower 7F: rounds 12 and 13 of "talk to Mr.
Fuji" beat two Rockets (two flags fired), but the news test counts only
cells, first presses and ways, and both presses read "not visible" because
the Rockets walked up to the party. The hard cap (rounds * 3 + bonuses)
ended the step on round 13 with the third Rocket and MR. FUJI a few cells
on, and the plan walked the party back to Lavender (user: "it defeated the
rockets but didnt talk to fuji").

Pinned by source: the rule sits after the round's own accounting, reads
the party and flag fields of the round snapshot, shares the find
allowance, and never counts one round twice.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(name, ok): checks.append((name, bool(ok)))

src = (ROOT / "planner/executor.py").read_text()
i = src.index("# A ROUND THAT CHANGED THE WORLD IS NOT A ROUND THAT WENT")
blk = src[i:i + 2200]
ck("the snapshot's party and flag fields decide it",
   "(sig1[4], sig1[5]) != (sig0[4], sig0[5])" in blk)
ck("it shares the find allowance, capped at the step's rounds",
   "_news_bonus < rounds" in blk and "_news_bonus += 1" in blk)
ck("a round already credited as a find is not credited twice",
   'getattr(self, "_esc_news_at", None) != rnd' in blk
   and "self._esc_news_at = rnd" in blk)
ck("it is logged and said on the page",
   'news="the world changed"' in blk and "changed the world" in blk)
ck("it sits after the round's own accounting, before the target notes",
   i < src.index("# accumulate targets that failed or did nothing", i))
ck("the loop's ceiling still counts the bonus",
   "while spent < rounds and rnd < rounds * 3 + _fresh_bonus + _news_bonus:" in src)
o1 = {"map": {"id": "POKEMON_TOWER_7F"}, "player": {"x": 9, "y": 12},
      "mode": "overworld", "party": [{"level": 38}], "flags": ["A"]}
o2 = dict(o1, flags=["A", "EVENT_BEAT_POKEMONTOWER_7_TRAINER_0"])
s1, s2 = E.Executor._snapshot(o1), E.Executor._snapshot(o2)
ck("a fired flag changes the snapshot field the rule reads",
   s1[5] != s2[5] and s1[4] == s2[4])

bad = [n for n, ok in checks if not ok]
for n, ok in checks: print(("ok  " if ok else "FAIL"), n)
sys.exit(1 if bad else 0)
