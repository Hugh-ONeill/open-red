#!/usr/bin/env python3
"""The upkeep question asks what each party leg is FOR, and the answer
rides with the leg into the outline's notes.

2026-09-24, the user: "it wouldnt sting so much if the type catches made
sense but they dont half the time". Counted over ten outlines: 25 of 44
"or" type legs standing before a gym carried a half that did nothing for
it, "or PSYCHIC" eleven times. The question asked what should be true of
the party and where, never what for, so a pair was a counter and a hedge.

MEASURED, the upkeep pass alone, four passes each on the same story legs:
without the field, 28 type legs, 19 hit the gym after them, 12 named
WATER, 11 of 21 pairs carried a dead half; with it, 24 type legs, 15
named a gym as their purpose and 14 of those hit it, 7 named WATER, 5 of
13 gym-aimed pairs carried a dead half. The each-ball method, applied to
the party legs: say what each is for before keeping it.

Pinned: the reply format asks for it and says why; a purpose given is
kept in the notes as "for: ..." beside its leg; none given is nothing;
the field is trimmed; nothing names a type or a gym to want. Synthetic."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import brock_probe  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


flat = " ".join(A.OUTLINE_UPKEEP_SYS.split())
ck("the reply format asks what each one is for",
   '"for": "<what this one is for, in a few words' in flat)
ck("...and says why: a party objective that serves nothing is not missing",
   "Say what each is for before you keep it" in flat
   and "serves nothing you can name is not missing" in flat)
_ask = flat[flat.index('"for":'):]
ck("the ask itself names no type and no gym to want",
   not any(w in _ask for w in ("WATER", "GRASS", "FIRE", "Brock", "Misty",
                                 "Surge", "Erika", "Koga", "Sabrina",
                                 "Blaine", "Giovanni"))
   and "should" not in _ask.lower(), _ask)

LEGS = ["Choose a starter Pokemon", "Reach Pewter City",
        "Defeat Brock for the Boulder Badge", "Reach Cerulean City"]
REPLY = json.dumps([
    {"item": "the party holds a FIGHTING or GRASS type", "after": 1,
     "for": "3"},
    {"item": "every party member is at least level 12", "after": 1,
     "for": "  Brock's  Onix   is level 14 "},
    {"item": "the party has at least 2 Pokemon", "after": 0},
])
brock_probe.chat = lambda msgs, model, **kw: REPLY
A.OUTLINE_NOTES.clear()
A.UPKEEP_TWINS.clear()
out = A._outline_upkeep_once("Become the Champion", list(LEGS), "m")
notes = dict(A.OUTLINE_NOTES)
ck("the legs are added as before",
   "the party holds a FIGHTING or GRASS type" in out
   and "every party member is at least level 12" in out
   and "the party has at least 2 Pokemon" in out, out)
ck("a purpose given rides in the notes beside its leg, a number as its leg",
   notes.get("the party holds a FIGHTING or GRASS type")
   == "for: Defeat Brock for the Boulder Badge", notes)
ck("...whitespace folded", notes.get("every party member is at least level 12")
   == "for: Brock's Onix is level 14", notes)
ck("none given is nothing", "the party has at least 2 Pokemon" not in notes)
# a twin re-proposed in a later round adds no second purpose
brock_probe.chat = lambda msgs, model, **kw: json.dumps(
    [{"item": "the party holds a FIGHTING or GRASS type", "after": 1, "for": "the rock gym"}])
out2 = A._outline_upkeep_once("Become the Champion", list(out), "m")
ck("a leg re-proposed as a twin keeps its one purpose",
   [k for k, _ in A.OUTLINE_NOTES].count("the party holds a FIGHTING or GRASS type") == 1
   and out2.count("the party holds a FIGHTING or GRASS type") == 1, A.OUTLINE_NOTES)
ck("the notes are the sidecar the leg's plan author reads",
   "OUTLINE_NOTES" in (ROOT / "planner/author.py").read_text()
   and "notes.write_text" in (ROOT / "planner/author.py").read_text())

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
