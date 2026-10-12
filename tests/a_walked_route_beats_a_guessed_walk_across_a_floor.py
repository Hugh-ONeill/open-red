#!/usr/bin/env python3
"""A walked route beats a guessed walk across a floor, and such a walk is
named in words.

Run 53 (2026-10-11): Cerulean's back yard, the city's only way south, is
reached through the burgled house (door 27,11, then its back wall 3,0).
The yard had once been walked down out of into town, so the router offered
the reverse as a one-leg guess, which beat the two walked legs, and the
page read "1 leg(s) away, first: walk walk:CERULEAN_CITY|26,7 to ...". The
run went round the square and the badge house for a leg and a half.

Pinned on run 53's own Cerulean record: the route from the square goes by
the house; with the house's edges gone the guess is still offered; the
first leg of a walk across the map reads as words, guess said. Mixed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
import ledger         # noqa: E402

REC = json.loads((ROOT / "tests/fixtures/run53_cerulean/explored.json").read_text())
SQ, YARD = "CERULEAN_CITY|20,0", "CERULEAN_CITY|26,7"
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def ex_with(explored):
    ex = E.Executor.__new__(E.Executor)
    ex.explored = json.loads(json.dumps(explored))
    ex._bad_seam = set()
    ex._mark_now = None
    return ex


ex = ex_with(REC["explored"])
r = ex._route(SQ, YARD)
ck("from the square the yard is reached by the burgled house, walked",
   r and [k for k, _ in r] == ["27,11", "3,0"], r)
ck("...not by the guessed walk across the floor",
   r and not any(str(k).startswith("walk:") for k, _ in r), r)

bare = {SQ: {}, YARD: {f"walk:{SQ}": REC["explored"][YARD][f"walk:{SQ}"]}}
r2 = ex_with(bare)._route(SQ, YARD)
ck("with no walked way, the guess is still offered", r2 and r2[0][0] == f"walk:{YARD}", r2)

w = ledger.leg_words(ex_with(bare), SQ, f"walk:{YARD}")
ck("a walk across the map reads as words, and the guess is said",
   w.startswith("walk across this map") and "never walked this way" in w
   and "walk:" not in w, w)
ck("a door still reads as a door", ledger.leg_words(ex, SQ, "27,11") == "door (27,11)")

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
