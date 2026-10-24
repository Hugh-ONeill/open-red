#!/usr/bin/env python3
"""A line the run's own blocker record quotes is among a place's four lines
in WHAT PEOPLE HAVE SAID, ahead of the newest.

Run 62, 2026-10-24: Cinnabar Island's four lines were three signs and
"REDDY got on PUDGE!"; "The door is locked..." from the Gym door it had
walked into four times (blockers CINNABAR_ISLAND|10,0|18,3) was cut, and the
rewrite's ideas read "The gym is currently open and enterable (from: memory)
— heard: nothing heard", planning the walk to the locked door again.

Pinned: the blocker's quoted words are shown even when four newer lines
exist; a place with no blocker keeps its newest four.
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

R = "CINNABAR_ISLAND|10,0"
LINES = ["someone: The door is locked...",
         "CINNABARISLAND_GIRL: CINNABAR GYM's BLAINE is an odd man.",
         "CINNABARISLAND_GAMBLER: Scientists conduct experiments in the burned out building.",
         "SIGN_CINNABAR_ISLAND_9_5: CINNABAR ISLAND The Fiery Town",
         "SIGN_CINNABAR_ISLAND_16_11: All your item needs fulfilled! POKeMON MART",
         "SIGN_CINNABAR_ISLAND_12_11: Heal Your POKeMON! POKeMON CENTER",
         "someone: REDDY got on PUDGE!"]


def said(blocked):
    d = {"hints": {R: LINES}, "visits": {R: 9},
         "explored": {R: {"6,3": {"to": "POKEMON_MANSION_1F|1,1", "n": 3}}}}
    if blocked:
        d["blockers"] = {R + "|18,3": {"where": R, "key": "18,3", "kind": "door",
                                       "what": '"The door is locked..."'}}
    tmp = Path(tempfile.mkdtemp())
    p = tmp / "explored.json"
    p.write_text(json.dumps(d))
    A._PEOPLE_SECTION.pop(str(p), None)
    return A.people_said_text(str(p))


t = said(True)
ck("the blocker's words are among the four", "The door is locked..." in t, t)
ck("...four lines still", t.count("\n    ") == 4, t)
t0 = said(False)
ck("with no blocker the newest four stand", "The door is locked..." not in t0
   and "REDDY got on PUDGE!" in t0, t0)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
