#!/usr/bin/env python3
"""An objective the ladder rewords keeps one search record, the drafts see
what was NOT done where it looked, and a room sweep keeps what every press
said.

Run 36 hunted HM04 under three wordings ("Retrieve the HM04 from the
Safari Zone", "Obtain HM04 from the Safari Zone", "Obtain HM04 from the
Warden in the Safari Zone"), each draft seeing only its own record; the
record said Fuchsia was stood on 17x and not that three of its doors had
never been gone through, the Warden's among them; and the sign that says
whose house that is had been pressed by a sweep whose words were lost,
because only the sweep's last press reached the hints (2026-10-05, user:
"once its totally explored it should look uninteresting").

Pinned: rewordings naming the same bag item are one objective, different
items or none are not; the executor merges every filed record of the
objective when it comes back; looked_text adds them up, lists the things
seen and never pressed and the doors never gone through, by coordinate
only; a door tried, landed on, or paired with one taken is not listed;
each sweep press files its words. Synthetic."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import executor as E  # noqa: E402
from objective_key import objective_items, same_objective  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ck("a machine is named however it is spelled",
   objective_items("Obtain HM 4 from the Warden") == {"HM04"}
   and objective_items("Retrieve the HM04 from the Safari Zone") == {"HM04"})
ck("a machine is named by its bag id too",
   objective_items("Obtain HM_STRENGTH") == {"HM04"}
   and objective_items("Get the HM Strength from the Warden") == {"HM04"}
   and objective_items("Buy TM_REST") == objective_items("buy TM44"))
ck("a key item is named however it is cased",
   objective_items("Retrieve the Secret Key") == {"SECRET_KEY"}
   and objective_items("Get the S.S. Ticket") == {"S_S_TICKET"})
ck("rewordings of one item are one objective",
   same_objective("Obtain HM04 from the Safari Zone",
                  "Obtain HM04 from the Warden in the Safari Zone"))
ck("different items are not",
   not same_objective("Retrieve the Gold Teeth", "Obtain HM04"))
ck("a goal naming no item matches only its own words",
   same_objective("Reach Saffron City", "reach  saffron city")
   and not same_objective("Reach Saffron City", "Reach Celadon City"))
ck("a move is not an item",
   objective_items("a party Pokemon knows STRENGTH") == frozenset())

d = {
    "leg_goal": "Reach the Indigo Plateau",
    "leg_looked": {"VIRIDIAN_CITY": 5}, "leg_tries": 2,
    "legs_past": {
        "Retrieve the HM04 from the Safari Zone":
            {"looked": {"SAFARI_ZONE_CENTER": 30, "FUCHSIA_CITY": 10},
             "tries": 3},
        "Obtain HM04 from the Safari Zone":
            {"looked": {"SAFARI_ZONE_CENTER": 19, "FUCHSIA_CITY": 7},
             "tries": 4},
        "Retrieve the Gold Teeth for the Warden":
            {"looked": {"SAFARI_ZONE_WEST": 99}, "tries": 9},
    },
    "sightings": {"FUCHSIA_CITY|2,2": ["SIGN_FUCHSIA_CITY_27_29",
                                       "FUCHSIACITY_GAMBLER", "CUT_TREE"],
                  "FUCHSIA_POKECENTER|3,7": ["PC", "FUCHSIAPOKECENTER_NURSE"]},
    "touched": {"FUCHSIA_CITY|2,2": ["SIGN_FUCHSIA_CITY_27_29"]},
    "map_doors": {"FUCHSIA_CITY": ["18,3", "27,27", "31,24", "31,27", "5,27",
                                   "11,27"],
                  "SAFARI_ZONE_GATE": ["3,0", "4,0"]},
    "explored": {"FUCHSIA_CITY|2,2": {
                     "18,3": {"to": "SAFARI_ZONE_GATE|3,5", "land": "3,5"}},
                 "SAFARI_ZONE_GATE|3,5": {"3,0": {"n": 1}},
                 "FUCHSIA_GYM|4,17": {"4,17": {"to": "FUCHSIA_CITY|2,2",
                                                "land": "5,27"}}},
    "shut_doors": {"FUCHSIA_CITY|2,2": ["31,24 (the way onto it is blocked)"]},
    "door_dests": {"FUCHSIA_CITY": {"27,27": "WARDENS_HOUSE"}},
}
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "explored.json"
    p.write_text(json.dumps(d))
    w = A.looked_text(p, "Obtain HM04 from the Warden in the Safari Zone")
ck("every wording's record is added up", "across 7 attempt(s)" in w
   and "SAFARI_ZONE_CENTER: stood on 49x" in w
   and "FUCHSIA_CITY: stood on 17x" in w, w)
ck("another item's record stays out", "SAFARI_ZONE_WEST" not in w, w)
ck("the leg underway is not mixed in", "VIRIDIAN_CITY" not in w, w)
ck("a thing seen and never pressed is listed",
   "NEVER pressed there: FUCHSIACITY_GAMBLER" in w, w)
ck("a sweep's press counts as pressed",
   "SIGN_FUCHSIA_CITY_27_29 1x" in w and "CUT_TREE" not in w, w)
ck("a door never gone through is listed by where it stands",
   "doors there NEVER gone through: 11,27, 27,27, 31,27" in w, w)
ck("never by where it leads", "WARDENS_HOUSE" not in w, w)

ex = E.Executor.__new__(E.Executor)
ex.hints = {}
ex._save_memory = lambda: None
ex._file_sweep_heard("FUCHSIA_CITY|2,2", "SIGN_FUCHSIA_CITY_27_29",
                     "SAFARI ZONE WARDEN's Home", {"flags": [1]})
ex._file_sweep_heard("FUCHSIA_CITY|2,2", "SIGN_FUCHSIA_CITY_13_7",
                     "SAFARI ZONE WARDEN's Home", {})
ex._file_sweep_heard("FUCHSIA_CITY|2,2", "SIGN_FUCHSIA_CITY_5_29",
                     "FUCHSIA CITY POKéMON GYM / LEADER: KOGA", {})
ex._file_sweep_heard("None|None", "X", "a long line said nowhere at all", {})
h = ex.hints.get("FUCHSIA_CITY|2,2") or []
ck("each press's words are filed under what was pressed",
   "SIGN_FUCHSIA_CITY_27_29: SAFARI ZONE WARDEN's Home" in h
   and any(l.startswith("SIGN_FUCHSIA_CITY_5_29: ") for l in h), h)
ck("the same words once, and a printed name not doubled",
   len(h) == 3 and "LEADER: KOGA" in h, h)
ck("and dated like the recorder's",
   "SIGN_FUCHSIA_CITY_27_29: SAFARI ZONE WARDEN's Home"
   in ex.hints_at["FUCHSIA_CITY|2,2"])
ck("no room, no line", "None|None" not in ex.hints)

src = (ROOT / "planner/executor.py").read_text()
ck("the sweep files every press",
   "self._file_sweep_heard(\n                                said_region(cur, o2), name,"
   in src)
ck("a returning objective takes back every wording's record",
   "if g == _goal_now or same_objective(g, _goal_now)]" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok  " if ok else "FAIL") + " " + n + ("" if ok else f"\n     {dd}"))
sys.exit(1 if failed else 0)
