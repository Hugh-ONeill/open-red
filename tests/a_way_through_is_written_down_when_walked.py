#!/usr/bin/env python3
"""A sweep that walks into a place records the mouth it came in by — which
is what a "go THROUGH here" objective is judged on.

Run 32's chain stopped dead at leg 11, "Traverse Mt. Moon", with the cave
behind it: in from Route 4's western pocket, across 1F, B1F and B2F, out at
ROUTE_4|36,2 to the east, then Cerulean, Bill, the S.S. Ticket, Vermilion.
The deed was done. But the way IN was walked by an `explore` sweep, and no
edge was written for it — the op that carries a run into a cave is often
the one that satisfies the step — so the walked graph held only the mouth
it came OUT of. A traverse needs two mouths, the done-check said no, the
author could not write a plan, the leg had been pushed twice, and the
wording rung would not void a leg the model rightly believed it had done.

A LEDGER OF WAYS-THROUGH WAS TRIED HERE AND WITHDRAWN. It kept the party's
own path instead of reading the graph, and rested on two different REGION
NAMES meaning two separate ends. A region name is an ANCHOR and anchors
drift as parts are joined, so one walkable component wears several over a
run: ROUTE_5 had six, and ROUTE_5|6,12 and ROUTE_5|6,16 both reach the DAY
CARE through the same cell. It filed that one-door building as a way
through (user, 2026-09-23), having already filed crossings nobody can walk.
A false way-through passes a Traverse leg in silence, which is worse than
the deadlock it was meant to prevent.

So the fix is where the loss was: the sweep records its own mouth, and the
two-mouth test on the walked graph answers as it always should have.

Pinned: the sweep records a map change it caused; it does so from the
observation before against the one after; a failure there never costs the
round; the two-mouth test is the only judge again, and reads both mouths
when the graph has them; and no parallel ledger remains. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

SRC = (ROOT / "planner/executor.py").read_text()
AU = (ROOT / "planner/author.py").read_text()
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ck("a sweep that changes the map records the edge it walked",
   "A DOOR IS A DOOR WHOEVER OPENED IT — and a sweep opens them." in SRC
   and '_sd = dict(_st, op="sweep")' in SRC
   and "self.note_transition(_pre_sweep, _sd, _after_sweep)" in SRC)
ck("...from the observation before it against the one after",
   "_pre_sweep = obs" in SRC and "_after_sweep = self.settle() or obs" in SRC
   and SRC.index("_pre_sweep = obs") < SRC.index("_after_sweep"))
ck("...only when the map actually changed",
   '_amap = ((_after_sweep or {}).get("map") or {}).get("id")\n'
   '                if ((_pre_sweep or {}).get("map") or {}).get("id") != _amap:'
   in SRC)
ck("...and a failure to record never costs the round",
   "pass            # an edge is never worth the round" in SRC)

ck("the withdrawn ledger is gone, not merely unused",
   "_note_through" not in SRC and "_went_in" not in SRC
   and '"through": dict(' not in SRC)
ck("...and why it went is written where it stood",
   "A WAY-THROUGH LEDGER LIVED HERE AND IS GONE" in SRC
   and "anchors drift as parts are joined" in SRC
   and "DAY CARE" in SRC)
ck("...and the author no longer reaches for it",
   "A PARALLEL WITNESS LIVED HERE AND IS GONE" in AU
   and 'd.get("through")' not in AU)

# ---- the two-mouth test, which is the judge again ----------------------
import json, tempfile  # noqa: E402
tmp = Path(tempfile.mkdtemp()) / "obs.json"


def through(edges):
    tmp.write_text(json.dumps({"explored": edges, "visits": {}}))
    return A._through_by_record("Traverse Mt. Moon", tmp)


BOTH = {"MT_MOON_B1F|20,2": {"27,3": {"to": "ROUTE_4|36,2"}},
        "MT_MOON_1F|3,2": {"5,3": {"to": "ROUTE_4|4,4"}}}
ONE = {"MT_MOON_B1F|20,2": {"27,3": {"to": "ROUTE_4|36,2"}}}
got = through(BOTH)
ck("with both mouths walked, the deed is found",
   got and "ROUTE_4|36,2" in got and "ROUTE_4|4,4" in got, got)
ck("...even though both mouths are on the SAME map",
   got and got.count("ROUTE_4|") == 2, got)
ck("with only the mouth it came out of, it is not",
   through(ONE) is None, through(ONE))
ck("...which is exactly what run 32 had, and why it stopped",
   through(ONE) is None)
ck("an objective that does not say through is left alone",
   A._through_by_record("Reach Cerulean City", tmp) is None)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
