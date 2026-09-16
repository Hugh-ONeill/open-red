#!/usr/bin/env python3
"""A box after a catch is not a party pick.

Every successful catch ends on "Do you want to give a nickname to X?", and
the battle loop read ANY ui screen as the forced "Use next POKeMON?" pick:
it sent pick_party, which presses A up to sixty times looking for a party
menu, answering the nickname question — or whatever box was up — yes. One
catch room's trials logged thirty of them with a one-Pokemon party that
never fainted (2026-09-16). Pinned: no pick on a nickname box; a pick on
the party menu, on "use next", and under a battle frame, as before.

Synthetic: a fake bridge, no game.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import executor as E          # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


class Bridge:
    def __init__(self):
        self.sent = []

    def send(self, op, **kw):
        self.sent.append(op)
        return {"mode": "overworld", "result": {"ok": True}}

    def obs(self):
        return {"mode": "overworld"}


PARTY = [{"species": "VILEPLUME", "level": 40, "hp": 118, "max_hp": 122},
         {"species": "PIKACHU", "level": 24, "hp": 50, "max_hp": 50}]


def run(obs):
    b = Bridge()
    E._run_policy(E.battle_policy.DEFAULT_SPEC, b, obs, lambda *a, **k: None,
                  5, intent="catch")
    return b.sent


ck("a nickname box after a catch sends no pick",
   "pick_party" not in run({"mode": "ui", "party": PARTY,
                            "recent_text": "Do you want to give a nickname "
                                           "to PIKACHU?"}))
ck("the new-Pokedex-data box sends no pick either",
   "pick_party" not in run({"mode": "ui", "party": PARTY,
                            "recent_text": "New POKéDEX data will be added "
                                           "for PIKACHU!"}))
fainted = [dict(PARTY[0], hp=0), PARTY[1]]
ck("'Use next POKeMON?' still sends a pick",
   "pick_party" in run({"mode": "ui", "party": fainted,
                        "recent_text": "Use next POKéMON?"}))
ck("the party menu itself still sends a pick",
   "pick_party" in run({"mode": "ui", "party": fainted,
                        "ui": {"screenId": "PartyMenu"}}))
ck("the party menu under a battle frame still sends a pick",
   "pick_party" in run({"mode": "battle", "party": fainted,
                        "battle": {"behind_a_menu": "PartyMenu",
                                   "me": None}}))

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
