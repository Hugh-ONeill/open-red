#!/usr/bin/env python3
"""A move the run has seen faint its own user ranks behind every move that
can hit, and is chosen only when nothing else can.

Run 27, 2026-09-17: GRAVELER picked SELFDESTRUCT 28 times, 19 of them at
80 hp or more, on Zubats and Spearows — the scorer ranks by power and
130 beats EARTHQUAKE's 100 whenever the effectiveness ties (user: "how
much does graveler choose selfdestruct?"; "keep the default last").

Pinned: the executor reads the self-KO off the turn's own text ("X used
SELFDESTRUCT!" then "X fainted!" with no enemy move between) and keeps the
count across attempts; choose() puts such a move last unless the spec says
self_ko: "free"; the knob is validated and documented. Synthetic.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E        # noqa: E402
import battle_policy as bp  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


tmp = Path(tempfile.mkdtemp())
E.SELF_KO_PATH = tmp / "self_ko.json"
E.SELF_KO.clear()

BEFORE = {"me": {"species": "GRAVELER", "hp": 89, "maxhp": 98},
          "foe": {"species": "ZUBAT", "hp": 44, "maxhp": 44}}


def after(text):
    return {"mode": "battle", "recent_text": text, "party": []}


ck("our move followed by our own faint is a self-KO",
   E._journal_self_ko(BEFORE, after("SAGE used SELFDESTRUCT! / Enemy ZUBAT fainted! / SAGE fainted!"), "SELFDESTRUCT")
   and E.SELF_KO == {"SELFDESTRUCT": 1})
ck("...and it is kept on disk", json.loads(E.SELF_KO_PATH.read_text()) == {"SELFDESTRUCT": 1})
ck("a faint after the enemy's move is not",
   not E._journal_self_ko(BEFORE, after("SAGE used EARTHQUAKE! / Enemy ZUBAT used BITE! / SAGE fainted!"), "EARTHQUAKE"))
ck("the enemy fainting alone is not",
   not E._journal_self_ko(BEFORE, after("SAGE used EARTHQUAKE! / Enemy ZUBAT fainted!"), "EARTHQUAKE"))
ck("the enemy's own selfdestruct is not ours",
   not E._journal_self_ko(BEFORE, after("Enemy GEODUDE used SELFDESTRUCT! / Enemy GEODUDE fainted!"), "MEGA_PUNCH"))
ck("a two-word move is matched as the screen spells it",
   E._journal_self_ko(BEFORE, after("SAGE used MEGA PUNCH! / SAGE fainted!"), "MEGA_PUNCH"))
ck("a mon already down records nothing",
   not E._journal_self_ko({"me": {"hp": 0}, "foe": {}}, after("SAGE used SELFDESTRUCT! / SAGE fainted!"), "SELFDESTRUCT"))

# the policy: last unless free
def obs():
    return {"mode": "battle", "bag": {},
            "party": [{"species": "GRAVELER", "level": 34, "hp": 89, "max_hp": 98},
                      {"species": "LAPRAS", "level": 35, "hp": 100, "max_hp": 149}],
            "battle": {"kind": "wild", "partyIndex": 0, "enemyIndex": 0,
                       "me": {"species": "GRAVELER", "level": 34, "hp": 89, "maxhp": 98,
                              "types": ["ROCK", "GROUND"], "status": None,
                              # the real set, with the accuracies the game gives them: ROCK_THROW's
                              # 65% is why 130 beats 50x2x1.5 against a Flying foe
                              "moves": [{"index": 1, "id": "SELFDESTRUCT", "type": "NORMAL", "power": 130, "accuracy": 100, "pp": 5},
                                        {"index": 2, "id": "ROCK_THROW", "type": "ROCK", "power": 50, "accuracy": 65, "pp": 15},
                                        {"index": 3, "id": "EARTHQUAKE", "type": "GROUND", "power": 100, "accuracy": 100, "pp": 10}]},
                       "foe": {"species": "ZUBAT", "level": 18, "hp": 44, "maxhp": 44,
                               "types": ["POISON", "FLYING"], "status": None, "moves": []}}}


spec = dict(bp.DEFAULT_SPEC, name="t", battle_items=[], setup=[])
ctx = {"turn": 1, "intent": "traversal", "self_ko": {"SELFDESTRUCT": 3}}
bp.reset_run_budget()
r = bp.choose(obs(), spec, ctx)
ck("with the record, the self-KO move is not the pick", r.get("index") != 1 and "SELFDESTRUCT" not in str(r.get("_why")), r)
ck("...the best of the rest is", r.get("index") == 2, r)
r0 = bp.choose(obs(), spec, {"turn": 1, "intent": "traversal"})
ck("with no record it is chosen by power, as before", r0.get("index") == 1, r0)
rf = bp.choose(obs(), dict(spec, self_ko="free"), ctx)
ck('self_ko "free" leaves the scoring alone', rf.get("index") == 1, rf)
o = obs()
o["battle"]["me"]["moves"] = [{"index": 1, "id": "SELFDESTRUCT", "type": "NORMAL", "power": 130, "pp": 5},
                              {"index": 2, "id": "DEFENSE_CURL", "type": "NORMAL", "power": 0, "pp": 30}]
r1 = bp.choose(o, spec, ctx)
ck("when nothing else can hit, it is still chosen", r1.get("index") == 1, r1)
ck("the knob is validated",
   any("self_ko" in p for p in bp.validate_spec(dict(spec, self_ko="sometimes")))
   and not any("self_ko" in p for p in bp.validate_spec(dict(spec, self_ko="free"))))
ck("...and documented for the author",
   'self_ko: "last"|"free"' in (ROOT / "planner/policy_author.py").read_text()
   and 'self_ko: "last"|"free"' in (ROOT / "planner/battle_policy.py").read_text())
src = (ROOT / "planner/executor.py").read_text()
ck("the battle loop records it after every move and hands the record to the policy",
   "if _journal_self_ko(before_b, obs, move_id):" in src
   and '"self_ko": SELF_KO, "want": want,' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
