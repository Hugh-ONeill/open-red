#!/usr/bin/env python3
"""A bush the party could not cut is written down as a way that turned it back.

Run 58 (2026-10-17): Cerulean's south, walk_to(19,28) "you stand beside it
now at (19,27)", then field_move CUT "no party Pokemon knows CUT and NO
TM/HM for it is in the bag". The turned-back list named a Cool Trainer and
two Viridian rows, not the bush (user: "build and stage that"). Evidence
only: the bush, where, and the game's refusal; nothing about what lifts it.

Synthetic.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(name, ok, d=""): checks.append((name, bool(ok), d))

def fresh():
    x = object.__new__(E.Executor)
    x.blockers = {}
    x._cur_target = "map:ROUTE_5"
    x._save_memory = lambda *a, **k: None
    x.log = lambda *a, **k: None
    x._where = lambda o: "CERULEAN_CITY|20,0"
    return x

PRE = {"map": {"id": "CERULEAN_CITY", "objects": [
           {"name": "CUT_TREE", "kind": "cut_tree", "x": 19, "y": 28},
           {"name": "CERULEANCITY_COOLTRAINER_M", "x": 31, "y": 20}]},
       "player": {"x": 19, "y": 27}}
NOTE = ("field_move(move=CUT): FAILED — no party Pokemon knows CUT and NO TM/HM for it "
        "is in the bag — someone in the world has to hand that machine over before CUT "
        "can ever be used")
x = fresh()
x._record_outcome(PRE, "field_move", {"op": "field_move", "move": "CUT"}, NOTE)
b = x.blockers.get("CERULEAN_CITY|20,0|19,28") or {}
ck("the bush beside the player is recorded where it stands", b.get("key") == "19,28", x.blockers)
ck("...with the bush and the game's own refusal",
   "CUT_TREE (a bush CUT clears) at (19,28)" in str(b.get("what"))
   and "no party Pokemon knows CUT and NO TM/HM for it is in the bag" in str(b.get("what")), b)
ck("...and nothing about what lifts it", b.get("lifts") is None, b)
x = fresh()
x._record_outcome(PRE, "field_move", {"op": "field_move", "move": "CUT", "x": 5, "y": 8}, NOTE)
ck("an aimed CUT records the bush it was aimed at", "CERULEAN_CITY|20,0|5,8" in x.blockers, x.blockers)
x = fresh()
x._record_outcome(PRE, "field_move", {"op": "field_move", "move": "CUT"},
                  "field_move(move=CUT): ok — the bush was cut")
ck("a CUT that worked records nothing", not x.blockers, x.blockers)
far = {"map": PRE["map"], "player": {"x": 10, "y": 10}}
x = fresh()
x._record_outcome(far, "field_move", {"op": "field_move", "move": "CUT"}, NOTE)
ck("no bush beside the player: nothing to name", not x.blockers, x.blockers)
x = fresh()
x._record_outcome(PRE, "field_move", {"op": "field_move", "move": "SURF"},
                  "field_move(move=SURF): FAILED — no party Pokemon knows SURF and NO TM/HM")
ck("another move is not this rule", not x.blockers, x.blockers)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
