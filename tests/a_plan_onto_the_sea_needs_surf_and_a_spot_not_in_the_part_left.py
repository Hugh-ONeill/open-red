#!/usr/bin/env python3
"""Plan validation: a step onto a sea route needs SURF, and a spot is not in
the part the step before left.

Run 68, 2026-10-28: "Reach Vermilion City" was accepted as a 22-step world
loop through Cinnabar by water with no SURF in the party. Run 70's Route 23
watch (2026-11-02) asked whether a player_at inside the part the step before
rules out should be refused. User, 2026-11-04: mark the sea routes (the
booklet's map draws Routes 19-21 as sea); for player_at, refuse only what is
certain, a spot on the excluded part's own first cell.

Pinned: a step ending on ROUTE_21 is refused with nobody knowing SURF; not
when a party member knows it; not when an earlier step teaches it; a land
route is not refused; a player_at on the excluded part's first cell right
after the not_area step is refused; a spot elsewhere is not. Synthetic.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BD = Path(os.environ.get("RED_BRIDGE_DIR") or tempfile.mkdtemp())
os.environ["RED_BRIDGE_DIR"] = str(BD)
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))


def party(moves):
    (BD / "obs.json").write_text(json.dumps({"party": [
        {"species": "BLASTOISE", "level": 40, "moves": [{"id": m} for m in moves]}]}))


def plan(*steps):
    return {"goal": "x", "subgoals": [
        {"id": f"s{i}", "goal_text": "a step", "done_when": dw}
        for i, dw in enumerate(steps)]}


def sea_refused(p):
    return [x for x in A.validate(p) if "draws as sea" in x]


party(["TACKLE", "WATER_GUN"])
ck("a step ending on a sea route is refused with nobody knowing SURF",
   sea_refused(plan({"map": "PALLET_TOWN"}, {"map": "ROUTE_21"})))
party(["SURF"])
ck("...not when a party member knows SURF",
   not sea_refused(plan({"map": "PALLET_TOWN"}, {"map": "ROUTE_21"})))
party(["TACKLE"])
ck("...not when an earlier step teaches it",
   not sea_refused(plan({"knows_move": "SURF"}, {"map": "ROUTE_21"})))
ck("a land route is not refused",
   not sea_refused(plan({"map": "ROUTE_1"})))

p7 = plan({"map": "ROUTE_23", "not_area": ["ROUTE_23|5,140"]},
          {"map": "ROUTE_23", "player_at": {"x": 5, "y": 140, "radius": 1}})
ck("a spot on the excluded part's first cell is refused",
   any("the part the step before it" in x for x in A.validate(p7)), A.validate(p7))
p8 = plan({"map": "ROUTE_23", "not_area": ["ROUTE_23|5,140"]},
          {"map": "ROUTE_23", "player_at": {"x": 9, "y": 30, "radius": 1}})
ck("a spot elsewhere is not", not any("the part the step before it" in x for x in A.validate(p8)))

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
