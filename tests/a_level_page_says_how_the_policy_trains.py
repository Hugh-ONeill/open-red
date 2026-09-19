#!/usr/bin/env python3
"""A level step's page says that experience is shared by the Pokemon that
took part, what the pinned policy's train rule does with the trainee, and
(for a slot condition) which Pokemon the condition is reading.

The how-to line said "only what fights, earns", which is not the game's
rule: a Pokemon that started a battle and was switched out earns its share
(manual tier). And a slot_level page never said who its slot held: the
target key carries the condition's value as its printed form, and every
line below asked isinstance(dw_val, dict) of a string, so the branch was
dead from the day it was written (found 2026-09-19).

Pinned: the split fact is on the page; the train rule is put in words
(lead, the fight conditions, the else); a spec with no rule says the
trainee is switched IN instead; the slot line names the pinned Pokemon and
how far short it is; the pin's DVs are not printed. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


class Bare(E.Executor):
    """An executor with no game: anything it was never given is empty."""

    def __init__(self):
        pass

    def __getattr__(self, n):
        return {}


ex = Bare()
ex.log = lambda *a, **k: None
party = [{"species": "LAPRAS", "level": 55, "hp": 200, "max_hp": 250,
          "types": ["WATER", "ICE"]},
         {"species": "MACHOP", "level": 24, "hp": 70, "max_hp": 74,
          "types": ["FIGHTING"], "dvs": {"hp": 3}, "otId": 9}]
sg = {"id": "train_machop", "goal_text": "Train Machop",
      "done_when": {"slot_level": {
          "slot": 2, "min": 30,
          "who": {"species": "MACHOP", "dvs": {"hp": 3}, "otId": 9}}}}
ex._cur_sg = sg
obs = {"party": party, "map": {"id": "ROUTE_1"}, "mode": "overworld"}

E.ACTIVE_SPEC = {"flee_wild": {"hp_below": 0.3},
                 "train": {"lead": True,
                           "fight_if": {"min_level_ratio": 0.9,
                                        "min_hp_frac": 0.5},
                           "else": "switch", "to": "highest_level"}}
t = ex.training_text(obs, ex._target_key(sg))
ck("the page says experience is shared by those that took part",
   "Experience is SHARED among your Pokemon that took part" in t, t[-600:])
ck("...and no longer that only what fights earns",
   "only what fights, earns" not in t and "only what takes part, earns" in t)
ck("the train rule is put in words for the trainee",
   "YOUR BATTLE POLICY'S TRAIN RULE, for MACHOP L24" in t, t[-500:])
ck("...who walks in first", "it is moved to the front before a grind" in t)
ck("...when it fights",
   "its level is at least 0.9x the wild's and its HP is at 50% or more" in t)
ck("...and what happens otherwise",
   "switched out on the spot for your highest level member and shares" in t)
ck("the slot line names the pinned Pokemon and how far short it is",
   "it is in slot 2 now: MACHOP (FIGHTING) L24 right now, still 6 short "
   "of L30" in t, t[:700])
ck("...and the pin's DVs are not printed", "'dvs'" not in t and "otId" not in t)

E.ACTIVE_SPEC = {"train": {"lead": False, "else": "flee",
                           "fight_if": {"min_matchup": 2}}}
w = ex._train_words(obs, sg)
ck("a flee rule and an unled trainee are said as such",
   "the party order is left as you set it" in w
   and "hits the wild for x2 or better" in w
   and "otherwise the battle is fled" in w, w)
E.ACTIVE_SPEC = {"train": {"lead": True}}
ck("a rule with no conditions fights everything",
   "it fights every wild itself" in ex._train_words(obs, sg))
E.ACTIVE_SPEC = {"flee_wild": {"hp_below": 0.3}}
w = ex._train_words(obs, sg)
ck("a spec with no rule says the trainee is switched IN",
   "has no train rule" in w and "switched IN on the first turn" in w, w)
ck("...and still says the split", "Experience is SHARED" in w)
ck("a step with no trainee gets the fact alone",
   ex._train_words(obs, {"done_when": {"map": "ROUTE_1"}}).strip()
   .startswith("Experience is SHARED")
   and "TRAIN RULE" not in ex._train_words(obs, {"done_when": {"map": "X"}}))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
