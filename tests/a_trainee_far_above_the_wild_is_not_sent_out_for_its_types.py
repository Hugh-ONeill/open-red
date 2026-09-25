#!/usr/bin/env python3
"""A trainee far enough above the wild is not sent out for its types, when
the train rule says where "far enough" is.

Run of record 3, 2026-09-24/25: the train rule (train_model_v1) fought a
wild only when "this wild's types hit it for no more than x1.5". On Route 6
ODDISH hits ROCK/GROUND x4 and MANKEY x2, so GEODUDE, then GRAVELER, went
out on turn one 161 times, 87 of them at twice the wild's level or more;
VENUSAUR finished those fights and went L30 -> L54 while the trainee
stalled at 29 (user: "it shouldnt be doing that after the point at which
graveler could train itself"). The type conditions are read before a hit
is thrown, so nothing the run records could ever lift them. The user chose
a new word in the rule (2026-09-25), its number the model's, and a room
that asks the question.

Pinned: types_ignored_at_level_ratio lifts both type conditions at or
above its ratio and nowhere below; left out, types always count; it is a
valid key in range and documented for the author; the spec-age line files
it with the train words; the outleveled room is built and scored with the
other three; the rule in play is scored beside every new one. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as bp  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


GRAV = {"level": 29, "hp": 80, "max_hp": 82, "types": ["ROCK", "GROUND"],
        "moves": [{"id": "ROCK_THROW", "type": "ROCK", "power": 50, "pp": 10}]}
ODD = {"species": "ODDISH", "level": 13, "hp": 40, "types": ["GRASS", "POISON"]}
V1 = {"min_level_ratio": 0.8, "min_hp_frac": 0.4, "max_foe_matchup": 1.5}

ck("the rule in play sends a L29 GRAVELER out against a L13 ODDISH",
   bp.train_fights(GRAV, ODD, V1)[0] is False)
ck("with the word at 2.0 it fights: 29/13 is past it",
   bp.train_fights(GRAV, ODD, dict(V1, types_ignored_at_level_ratio=2.0)) == (True, ""))
ck("...and not below it: a L20 still goes out",
   bp.train_fights(dict(GRAV, level=20), ODD,
                   dict(V1, types_ignored_at_level_ratio=2.0))[0] is False)
ck("min_matchup is lifted the same way",
   bp.train_fights(GRAV, ODD, {"min_matchup": 2.0})[0] is False
   and bp.train_fights(GRAV, ODD, {"min_matchup": 2.0,
                                   "types_ignored_at_level_ratio": 2.0})[0] is True)
ck("...and the level and HP conditions are not",
   bp.train_fights(dict(GRAV, hp=10), ODD,
                   dict(V1, types_ignored_at_level_ratio=2.0))[0] is False)
ck("the word is valid in range and refused outside it",
   not bp._train_problems({"fight_if": dict(V1, types_ignored_at_level_ratio=1.5)})
   and bp._train_problems({"fight_if": dict(V1, types_ignored_at_level_ratio=0.5)}))
pa = (ROOT / "planner/policy_author.py").read_text()
ck("the author is told what it does",
   "types_ignored_at_level_ratio\n                        when the trainee's level divided by the wild's is" in pa
   and '"types_ignored_at_level_ratio": 1.0-5.0}' in pa)
sa = (ROOT / "planner/spec_age.py").read_text()
ck("the spec-age line files it with the train words",
   '"types_ignored_at_level_ratio"}' in sa)
gg = (ROOT / "planner/gin_gym_arenas.py").read_text()
ck("the outleveled room is Route 6 with a GEODUDE far above its wilds",
   'dict(name="train_outleveled", map="ROUTE_6"' in gg and '("GEODUDE", 22)]' in gg)
ck("...and it is scored with the other three",
   'TRAIN_ROOMS = ("train_early", "train_mid", "train_late", "train_outleveled")' in pa)
ck("the rule in play is scored beside every new one, so it has to be beaten",
   'f"the rule in play now ({Path(_cur).stem})"' in pa
   and "for label, block in _baselines:" in pa)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
