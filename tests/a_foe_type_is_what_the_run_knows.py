#!/usr/bin/env python3
"""A foe's types are what the run knows of them, never the game's memory.

Gen 1's battle screen shows a foe's name, level and HP bar (booklet p.34),
not its types (user, 2026-10-13: "yeah we have to make that change too to
be accurate"). Known: a species once owned (its summary screen), what the
game said when a move type hit it, and the model's own word, asked once.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import type_ledger as T                                         # noqa: E402
import battle_policy as bp                                      # noqa: E402
import executor as E                                            # noqa: E402

fails = []


def ck(name, cond, det=""):
    print(("ok   " if cond else "FAIL ") + name + ("" if cond else f"  {str(det)[:300]}"))
    if not cond:
        fails.append(name)


def battle(species, types):
    return {"mode": "battle", "party": [{"species": "PIKACHU", "types": ["ELECTRIC"]}],
            "battle": {"kind": "trainer", "me": {"species": "PIKACHU"},
                       "foe": {"species": species, "level": 14, "hp": 30, "maxhp": 30,
                               "types": types}}}


T.reset()
o = T.scrub(battle("ONIX", ["ROCK", "GROUND"]))
ck("a species never owned and never named has no types on the page",
   "types" not in o["battle"]["foe"] and o["battle"]["foe"]["eff_seen"] == {}, o["battle"]["foe"])
ck("the party's own types are read off its summary screens", T.OWNED == {"PIKACHU": ["ELECTRIC"]})
T.SAID["ONIX"] = ["ROCK", "GROUND"]
o = T.scrub(battle("ONIX", ["WATER"]))
ck("the model's word stands in, said as whose",
   o["battle"]["foe"]["types"] == ["ROCK", "GROUND"] and o["battle"]["foe"]["types_from"] == "said",
   o["battle"]["foe"])
T.OWNED["ONIX"] = ["ROCK", "GROUND"]
ck("an owned species reads as owned", T.believed("ONIX") == (["ROCK", "GROUND"], "owned"))

# what the game said when a move type hit it
T.reset()
ck("'doesn't affect' files 0", T.note_hit("ONIX", "ELECTRIC", "It doesn't affect enemy ONIX!", False) == 0.0)
ck("'super effective' files 2", T.note_hit("ONIX", "WATER", "It's super effective!", True) == 2.0)
ck("'not very effective' files 0.5", T.note_hit("ONIX", "NORMAL", "It's not very effective...", True) == 0.5)
ck("a plain hit files 1", T.note_hit("ONIX", "FIRE", "", True) == 1.0)
ck("a miss files nothing", T.note_hit("ONIX", "ICE", "PIKACHU's attack missed!", False) is None
   and "ONIX|ICE" not in T.SEEN)
foe = T.scrub(battle("ONIX", None))["battle"]["foe"]
ck("what was said rides on the foe", foe["eff_seen"] == {"ELECTRIC": 0.0, "WATER": 2.0, "NORMAL": 0.5, "FIRE": 1.0})
ck("...and the scorer reads it before any type",
   bp.foe_eff("ELECTRIC", foe) == 0.0 and bp.foe_eff("WATER", dict(foe, types=["NORMAL"])) == 2.0)
ck("...and a move type never said and no types is neutral", bp.foe_eff("GRASS", foe) == 1.0)
T.SAID["ONIX"] = ["WATER"]                                  # the model was wrong
foe = T.scrub(battle("ONIX", None))["battle"]["foe"]
T.SAID["ONIX"] = ["ROCK", "GROUND"]
foe = T.scrub(battle("ONIX", None))["battle"]["foe"]
ck("a message that agrees with the chart keeps the chart's number (4x is 'super' too)",
   bp.foe_eff("WATER", foe) == 4.0, bp.foe_eff("WATER", foe))
T.SAID["ONIX"] = ["WATER"]
foe = T.scrub(battle("ONIX", None))["battle"]["foe"]
ck("what was SEEN overrides the model's word for that move type",
   bp.foe_eff("ELECTRIC", foe) == 0.0 and bp.foe_eff("GRASS", foe) == 2.0)

# the boxes after OUR move, before the enemy's turn
after = {"battle_text": "PIKACHU used THUNDERSHOCK! / It doesn't affect enemy ONIX! / "
                        "Enemy ONIX used TACKLE! / It's super effective!",
         "battle_text_seq": 24}
ck("our move's words stop at the enemy's turn",
   E._our_move_words(after, "THUNDERSHOCK", 20) == "It doesn't affect enemy ONIX!")
ck("...and a move we did not use has none", E._our_move_words(after, "SURF", 20) is None)
ck("only the lines this op added are read, never an earlier turn's",
   E._our_move_words(after, "THUNDERSHOCK", 22) is None
   and E._our_move_words(after, "THUNDERSHOCK", None) is None)
psy = {"battle_text": "KADABRA used PSYCHIC! / It's not very effective...", "battle_text_seq": 9}
ck("PSYCHIC_M is read as the screen's PSYCHIC",
   E._our_move_words(psy, "PSYCHIC_M", 7) == "It's not very effective...")

# a STATUS move's failure says nothing of the foe's types
T.reset()
_st = {"index": 1, "id": "THUNDER_WAVE", "type": "ELECTRIC", "power": 0, "pp": 20}
_me = {"species": "PIKACHU", "level": 40, "hp": 90, "status": None, "moves": [_st]}
_fo = {"species": "GOLBAT", "level": 40, "hp": 100, "maxhp": 100, "types": ["POISON", "FLYING"]}
E._journal_damage({"me": _me, "foe": _fo, "_text_seq": 3},
                  {"mode": "battle", "battle_text": "PIKACHU used THUNDER WAVE! / It didn't affect enemy GOLBAT!",
                   "battle_text_seq": 5, "battle": {"me": _me, "foe": dict(_fo, hp=100)}}, "THUNDER_WAVE")
ck("a status move that 'didn't affect' files nothing", T.SEEN == {}, T.SEEN)

# the ledger is kept with the run's memory; the bridge lays it on every obs
src = (ROOT / "planner/executor.py").read_text()
ck("kept with explored.json",
   '"type_ledger": type_ledger.dump()' in src and 'type_ledger.load(data.get("type_ledger"))' in src)
ck("the bridge scrubs every observation",
   "return type_ledger.scrub(self._came_from_stamp(o))" in (ROOT / "planner/bridge.py").read_text())
ck("the game's species table is not read for types",
   'gin_save.GEN / "pokemon.lua"' not in src)
ck("a never-owned species is asked about once, with no model nothing is asked",
   "def _ask_types(self, species)" in src and "not self.model" in src[src.index("def _ask_types"):][:600])
# a trainer's NEXT Pokemon is asked about as it comes out (BROCK's ONIX,
# run 55): the battle loop calls the executor's asker on a species with no
# types, and an executor with a model sets it
loop = src[src.index("def _run_policy("):]
loop = loop[:loop.index("\ndef ", 10)]
ck("the battle loop asks about a foe it knows no types for",
   "TYPES_ASKER(_f0.get(\"species\"))" in loop and "obs = type_ledger.scrub(obs)" in loop)
ck("...set by an executor with a model, never without one",
   "TYPES_ASKER = self._ask_types if model else None" in src)
T.reset()

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all ok'}")
sys.exit(1 if fails else 0)
