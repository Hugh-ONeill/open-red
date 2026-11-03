#!/usr/bin/env python3
"""The outline upkeep asks for levels as a question of their own.

Run 71, 2026-11-03: asked what the party must become beside types, moves
and catches, the model wrote a curve of level legs in nine of 27 candidate
outlines since 2026-09-23 and one "level 50" leg in the rest. Run 71 played
one of the rest: its train rule never ran and PIKACHU and PIDGEY were L8 at
Erika (user: "part of what made that one outline with the mistakes good was
that it had regular leveling legs"; chose the own-question fix).

Pinned: after the upkeep rounds one more pass runs with the levels
question; it adds only "every party member is at least level N" states, at
the places the model gives; other kinds and exact repeats are dropped; its
additions are recorded as upkeep; the prompt names no level number.
Synthetic: the model is stubbed.
"""
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

LEGS = ["Pick a starter", "Defeat Brock for the Boulder Badge",
        "Defeat Misty for the Cascade Badge",
        "every party member is at least level 50", "Defeat the Champion"]

asked = []
def fake(msgs, model):
    sysm = msgs[0]["content"]
    asked.append(sysm)
    if sysm == A.OUTLINE_LEVELS_SYS:
        return json.dumps([
            {"item": "every party member is at least level 12", "after": 1,
             "for": "Brock"},
            {"item": "every party member is at least level 22", "after": 2,
             "for": "Misty"},
            {"item": "the party holds a WATER type", "after": 1},
            {"item": "every party member is at least level 50", "after": 3}])
    return "[]"

_real, _path = A.brock_probe.chat, A.UPKEEP_PATH
A.brock_probe.chat = fake
A.UPKEEP_PATH = Path(tempfile.mkdtemp()) / "upkeep.test"
try:
    out = A._outline_upkeep("Become the Champion", list(LEGS), "m", rounds=1)
    up = A.UPKEEP_PATH.read_text() if A.UPKEEP_PATH.exists() else ""
finally:
    A.brock_probe.chat, A.UPKEEP_PATH = _real, _path

ck("the levels question is asked after the upkeep round",
   len(asked) == 2 and asked[0] == A.OUTLINE_UPKEEP_SYS
   and asked[1] == A.OUTLINE_LEVELS_SYS, [a[:40] for a in asked])
ck("a level leg lands where the model put it",
   out[:3] == ["Pick a starter", "every party member is at least level 12",
               "Defeat Brock for the Boulder Badge"], out)
ck("...and the next one before the gym it is for",
   out.index("every party member is at least level 22")
   == out.index("Defeat Misty for the Cascade Badge") - 1, out)
ck("another kind is not this question's to add",
   "the party holds a WATER type" not in out, out)
ck("a level already on the list is not added twice",
   out.count("every party member is at least level 50") == 1, out)
ck("its additions are recorded as upkeep",
   "level 12" in up and "level 22" in up, up)
ck("the question names no level number of its own",
   not re.search(r"level \d", A.OUTLINE_LEVELS_SYS), A.OUTLINE_LEVELS_SYS)
ck("the shape accepts only an every-member level state",
   A._LEVEL_SHAPE.match("every party member is at least level 30")
   and not A._LEVEL_SHAPE.match("the lead Pokemon is at least level 30"))

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
