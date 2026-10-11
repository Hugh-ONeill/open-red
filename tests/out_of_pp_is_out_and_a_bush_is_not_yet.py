#!/usr/bin/env python3
"""Out of PP is out; a part behind an uncuttable bush is not yet.

Run 51 (2026-10-11):
- BULBASAUR at 24/35 with TACKLE at 1 PP and LEECH_SEED at 0 read as a
  party in fair shape; the sweep walked it into Viridian Forest's Bug
  Catcher and it used GROWL twenty-one times until it fainted. The sweep's
  "nearly out" stop and the grind's spent stop counted HP only.
- "A new part of ROUTE_2" had both walked parts ruled out and the rest of
  the road behind CUT trees, nobody able to cut; ground seen past the bush
  kept the step open (user: "the goal is possible but not currently
  possible because it lacks the ability to access those other areas
  without cut").
- The 1x copy put its CONTINUING card back mid-game on a press (user: "it
  happens when it talks to a trainer its already beaten").

Pinned: the grind stop counts a member with no damaging PP as unable; the
sweep stop reads wd.party_armed; the new-part answer names the bushes when
nobody can cut and stays open when someone can or holds HM_CUT; the copy's
boot card is once per replay. Synthetic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def mv(i, mid, power, pp):
    return {"id": mid, "power": power, "pp": pp, "index": i}


E.ACTIVE_SPEC = {"flee_wild": {"hp_below": 0.2}}
ex = E.Executor.__new__(E.Executor)
DRY = {"party": [{"species": "BULBASAUR", "hp": 24, "max_hp": 35,
                  "moves": [mv(1, "TACKLE", 35, 0), mv(2, "GROWL", 0, 40),
                            mv(3, "LEECH_SEED", 0, 0)]}]}
why = ex._grind_spent({"id": "g", "done_when": {"party_min_level": 12}}, DRY)
ck("a member with HP and no damaging PP is spent", "no damaging move left" in why, why)
WET = json.loads(json.dumps(DRY))
WET["party"][0]["moves"][0]["pp"] = 5
ck("...and with PP left it is not", ex._grind_spent({"id": "g", "done_when": {}}, WET) == "")

SG = {"id": "exit_viridian_forest",
      "done_when": {"map": "ROUTE_2", "not_area": ["ROUTE_2|3,43", "ROUTE_2|8,0"]}}
OBS = {"mode": "overworld", "player": {"x": 8, "y": 3}, "bag": {},
       "party": [{"species": "BULBASAUR", "moves": [mv(1, "TACKLE", 35, 30)]}],
       "map": {"id": "ROUTE_2", "region": "8,0", "seen": {"n": 300}, "frontier": [],
               "seen_unreached": {"n": 40, "beside_n": 2},
               "objects": [{"kind": "cut_tree", "name": "CUT_TREE", "x": 5, "y": 10,
                            "reachable": True, "opens": True}]}}
ex2 = E.Executor.__new__(E.Executor)
ex2._where = lambda o: f"{o['map']['id']}|{o['map']['region']}"
r = ex2._new_part_ruled_out(SG, OBS)
ck("past an uncuttable bush the step is answered, not yet", r and "(5,10)" in r
   and "nobody in the party can cut yet" in r, r)
CUTS = json.loads(json.dumps(OBS))
CUTS["party"][0]["moves"].append(mv(2, "CUT", 50, 30))
ck("a party that knows CUT keeps it open", ex2._new_part_ruled_out(SG, CUTS) is None)
HM = json.loads(json.dumps(OBS))
HM["bag"] = {"HM_CUT": 1}
ck("HM_CUT in the bag keeps it open", ex2._new_part_ruled_out(SG, HM) is None)
NOBUSH = json.loads(json.dumps(OBS))
NOBUSH["map"]["objects"] = []
ck("unreached ground with no bush keeps it open", ex2._new_part_ruled_out(SG, NOBUSH) is None)

shim = (ROOT / "harness/shim.lua").read_text()
ck("the sweep stop reads party_armed", "wd.party_armed(G) == 0" in shim
   and "wd.party_armed = function(G)" in shim)
shadow = (ROOT / "tools/shadow/shadow.lua").read_text()
ck("the copy's boot card is once per replay",
   "booting = not loaded and not ever_loaded" in shadow
   and "if loaded then ever_loaded = true end" in shadow)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
