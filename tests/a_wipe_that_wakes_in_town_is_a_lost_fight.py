#!/usr/bin/env python3
"""A wipe that wakes the party in a town is a lost fight.

This recomp respawns a wiped party on the town map, not in a Center: run
46's lone BULBASAUR L8 and PIDGEY L4 lost to Pewter gym's JR.TRAINER and
woke in VIRIDIAN_CITY, and the fight was kept as won ("lost": false), as
run 45's Viridian Forest wipe had been (2026-10-10). Probed on the real
game from run 46's leg-3 save: the same fight now records "lost": true.

Pinned: a new map, the whole party at full HP and less money than the
fight began with is a loss; a won fight on the same map is not. Synthetic.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def recap(after_map, hp, money_after):
    ex = E.Executor.__new__(E.Executor)
    ex.logf = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    ex.logf.write(json.dumps({"kind": "battle_turn", "op": "battle_move",
                              "why": "TACKLE score=33", "foe": "DIGLETT L11",
                              "foe_hp": 6}) + "\n")
    ex.logf.flush()
    ex._last_overworld_map = "PEWTER_GYM"
    ex.logged = []
    ex.log = lambda kind, **kw: ex.logged.append((kind, kw))
    before = {"money": 225, "map": {"id": None},
              "battle": {"kind": "trainer", "trainer": "JR.TRAINER♂",
                         "foe": {"species": "DIGLETT", "level": 11}},
              "party": [{"species": "BULBASAUR", "level": 8, "hp": 26, "max_hp": 26},
                        {"species": "PIDGEY", "level": 4, "hp": 18, "max_hp": 18}]}
    after = {"money": money_after, "map": {"id": after_map},
             "party": [{"species": "BULBASAUR", "level": 8, "hp": hp, "max_hp": 26},
                       {"species": "PIDGEY", "level": 4, "hp": 18, "max_hp": 18}]}
    ex._note_fight(before, after, 0)
    return next((kw for k, kw in ex.logged if k == "fight_recap"), {})


r = recap("VIRIDIAN_CITY", 26, 112)
ck("woke in Viridian, healed and poorer: lost", r.get("lost") is True, r)
r = recap("PEWTER_GYM", 20, 400)
ck("a won fight on the same map is not lost", r.get("lost") is False, r)
r = recap("VIRIDIAN_CITY", 26, 400)
ck("a new map with more money is not a wipe", r.get("lost") is False, r)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
