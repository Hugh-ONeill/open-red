#!/usr/bin/env python3
"""Outline lines name what, not where; a worked building is refused by name.

Run 70, 2026-11-02 (outline false facts, ideas 1-3; user at the stop): every
outline drawn or rewritten put the Secret Key somewhere it was not (Game
Corner, prize counter, Rocket Hideout, Silph president), each a guess the
plans inherited as fact, and the rewrite "from the Rocket Hideout" passed the
emptied-floor refusal because "Rocket Hideout" names no single map id.

Pinned: the line-writing prompts carry the what-not-where and lock rules;
the insert prompt no longer asks for "the place it happens in"; the reword
and insert prompts allow a place only where the run saw or was told; and on
a synthetic ledger a building family whose every stood floor is worked and
every door gone through is refused by name, while one with a door never
taken, or a floor with ground left, is not.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

W = getattr(A, "WHAT_NOT_WHERE", "")
ck("the rule exists and names no place or item",
   "NAME WHAT, NOT WHERE" in W and "COMES WHEN THE LOCK DOES" in W
   and not any(x in W for x in ("Secret", "Corner", "Hideout", "Cinnabar")))
for v in ("OUTLINE_SYS", "ERA_LIST_ASK", "GAP_SYS", "STAGE_MISSING_SYS"):
    ck(f"{v} carries it", W and W in getattr(A, v))
ck("the insert prompt no longer asks for the place it happens in",
   "with\nthe place it happens in" not in A.CHECKMISSING_SYS
   and "SAY WHERE ONLY WHAT THE RUN HAS SEEN" in A.CHECKMISSING_SYS
   and "A FETCH ANSWERS A LOCK THE RUN HAS MET" in A.CHECKMISSING_SYS)
ck("the reword prompt allows a place only where it was seen or said",
   "it may name a PLACE only where the\nrun SAW the thing" in A.WORDING_SYS)


def ledger(door_taken=True, ground_left=0):
    regs = {"ROCKET_HIDEOUT_B1F|19,1": 3, "ROCKET_HIDEOUT_B2F|19,7": 2,
            "ROCKET_HIDEOUT_ELEVATOR|2,1": 1}
    return {"visits": regs,
            "frontier_here": {r: (ground_left if "B2F" in r else 0) for r in regs},
            "region_seen": {r: 0 for r in regs},
            "sightings": {"ROCKET_HIDEOUT_B1F|19,1": ["ITEM_ROCKET_HIDEOUT_B1F_1_1"]},
            "touched": {"ROCKET_HIDEOUT_B1F|19,1": ["ITEM_ROCKET_HIDEOUT_B1F_1_1"]},
            "map_doors": {"ROCKET_HIDEOUT_B1F": ["21,2", "23,2"],
                          "ROCKET_HIDEOUT_B2F": ["21,8"],
                          "ROCKET_HIDEOUT_ELEVATOR": ["2,1", "3,1"]},
            "explored": {"ROCKET_HIDEOUT_B1F|19,1": {"21,2": {}, "23,2": {}},
                         "ROCKET_HIDEOUT_B2F|19,7": ({"21,8": {}} if door_taken else {})}}


def judge(text, **kw):
    f = Path(tempfile.mkdtemp()) / "explored.json"
    f.write_text(json.dumps(ledger(**kw)))
    return A.names_an_emptied_floor(text, str(f))


r = judge("Obtain the Secret Key from the Rocket Hideout in Celadon City")
ck("a worked building is refused by its name", r and "Rocket Hideout" in r and "SECRET_KEY" in r, r)
ck("...not when a door on a stood floor was never gone through",
   judge("Retrieve the Secret Key from the Rocket Hideout", door_taken=False) is None)
ck("...nor when a floor still has ground left",
   judge("Retrieve the Secret Key from the Rocket Hideout", ground_left=4) is None)
ck("...nor for a line that names no place",
   judge("Obtain the Secret Key") is None)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
