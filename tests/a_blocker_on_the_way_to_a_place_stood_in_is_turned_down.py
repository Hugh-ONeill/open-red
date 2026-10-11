#!/usr/bin/env python3
"""A missing-step reason that the way to a place is blocked is turned down
when the run has stood in that place.

Run 47 (2026-10-11): the L40 leg failed grinding on Route 15, and the
missing rung answered "The player is on Route 15 trying to reach Fuchsia
City, but the path is blocked by a gate that requires a specific item to
pass through" — with FUCHSIA_CITY already stood in — and inserted "Obtain
the SECRET KEY from the Celadon Game Corner", which walked the run back to
Celadon (user: "this damn secret key nonsense?").

Pinned on run 47's words: the blocker to a place stood in is caught; one
to a place never stood in, a plain "needs to reach", and a reason with no
way-to are not; the rung turns it down before its other reason checks.
Synthetic.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
    json.dump({"visits": {"FUCHSIA_CITY|2,2": 1, "ROUTE_15|0,8": 9,
                          "SAFFRON_CITY|10,0": 3}}, f)
    OB = f.name

RUN47 = ("The player is on Route 15 trying to reach Fuchsia City, but the path is "
         "blocked by a gate that requires a specific item to pass through.")
ck("run 47's reason is caught on FUCHSIA_CITY",
   A._blocked_way_to_stood(RUN47, OB) == "FUCHSIA_CITY")
ck("...as is one that starts with the verb",
   A._blocked_way_to_stood("Entering Saffron City is blocked by a thirsty guard.", OB)
   == "SAFFRON_CITY")
ck("a blocker to a place never stood in is left alone",
   A._blocked_way_to_stood("The way to Cinnabar Island is blocked by water.", OB) is None)
ck("a plain 'needs to reach' is not a blocker",
   A._blocked_way_to_stood("The player needs to reach Fuchsia City to talk to the warden.",
                           OB) is None)
ck("a reason with no way-to is left alone",
   A._blocked_way_to_stood("The S.S. Ticket is blocked until Bill is helped.", OB) is None)
src = (ROOT / "planner/author.py").read_text()
cm = src[src.index("def check_missing("):]
ck("the missing rung turns it down, before the inferred-need check",
   "_stood = _blocked_way_to_stood(_why, observed)" in cm
   and cm.index("_blocked_way_to_stood(_why") < cm.index("if _inferred(_why):"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
