#!/usr/bin/env python3
"""best_matchup weighs level before types.

Pewter gym, run 46 (2026-10-10): BULBASAUR L11 at full HP out against the
JR.TRAINER's DIGLETT L11. The policy's turn-1 rule "switch to best_matchup
vs trainers" sent PIDGEY L5 in (Flying is immune to Ground), it was knocked
out, BULBASAUR then beat DIGLETT on its own and fell to SANDSHREW: four
fights, four blackouts, money 225 -> 14 (user: "make the best matchup
change").

Pinned on that party: no switch is made; a member under 0.7 of the foe's
level ranks after one at or above it; within a tier the matchup still
decides; a lead read with no foe level uses the party's highest. Synthetic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as B  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def mv(name, typ, power):
    return {"name": name, "type": typ, "power": power, "pp": 20}


BULB = {"species": "BULBASAUR", "level": 11, "hp": 33, "max_hp": 33,
        "types": ["GRASS", "POISON"], "moves": [mv("TACKLE", "NORMAL", 35)]}
PIDG = {"species": "PIDGEY", "level": 5, "hp": 20, "max_hp": 20,
        "types": ["NORMAL", "FLYING"], "moves": [mv("GUST", "NORMAL", 40)]}
PIKA = {"species": "PIKACHU", "level": 3, "hp": 15, "max_hp": 15,
        "types": ["ELECTRIC"], "moves": [mv("THUNDERSHOCK", "ELECTRIC", 40)]}
OBS = {"party": [BULB, PIDG, PIKA],
       "battle": {"kind": "trainer",
                  "me": dict(BULB, maxhp=33, slot=1),
                  "foe": {"species": "DIGLETT", "level": 11, "types": ["GROUND"]}}}
SPEC = json.loads((ROOT / "plans/policy_model_v20.json").read_text())

ck("run 46's turn 1: no switch away from BULBASAUR",
   B.should_switch(OBS, SPEC, {"turn": 1}) is None)
ck("best_matchup picks BULBASAUR over PIDGEY L5",
   B.choose_replacement(OBS, {"replacement": {"order": "best_matchup"}}) == 1)
even = json.loads(json.dumps(OBS))
even["party"][1]["level"] = 11
ck("within a tier the matchup decides: PIDGEY L11 is picked",
   B.choose_replacement(even, {"replacement": {"order": "best_matchup"}}) == 2)
ck("...and then the turn-1 rule does switch", B.should_switch(even, SPEC, {"turn": 1}) == 2)
ck("a lead with no foe level reads the party's highest",
   B._level_tier(PIDG, B._level_ref({}, [BULB, PIDG])) == 0
   and B._level_tier(BULB, B._level_ref({}, [BULB, PIDG])) == 1)
ck("the training hand-over reads it too",
   B._train_to(dict(OBS, party=[PIKA, PIDG, BULB],
                    battle=dict(OBS["battle"], me=dict(PIKA, slot=1))),
               "best_matchup", {1}) == 3)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
