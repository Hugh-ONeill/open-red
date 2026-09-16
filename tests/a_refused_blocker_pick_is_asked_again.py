#!/usr/bin/env python3
"""A blocker pick the harness turns down is asked again, not dropped.

Run 27 was walled out of Cerulean's south half by the guard standing on the
trashed house's only door; "Reach Vermilion City" named the HM01 on the S.S.
Anne as its blocker, the pick was refused as circular (the ship docks in
Vermilion), and the rung returned nothing — so "Retrieve the S.S. Ticket
from Bill", two legs up and the deed that moves that guard, was never on
the table (user, 2026-09-16: "the point of doing an authored run now is to
work out the push-up/down and rewrites for nonesense and all that, but lets
try 2").

Pinned: a refused pick leaves the list and is said on the next ask; the
model may name another; two re-asks at most; "none" still ends it; and the
question shows the doorways the run found a person standing in.

Synthetic: the model is stubbed, no game.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import author as A            # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


tmp = Path(tempfile.mkdtemp(prefix="blocker_reask_"))
observed = tmp / "explored.json"
observed.write_text(json.dumps({"shut_doors": {
    "CERULEAN_CITY|20,0": ["27,11 (CERULEANCITY_GUARD2 is standing there)",
                           "4,11 (the way onto it is blocked; nobody is "
                           "standing there)"],
    "CERULEAN_CITY|23,0": ["27,11 (CERULEANCITY_GUARD2 is standing there)"]}}))
AHEAD = [(13, "Retrieve the S.S. Ticket from Bill"),
         (14, "Reach Vermilion City"),
         (15, "Retrieve the HM01 from the S.S. Anne")]
bodies, script = [], []


def chat(msgs, model):
    bodies.append(msgs[-1]["content"])
    return script.pop(0)


A.brock_probe.chat = chat
A.check_already_done = lambda *a, **k: False
A.confirm_blocker = lambda *a, **k: True
A.attempt_yield_text = lambda goal: ("",)
A._wording_lineage = lambda goal: ""
A.pull_into_unreached = (lambda text, plan, observed:
                         "SS_ANNE_1F" if "S.S. Anne" in text else None)
A.pull_into_held = lambda text, observed: None

script[:] = ['{"why": "Cut clears the bush", "pull_forward": 15}',
             '{"why": "Bill hands over the ticket", "pull_forward": 13}']
n = A.check_blocker("Defeat Lt. Surge for the Thunder Badge", AHEAD,
                    "in CERULEAN_CITY", "", "m", leg=12, observed=observed,
                    refused=set(), plan=tmp / "plan.json")
ck("a refused pick is followed by a second ask, and its answer stands",
   n == 13 and len(bodies) == 2)
ck("the first ask lists every leg ahead",
   "15. Retrieve the HM01" in bodies[0] or "HM01" in bodies[0])
ck("the second ask no longer lists the refused leg",
   "HM01 from the S.S. Anne" not in bodies[1].split("ANSWERS ALREADY")[0]
   .split("THE LEGS STILL AHEAD:")[1])
ck("...and says why it was turned down",
   "ANSWERS ALREADY TURNED DOWN FOR THIS LEG" in bodies[1]
   and "leg 15: leg 15 happens in SS_ANNE_1F" in bodies[1])
ck("the question shows who is standing in which doorway",
   "DOORWAYS YOU HAVE FOUND SOMEONE STANDING IN" in bodies[0]
   and "CERULEAN_CITY door 27,11 (CERULEANCITY_GUARD2 is standing there)"
   in bodies[0])
ck("...once per door, and not the doorways nobody stands in",
   bodies[0].count("27,11 (CERULEANCITY_GUARD2") == 1
   and "4,11 (the way" not in bodies[0])

bodies.clear()
script[:] = ['{"why": "a", "pull_forward": 15}',
             '{"why": "b", "pull_forward": 15}',
             '{"why": "c", "pull_forward": 15}']
n = A.check_blocker("Reach Vermilion City", AHEAD, "s", "", "m", leg=12,
                    observed=observed, refused=set(), plan=tmp / "plan.json")
ck("two re-asks at most", n is None and len(bodies) == 3)

bodies.clear()
script[:] = ['{"why": "a", "pull_forward": 15}',
             '{"why": "nothing ahead unblocks it", "pull_forward": null}']
n = A.check_blocker("Reach Vermilion City", AHEAD, "s", "", "m", leg=12,
                    observed=observed, refused=set(), plan=tmp / "plan.json")
ck("'none' after a refusal ends it", n is None and len(bodies) == 2)

bodies.clear()
script[:] = ['{"why": "x", "pull_forward": null}']
n = A.check_blocker("Reach Vermilion City", AHEAD, "s", "", "m", leg=12,
                    observed=observed, refused=set(), plan=tmp / "plan.json")
ck("a first 'none' is one question, as before", n is None and len(bodies) == 1)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
