#!/usr/bin/env python3
"""A switch rule may say "no_effect": fire when no damaging move the active mon
has PP for can touch the foe (all 0x on the chart).

Run 54 (2026-10-12): PIKACHU used THUNDERSHOCK on BROCK's ONIX eight turns
running, Onix on 5 HP and a full BULBASAUR on the bench, three blackouts. The
language had no word for it (out_of_pp is the nearest); the user chose a word
the model opts into. v20 does not carry it and is unchanged.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import battle_policy as BP  # noqa: E402
import policy_author  # noqa: E402
import spec_age  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


def mv(i, t, p, pp=20):
    return {"id": i, "type": t, "power": p, "pp": pp}


ONIX = {"species": "ONIX", "level": 14, "hp": 5, "maxhp": 40, "types": ["ROCK", "GROUND"]}
PIK_ME = {"species": "PIKACHU", "hp": 33, "maxhp": 33, "types": ["ELECTRIC"],
          "moves": [mv("THUNDERSHOCK", "ELECTRIC", 40), mv("GROWL", "NORMAL", 0),
                    mv("THUNDER_WAVE", "ELECTRIC", 0)]}
party = [{"species": "PIDGEY", "hp": 0, "max_hp": 35, "types": ["NORMAL", "FLYING"], "level": 13},
         {"species": "PIKACHU", "hp": 33, "max_hp": 33, "types": ["ELECTRIC"], "level": 12,
          "moves": PIK_ME["moves"]},
         {"species": "BULBASAUR", "hp": 35, "max_hp": 35, "types": ["GRASS", "POISON"], "level": 12,
          "moves": [mv("TACKLE", "NORMAL", 35), mv("LEECH_SEED", "GRASS", 0)]}]
spec = {"switch": [{"to": "best_matchup", "no_effect": True, "vs": "trainer"}]}


def obs(me):
    return {"party": party, "battle": {"kind": "trainer", "me": me, "foe": ONIX}}


ck("PIKACHU on ONIX, every damaging move 0x: the rule brings BULBASAUR in",
   BP.should_switch(obs(PIK_ME), spec, {"turn": 6}) == 3)
qa = dict(PIK_ME, moves=PIK_ME["moves"] + [mv("QUICK_ATTACK", "NORMAL", 40)])
ck("a move that lands at all (Quick Attack, 0.5x) keeps it in",
   BP.should_switch(obs(qa), spec, {"turn": 6}) is None)
dry = dict(PIK_ME, moves=[mv("THUNDERSHOCK", "ELECTRIC", 40, pp=0), mv("GROWL", "NORMAL", 0)]
           + [mv("QUICK_ATTACK", "NORMAL", 40, pp=0)])
ck("moves with no PP left are not counted as able to land",
   BP.should_switch(obs(dry), spec, {"turn": 6}) == 3)
untyped = dict(PIK_ME, moves=[{"id": "THUNDERSHOCK", "power": 40, "pp": 20}])
ck("a move whose type is not read is not called useless",
   BP.should_switch(obs(untyped), spec, {"turn": 6}) is None)
ck("not gated to turn 1 unless first_turns says so",
   BP.should_switch(obs(PIK_ME), {"switch": [dict(spec["switch"][0], first_turns=1)]},
                    {"turn": 6}) is None)
ck("a rule without it is unchanged (turn 6, turn-1 gate)",
   BP.should_switch(obs(PIK_ME), {"switch": [{"to": "best_matchup", "vs": "trainer"}]},
                    {"turn": 6}) is None)
ck("the validator takes true/false and refuses anything else",
   not any("no_effect" in p for p in BP.validate_spec(spec))
   and any("no_effect" in p for p in BP.validate_spec(
       {"switch": [{"to": "best_matchup", "no_effect": "yes"}]})))
ck("the author is offered the word", "no_effect" in spec_age.dsl_words()
   and '"no_effect": true/false' in policy_author.DSL_DOC)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
