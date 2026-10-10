#!/usr/bin/env python3
"""A trainee is never handed to a member its own spec would run with.

Route 2, run 45 (2026-10-10): a level step for PIKACHU L3. The train block
sent BULBASAUR L8 in as highest_level while it stood at 4/25, the spec's
flee_wild.hp_below 0.2 ran on the next turn, and that went on for seven
wild fights: 0 exp, PIDGEY L7 at 24/24 never used, then a blackout.

Pinned on that party: the hand-over skips a member under the spec's own
flee line and takes the next by the spec's order; with nobody above the
line it picks as before; a spec with no hp_below is unchanged. Synthetic.
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


def mon(sp, lv, hp, mx, types, slot=None):
    m = {"species": sp, "level": lv, "hp": hp, "max_hp": mx, "types": types,
         "moves": [{"name": "TACKLE", "type": "NORMAL", "power": 35, "pp": 30}]}
    return m


PARTY = [mon("PIKACHU", 3, 5, 15, ["ELECTRIC"]),
         mon("BULBASAUR", 8, 4, 25, ["GRASS", "POISON"]),
         mon("PIDGEY", 7, 24, 24, ["NORMAL", "FLYING"])]
OBS = {"party": PARTY, "mode": "battle",
       "battle": {"kind": "wild",
                  "me": {"species": "PIKACHU", "level": 3, "hp": 5, "maxhp": 15,
                         "slot": 1, "types": ["ELECTRIC"], "moves": PARTY[0]["moves"]},
                  "foe": {"species": "RATTATA", "level": 3, "hp": 15, "maxhp": 15,
                          "types": ["NORMAL"]}}}
TRAIN = json.loads((ROOT / "plans/train_model_v3.json").read_text())["train"]
SPEC = {"flee_wild": {"when_traversal": True, "hp_below": 0.2}, "train": TRAIN}

ck("under its flee line BULBASAUR is passed over for PIDGEY",
   B._train_to(OBS, "highest_level", {1}, 0.2) == 3)
ck("without a flee line the order is unchanged",
   B._train_to(OBS, "highest_level", {1}) == 2)
low = json.loads(json.dumps(OBS))
low["party"][2]["hp"] = 3
ck("with nobody above the line it picks as before",
   B._train_to(low, "highest_level", {1}, 0.2) == 2)

tt = B.train_turn(OBS, SPEC, {"trainee": 1, "turn": 1, "intent": "fight"})
ck("the train turn on run 45's party sends PIDGEY", (tt or {}).get("slot") == 3, tt)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
