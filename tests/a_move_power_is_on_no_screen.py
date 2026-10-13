#!/usr/bin/env python3
"""A move's power is on no screen, so the model is not shown it.

Gen 1's FIGHT menu shows a known move's TYPE and PP, the summary its PP;
power is printed nowhere, and a move not yet learned is only its name. The
level-up and TM questions said "power 80" beside RAZOR_WIND and "power 35"
beside WING_ATTACK, PIDGEOTTO gave up its only FLYING move for a two-turn
NORMAL one, and every page carried "power" on each party move and the
machines ledger's type, power and PP for moves nobody knew (run 54,
2026-10-13; user: "you cant know beforehand what the power is and all that
its not on the pamphlet").
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E                                           # noqa: E402

fails = []


def ck(name, cond, det=""):
    print(("ok   " if cond else "FAIL ") + name + ("" if cond else f"  {str(det)[:300]}"))
    if not cond:
        fails.append(name)


OBS = {"party": [{"species": "PIDGEOT", "level": 39, "types": ["NORMAL", "FLYING"],
                  "dvs": {"atk": 9},
                  "moves": [{"id": "RAZOR_WIND", "type": "NORMAL", "power": 80, "pp": 10, "max_pp": 10},
                            {"id": "SAND_ATTACK", "type": "NORMAL", "power": 0, "pp": 15, "max_pp": 15}]}],
       "machines": {"TM_MEGA_DRAIN": {"move": "MEGA_DRAIN", "able": ["VENUSAUR"], "not_able": [],
                                      "type": "GRASS", "power": 40, "max_pp": 10}},
       "map": {"name": "ROUTE_16"}}
v = E.model_view(OBS)
txt = json.dumps(v)
ck("the page carries no move power", '"power"' not in txt, txt)
ck("...but a known move keeps its type and PP",
   v["party"][0]["moves"][0] == {"id": "RAZOR_WIND", "type": "NORMAL", "pp": 10, "max_pp": 10},
   v["party"][0]["moves"])
ck("a machine's move is a name and its ABLE list",
   v["machines"]["TM_MEGA_DRAIN"] == {"move": "MEGA_DRAIN", "able": ["VENUSAUR"], "not_able": []},
   v["machines"])
ck("the raw observation is untouched (the engine still reads it)",
   OBS["party"][0]["moves"][0]["power"] == 80 and OBS["machines"]["TM_MEGA_DRAIN"]["power"] == 40)
ck("the hidden numbers stay hidden too", "dvs" not in v["party"][0])

w = E._known_move_words({"id": "WING_ATTACK", "type": "FLYING", "power": 35, "pp": 30, "max_pp": 35})
ck("a known move reads name, type and PP", w == "WING_ATTACK (FLYING, PP 30/35)", w)
ck("a bare name stays a name", E._known_move_words("TACKLE") == "TACKLE")

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all ok'}")
sys.exit(1 if fails else 0)
