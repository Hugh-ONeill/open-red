#!/usr/bin/env python3
"""A wipe reopens only the place steps that lie on the way back.

Run 71, 2026-11-02, leg 9 (the HM for Cut): the party wiped on the S.S.
Anne and woke at the Cerulean Center. No earlier step held there, so every
place step reopened and the plan regressed to step 0, exit_bills_house
{map: ROUTE_25}; go walked Cerulean to Route 25 and back before going south.

Pinned: a place step whose map is off the walked way from the wake point to
the last reopened place step is not reopened, so the regress starts at the
first one on the way; the league (run 27, 2026-09-18), whose rooms lie on
the way to the room lost in, still regresses to its first room; with no
walked way known, nothing is filtered. Synthetic.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))


def rig(explored, plan, idx, prev):
    ex = E.Executor.__new__(E.Executor)
    ex.explored = explored
    ex.visits = {r: 1 for r in explored}
    ex._bad_seam = set()
    ex.pad_lands = {}
    ex.plan = plan
    ex._cur_sg_idx = idx
    ex._faint_at = None
    ex._cur_target = ""
    ex._wipe_watch = prev
    ex.log = lambda *a, **k: None
    ex._where = lambda o: f"{o['map']['id']}|{o['map']['region']}"
    return ex


def woke(mid, region, money):
    return {"mode": "overworld", "money": money, "player": {"x": 3, "y": 4},
            "map": {"id": mid, "region": region},
            "party": [{"species": "IVYSAUR", "hp": 60, "max_hp": 60}]}


CERULEAN = {
    "CERULEAN_POKECENTER|0,3": {"3,7": {"n": 3, "to": "CERULEAN_CITY|20,0"}},
    "CERULEAN_CITY|20,0": {"19,17": {"n": 3, "to": "CERULEAN_POKECENTER|0,3"},
                           "north": {"n": 2, "to": "ROUTE_24|4,4"},
                           "south": {"n": 1, "to": "ROUTE_5|4,4"}},
    "ROUTE_24|4,4": {"east": {"n": 1, "to": "ROUTE_25|1,6"}, "south": {"n": 2, "to": "CERULEAN_CITY|20,0"}},
    "ROUTE_25|1,6": {"west": {"n": 1, "to": "ROUTE_24|4,4"}},
    "ROUTE_5|4,4": {"south": {"n": 1, "to": "VERMILION_CITY|18,0"}},
    "VERMILION_CITY|18,0": {"18,31": {"n": 1, "to": "SS_ANNE_1F|26,0"}},
    "SS_ANNE_1F|26,0": {"7,0": {"n": 1, "to": "SS_ANNE_2F|7,1"}},
    "SS_ANNE_2F|7,1": {},
}
PLAN = {"goal": "HM for Cut", "subgoals": [
    {"id": "exit_bills_house", "done_when": {"map": "ROUTE_25"}},
    {"id": "travel_to_vermilion", "done_when": {"map": "VERMILION_CITY"}},
    {"id": "enter_ss_anne", "done_when": {"map": "SS_ANNE_1F"}},
    {"id": "find_captain", "done_when": {"map": "SS_ANNE_CAPTAINS_ROOM"}}]}

ex = rig(CERULEAN, PLAN, 3, (1000, "SS_ANNE_2F", "SS_ANNE_2F|7,1"))
note = ex._watch_for_a_wipe(woke("CERULEAN_POKECENTER", "0,3", 500))
ck("the wipe is seen", note and "YOUR PARTY FAINTED" in note, note)
ck("the regress starts at the first place on the way back, not Route 25",
   getattr(ex, "_plan_regress", None) == 1, getattr(ex, "_plan_regress", None))
ck("...and the off-route step is not named undone",
   "exit_bills_house" not in (note or ""), note)

LEAGUE = {
    "INDIGO_PLATEAU_LOBBY|0,1": {"8,0": {"n": 2, "to": "LORELEIS_ROOM|4,0"}},
    "LORELEIS_ROOM|4,0": {"4,0": {"n": 2, "to": "BRUNOS_ROOM|4,0"}},
    "BRUNOS_ROOM|4,0": {"4,0": {"n": 2, "to": "AGATHAS_ROOM|4,0"}},
    "AGATHAS_ROOM|4,0": {},
}
LPLAN = {"goal": "Elite Four", "subgoals": [
    {"id": "enter_elite_four", "done_when": {"map": "LORELEIS_ROOM"}},
    {"id": "defeat_lorelei", "done_when": {"map": "BRUNOS_ROOM"}},
    {"id": "defeat_bruno", "done_when": {"map": "AGATHAS_ROOM"}},
    {"id": "defeat_agatha", "done_when": {"map": "LANCES_ROOM"}}]}
ex2 = rig(LEAGUE, LPLAN, 3, (8000, "AGATHAS_ROOM", "AGATHAS_ROOM|4,0"))
ex2._watch_for_a_wipe(woke("INDIGO_PLATEAU_LOBBY", "0,1", 4000))
ck("the league's rooms lie on the way back, so it regresses to the first",
   getattr(ex2, "_plan_regress", None) == 0, getattr(ex2, "_plan_regress", None))

ex3 = rig({}, PLAN, 3, (1000, "SS_ANNE_2F", "SS_ANNE_2F|7,1"))
ex3._watch_for_a_wipe(woke("CERULEAN_POKECENTER", "0,3", 500))
ck("with no walked way known nothing is filtered",
   getattr(ex3, "_plan_regress", None) == 0, getattr(ex3, "_plan_regress", None))

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
