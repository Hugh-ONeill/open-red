#!/usr/bin/env python3
"""Run 21's S.S. Ticket knot (2026-10-02): three ways the harness turned the
right direction down or let a weak one through.

1. "Pay the toll to cross the Nugget Bridge on Route 24" was refused three
   times as naming ROUTE_2, the road the leg had just failed to walk:
   squashed, "ROUTE2" sits inside "ONROUTE24".
2. "Visit Bill in his house on Route 25" was refused as "met by arriving",
   though the thing after the verb is a person, not a place.
3. The momentum rung rolled onto a party leg citing "IVYSAUR 21->22", a
   level line, as the ground it had walked.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


td = Path(tempfile.mkdtemp())
j = td / "log.jsonl"


def journal(failed_place):
    j.write_text("\n".join(json.dumps(r) for r in [
        {"kind": "plan_start", "goal": "Retrieve the S.S. Ticket"},
        {"kind": "escalate_context", "subgoal": "s1", "target": f"map:{failed_place}"},
        {"kind": "escalate_end", "subgoal": "s1", "success": False}]) + "\n")
    return j


f = A._reword_points_at_what_failed
ck("ROUTE_2 does not match inside Route 24",
   f("Pay the toll to cross the Nugget Bridge on Route 24", journal("ROUTE_2")) is None)
ck("...but still matches Route 2 itself", f("Go back along Route 2", journal("ROUTE_2")) == "ROUTE_2")
ck("...and a squashed name still matches its punctuated form",
   f("Retrieve it from the captain of the S.S. Anne", journal("SS_ANNE_1F")) == "SS_ANNE")
ck("...and Route 24 still matches Route 24", f("Cross Route 24", journal("ROUTE_24")) == "ROUTE_24")

v = A._visits_a_person
ck("visiting a person is a meeting", v("Visit Bill in his house on Route 25")
   and v("Visit Mr. Fuji in his house") and v("Visit Professor Oak"))
ck("visiting a place is still an arrival", not v("Visit Cerulean City") and not v("Go to Bill's house")
   and not v("Visit the Pokemon Center") and not v("Visit Oak's lab") and not v("Enter Mt. Moon"))
src = (ROOT / "planner/author.py").read_text()
ck("the arrival refusal asks it", "and not _visits_a_person(ins):" in src)

g = ("WHAT CHANGED WHILE THIS LEG RAN — events that fired: EVENT_BEAT_ROUTE_24_TRAINER_0; "
     "2 place(s) entered for the first time — by map: ROUTE_24 x1, ROUTE_25 x1; "
     "levels gained: IVYSAUR 21->22; joined the party: ODDISH")
ground = A._momentum_ground(g)
ck("momentum's ground holds places and events", "ROUTE_25" in ground and "EVENT_BEAT_ROUTE_24" in ground)
ck("...not levels or party changes", "IVYSAUR" not in ground and "ODDISH" not in ground, ground)
A.chat_json = lambda m, mo: json.dumps({"why": "x", "leg": 16, "from": "IVYSAUR 21->22"})
ck("a pick resting on a level line is refused",
   A.check_momentum("g", 13, [(16, "the party holds a GRASS type")], "", g, "m") is None)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
