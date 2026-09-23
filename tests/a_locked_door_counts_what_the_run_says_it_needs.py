#!/usr/bin/env python3
"""A locked door counts what the run's plans say they need, so the author
reads it beside the door.

Run 27, 2026-09-18: the executor model wrote "I need the Secret Key to
enter the Cinnabar Gym" round after round, but the tally that ties a need
to a blocker had cues only for ghosts, bushes, water, Snorlax and
boulders, so the gym door's blocker read "nothing named yet as what lifts
it" on the author's page, and the author wrote a switch that restores the
gym's power (user: "is the author aware of the blockers ... the author
keeps writing goals that dont make sense in light of that fact given we
are keyless").

Pinned: a locked-door blocker takes the run's need for an item it does not
hold; a held item and an unrelated blocker are not counted. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def fake():
    ex = object.__new__(E.Executor)
    ex.blockers = {
        "CINNABAR_ISLAND|10,0|18,3": {"what": "\"The door is locked...\"", "cleared": False},
        "ROUTE_12|0,61|snorlax": {"what": "ROUTE12_SNORLAX: A sleeping POKéMON blocks the way!", "cleared": False},
    }
    return ex


ex = fake()
got = ex._tally_named_needs("The Cinnabar Gym door is locked. I need the Secret Key, which is located inside the Pokemon Mansion.",
                            {"bag": {"POTION": 2}})
ck("a locked door takes the run's need for an item it lacks",
   ("CINNABAR_ISLAND|10,0|18,3", "SECRET_KEY") in got
   and ex.blockers["CINNABAR_ISLAND|10,0|18,3"].get("named") == {"SECRET_KEY": 1}, (got, ex.blockers))
ck("...and not the unrelated blocker", not ex.blockers["ROUTE_12|0,61|snorlax"].get("named"))
ex = fake()
ck("an item already held is not a need",
   ex._tally_named_needs("I need the Secret Key to enter the gym.", {"bag": {"SECRET_KEY": 1}}) == [])
ex = fake()
ck("a sentence with no need word counts nothing",
   ex._tally_named_needs("The gym has a Secret Key lock on its door.", {"bag": {}}) == [])

# ---- a guard's gate takes the need said of it; a locked door elsewhere
# does not take every sentence with "enter" or "open" in it (run 34,
# 2026-09-23: "I need FRESH WATER to pass the Route 6 gate" was counted
# against the VIRIDIAN GYM's locked door four times, and the page told the
# model its own plans had named the drink as what the gym needs — a thing
# it never said — while both thirsty guards read "nothing named yet").
def gates():
    ex = object.__new__(E.Executor)
    ex.blockers = {
        "ROUTE_6_GATE|3,0|3,0": {"what": "\"I'm on guard duty. Gee, I'm thirsty, though!\"", "cleared": False},
        "ROUTE_5_GATE|2,0|3,5": {"what": "\"I'm on guard duty. Gee, I'm thirsty, though!\"", "cleared": False},
        "VIRIDIAN_CITY|17,0|32,7": {"what": "\"The GYM's doors are locked...\"", "cleared": False},
    }
    return ex


ex = gates()
got = ex._tally_named_needs(
    "I need FRESH WATER to pass the Route 6 gate. I will enter the Pokemon "
    "Center and open the menu to check my bag.", {"bag": {"POTION": 1}})
ck("a guard's gate takes the need said of it",
   ("ROUTE_6_GATE|3,0|3,0", "FRESH_WATER") in got, got)
ck("...and a locked door somewhere else does not, for an 'enter' or an 'open'",
   not ex.blockers["VIRIDIAN_CITY|17,0|32,7"].get("named"), ex.blockers)
ex = gates()
got = ex._tally_named_needs(
    "I need FRESH WATER to pass the guards on Route 5 and 6.", {"bag": {}})
ck("'the guards' lands on every guard's gate",
   ("ROUTE_6_GATE|3,0|3,0", "FRESH_WATER") in got
   and ("ROUTE_5_GATE|2,0|3,5", "FRESH_WATER") in got, got)
ex = gates()
got = ex._tally_named_needs(
    "I need the Secret Key to open the Viridian Gym door.", {"bag": {}})
ck("a locked door still takes a need said of a door, a lock or a gym",
   ("VIRIDIAN_CITY|17,0|32,7", "SECRET_KEY") in got
   and not ex.blockers["ROUTE_6_GATE|3,0|3,0"].get("named"), got)
CUES = dict(E.Executor.BLOCK_CUES)
ck("the words every plan uses are no longer cues for a locked door",
   not ({"enter", "open"} & set(CUES["LOCKED"])))
ck("a guard has cues of his own", {"guard", "gate", "thirsty"} <= set(CUES["GUARD"]))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
