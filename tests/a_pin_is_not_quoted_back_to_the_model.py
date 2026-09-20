#!/usr/bin/env python3
"""A condition printed for the model carries no DVs and no trainer id.

A slot_level check is pinned at plan start to the Pokemon standing in that
slot, by DVs and trainer id, so the check follows it through a reorder or
an evolution. Those live in the save and on no screen — and the pin sits
inside done_when, which is quoted back in the status line, in the
escalation prompt, in the plan echo, in the draft skeletons and in the
carried-gate notes. So it leaked everywhere a condition was printed (user,
2026-09-20: "were still leaking the DVs in the donewhen/carried text"),
even after the party's own DVs were taken out of the observation.

Pinned: the helper strips the pin's hidden numbers and keeps everything
else, at any depth; an empty pin leaves no empty object behind; the sites
that PRINT a condition use it; the sites that COMPARE two conditions do
not, because two checks pinned to different Pokemon must not read as one.
Synthetic."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import pred_text as P  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


WHO = {"species": "PARAS", "dvs": {"hp": 3, "attack": 8}, "otId": 45799}
PINNED = {"slot_level": {"slot": 4, "min": 30, "who": dict(WHO)}}

ck("the pin's DVs and trainer id are gone",
   P.dumps(PINNED)
   == '{"slot_level": {"slot": 4, "min": 30, "who": {"species": "PARAS"}}}',
   P.dumps(PINNED))
ck("...and the rest of the condition is untouched",
   P.for_model(PINNED)["slot_level"]["min"] == 30
   and P.for_model(PINNED)["slot_level"]["slot"] == 4)
ck("a pin with nothing left is dropped entirely",
   P.dumps({"slot_level": {"slot": 1, "min": 5,
                           "who": {"dvs": {"hp": 1}, "otId": 2}}})
   == '{"slot_level": {"slot": 1, "min": 5}}')
ck("a condition nested in any_of is cleaned too",
   "dvs" not in P.dumps({"any_of": [PINNED, {"map": "ROUTE_6"}]})
   and "ROUTE_6" in P.dumps({"any_of": [PINNED, {"map": "ROUTE_6"}]}))
ck("...and in all_of", "otId" not in P.dumps({"all_of": [PINNED]}))
ck("an ordinary condition is passed through as it is",
   P.dumps({"map": "VERMILION_CITY"}) == '{"map": "VERMILION_CITY"}'
   and P.dumps({"has_item": {"HM_CUT": 1}}) == '{"has_item": {"HM_CUT": 1}}')
ck("nothing is mutated on the way",
   (lambda d: (P.dumps(d), d == PINNED)[1])({"slot_level": dict(
       PINNED["slot_level"], who=dict(WHO))}))
ck("None and empty are fine", P.dumps(None) == "{}" and P.dumps({}) == "{}")
ck("the keys it hides are named once", P.HIDDEN == ("dvs", "otId"))

ex = (ROOT / "planner/executor.py").read_text()
au = (ROOT / "planner/author.py").read_text()
cg = (ROOT / "planner/carry_gates.py").read_text()
ck("the status line prints it cleaned",
   'f"DONE_WHEN{pred_text.dumps(' in ex)
ck("the escalation prompt prints it cleaned",
   'DONE_WHEN: {pred_text.dumps(done)}' in ex)
ck("...and so do the condition-is-the-step lines",
   ex.count("THE CONDITION IS THE STEP: {pred_text.dumps(done)}") == 2)
ck("the author's plan listing and draft skeletons print it cleaned",
   "f\"{s.get('id')} {pred_text.dumps(s.get('done_when'))}\"" in au
   and "out.append(f\"{sg.get('id')}: {pred_text.dumps(sg.get('done_when'))}" in au)
ck("the carried-gate note prints it cleaned",
   "pred_text.dumps(_died_on.get('done_when') or {})" in cg)

# ...and the comparisons keep the whole thing
ck("carry_gates matches gates on the WHOLE condition",
   cg.count('json.dumps(sg.get("done_when") or {}, sort_keys=True)') >= 3)
ck("...and the plan digest does too",
   "f\"{s.get('id')}{json.dumps(s.get('done_when'), sort_keys=True)}\"" in au)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
