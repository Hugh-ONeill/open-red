#!/usr/bin/env python3
"""Somebody who has left the map is not offered as a way back or a word.

Route 12's Snorlax was fought on the Poke Flute and left; the sightings
ledger booked it gone at ROUTE_12|0,61 and ROUTE_12|10,21. Its "A sleeping
POKéMON blocks the way!" still headed WAYS THAT HAVE ALREADY TURNED YOU BACK
("turned you back 3x ... it may answer differently now"), and ROOMS WHERE
SOMEBODY IS WORTH ANOTHER WORD offered it on ROUTE_13|50,0, where a press had
been filed under its name. The model walked back to wake it and pressed a
name that was not there four times (run 54, 2026-10-13).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
from executor import Executor                                  # noqa: E402

fails = []


def ck(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


class _E(Executor):
    TOUCH_REOFFERS = 3

    def __init__(self):
        self._gone = {"ROUTE_12|0,61": {"ROUTE12_SNORLAX"},
                      "ROUTE_12|10,21": {"ROUTE12_SNORLAX"}}
        self.sightings = {"ROUTE_13|50,0": ["ROUTE13_BIKER"],
                          "ROUTE_12|0,61": ["ROUTE12_FISHER1"]}
        self.touched = {}
        self._tried_objs = {}
        self.logged = []
        old = [3, "a", "b"]
        self._touch_mark = {
            "ROUTE_13|50,0": {
                "ROUTE12_SNORLAX": {"then": old, "n": 0, "at": None},
                "ROUTE13_BIKER": {"then": old, "n": 0, "at": None}},
            "ROUTE_12|0,61": {
                "ROUTE12_SNORLAX": {"then": old, "n": 0, "at": None},
                "ROUTE12_FISHER1": {"then": old, "n": 0, "at": None}}}
        self.blockers = {
            "ROUTE_12|0,61|ROUTE12_SNORLAX": {
                "where": "ROUTE_12|0,61", "key": "ROUTE12_SNORLAX",
                "kind": "said", "n": 3, "cleared": False,
                "what": 'ROUTE12_SNORLAX said: "A sleeping POKéMON blocks the way!"'},
            "ROUTE_7_GATE|0,3|5,3": {
                "where": "ROUTE_7_GATE|0,3", "key": "5,3", "kind": "door",
                "n": 2, "cleared": False,
                "what": '"I\'m on guard duty. Gee, I\'m thirsty, though!"'}}

    def log(self, kind, **kw):
        self.logged.append((kind, kw))

    @staticmethod
    def _world_mark(obs):
        return [5, "c", "d"]


OBS = {"map": {"name": "FUCHSIA_CITY", "objects": []}}
e = _E()
e._sweep_blockers(OBS)
b = e.blockers["ROUTE_12|0,61|ROUTE12_SNORLAX"]
ck("a said-blocker whose speaker is gone there is cleared, from any map",
   b.get("cleared") is True)
ck("...and says why", b.get("cleared_how") == "who said it is no longer on this map")
ck("a guard's door is left alone", not e.blockers["ROUTE_7_GATE|0,3|5,3"].get("cleared"))
ck("the clearing is logged",
   any(k == "blocker_cleared" and kw.get("how") == "speaker gone" for k, kw in e.logged))

ck("the room it left does not offer it again",
   e._worth_another_word("ROUTE_12|0,61", OBS, backfill=False) == ["ROUTE12_FISHER1"])
ck("a room it was never seen in does not offer it either",
   e._worth_another_word("ROUTE_13|50,0", OBS, backfill=False) == ["ROUTE13_BIKER"])
e.sightings["ROUTE_13|50,0"].append("ROUTE12_SNORLAX")
ck("...unless it was seen standing there",
   "ROUTE12_SNORLAX" in e._worth_another_word("ROUTE_13|50,0", OBS, backfill=False))
ck("the backfill branch filters the same way",
   "ROUTE12_SNORLAX" not in e._worth_another_word("ROUTE_12|0,61", OBS))

print(f"\n{'FAILED: ' + ', '.join(fails) if fails else 'all ok'}")
sys.exit(1 if fails else 0)
