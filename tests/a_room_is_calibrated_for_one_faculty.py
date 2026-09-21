#!/usr/bin/env python3
"""A room is calibrated FOR A NAMED FACULTY, and the twin loses that one.

The nine rooms were built to separate a spec that heals from one that does
not, and they do it well: take the medicine away and the party dies, so the
room measures medicine. They say nothing about a spec that uses STATUS
MOVES. v15's four candidates tied at 8.24 to 8.41 of 9.00 with six rooms
cleared perfectly by every one of them, and both Celadon and Fuchsia
returned the same number for all four because what those rooms ran out of
was trainers reached, not fights won (2026-09-21). The user: "we might have
to recalibrate to seperate out policies, the previous calibration was to
seperate item usage from no item usage, this might have to be calibrated
differently."

So which faculty the twin loses is an argument. And a room can be decided
two ways: medicine shows up as blackouts, a status move need not — it wins
fights that would otherwise be lost — so both the blackout swing and the
share of the room are measured, and either can decide it.

Pinned: each faculty's twin loses that faculty and nothing else; a spec
with none of it is refused rather than scored against itself; the verdict
names the faculty; a room decided only by fights won is calibrated, not
too easy; the old medicine verdicts still read as they did. Synthetic."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import calibrate_arenas as C  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


SPEC = {"name": "v", "stab": 1.5, "prefer_ko": True,
        "battle_items": [{"item": "heal", "hp_below": 0.4}],
        "field_heal": {"hp_below": 0.5}, "field_cure": ["any"],
        "setup": [{"move": "LEECH_SEED", "per_foe": True},
                  {"move": "THUNDER_WAVE", "only_if_foe_clear": True}],
        "switch": [{"to": "best_matchup", "vs": "trainer"},
                   {"to": "healthiest", "out_of_pp": True}],
        "provenance": {"authored_by": "x"}}

med, setup = C.strip_medicine(SPEC), C.strip_setup(SPEC)
pp, sw = C.strip_pp(SPEC), C.strip_switch(SPEC)
ck("the medicine twin loses the medicine and keeps the rest",
   med["battle_items"] == [] and med["field_heal"] is None
   and med["field_cure"] == [] and med["setup"] == SPEC["setup"]
   and med["switch"] == SPEC["switch"])
ck("the status twin loses the status moves and keeps the rest",
   setup["setup"] == [] and setup["battle_items"] == SPEC["battle_items"]
   and setup["switch"] == SPEC["switch"]
   and setup["field_heal"] == SPEC["field_heal"])
ck("the out-of-PP twin loses only the rules that carry it",
   pp["switch"] == [{"to": "best_matchup", "vs": "trainer"}]
   and pp["setup"] == SPEC["setup"])
ck("the switch twin loses every switch",
   sw["switch"] == [] and sw["setup"] == SPEC["setup"])
for nm, t in (("medicine", med), ("setup", setup), ("pp", pp), ("switch", sw)):
    ck(f"the {nm} twin says in its name what it lost",
       t["name"].startswith("v_") and t["name"] != "v")
    ck(f"...and carries no provenance of the spec it came from",
       "provenance" not in t)
ck("nothing is mutated on the way", SPEC["setup"] and SPEC["switch"]
   and SPEC["battle_items"] and "provenance" in SPEC)

ck("every faculty is named, with the key it lives in",
   set(C.FACULTIES) == set(C._KEYS) == {"medicine", "setup", "pp", "switch"})
ck("...and each one's stripper is the function of that name",
   C.FACULTIES["setup"][0] is C.strip_setup
   and C.FACULTIES["medicine"][0] is C.strip_medicine)

SRC = (ROOT / "planner/calibrate_arenas.py").read_text()
ck("a spec with none of the faculty is refused, not scored against itself",
   'has no {_noun} to take away' in SRC and "return 2" in SRC)
ck("the twin that is scored is the faculty's, not the medicine's always",
   "bare = _strip(full)" in SRC and "bare = strip_medicine(full)" not in SRC)
ck("a room can be decided by blackouts or by the fights won",
   "decides = swing >= a.trials / 2 or gap >= 0.15" in SRC
   and "gap = wf - nf" in SRC)
ck("...and the verdict says which of the two decided it",
   '_by = (f"{swing} fewer blackout(s)" if swing > 0' in SRC
   and 'else f"{gap:.0%} more of the room")' in SRC)
ck("every verdict names the faculty rather than assuming medicine",
   SRC.count("{_noun}") >= 6 and "the medicine is what wins it\"" not in SRC)
ck("the table says which spec and which faculty it is reading",
   '{_noun} against no {_noun}' in SRC)

# ---- the verdicts themselves, worked the way main() works them ---------
def verdict(w, n, trials=2, noun="medicine", doing="healing"):
    wf, nf = w[0] / max(1, w[1]), n[0] / max(1, n[1])
    swing, gap = n[2] - w[2], wf - nf
    decides = swing >= trials / 2 or gap >= 0.15
    if gap <= -0.15 or swing <= -trials / 2:
        return "HARMFUL"
    if w[2] >= trials and not decides:
        return "TOO HARD"
    if wf >= 0.85 and decides:
        return "CALIBRATED"
    if nf >= 0.85 and not decides:
        return "TOO EASY"
    if decides:
        return "HARD"
    if wf < 0.5:
        return "TOO HARD"
    if swing <= 0 and gap <= 0:
        return "TOO EASY"
    return "THIN"


ck("a room the medicine saves from wiping is calibrated",
   verdict((16, 16, 0), (14, 16, 2)) == "CALIBRATED")
ck("a room both arms sweep is too easy",
   verdict((16, 16, 0), (16, 16, 0)) == "TOO EASY")
ck("...which is what all four v15 candidates met in six of nine rooms",
   verdict((10, 10, 0), (10, 10, 0)) == "TOO EASY")
ck("a room that wipes both arms every trial is too hard",
   verdict((4, 16, 2), (3, 16, 2)) == "TOO HARD")
ck("a room decided by FIGHTS WON and no blackout at all is calibrated",
   verdict((16, 16, 0), (12, 16, 0)) == "CALIBRATED", "gap 25%")
ck("...and the same gap where the full arm is also losing reads HARD",
   verdict((11, 16, 0), (7, 16, 0)) == "HARD")
ck("a room the stripped arm still all but sweeps is too easy, not thin",
   verdict((16, 16, 0), (15, 16, 0)) == "TOO EASY", "one fight in sixteen")
ck("...and THIN is for a room neither arm takes cleanly",
   verdict((13, 16, 0), (11, 16, 0)) == "THIN")
ck("Celadon as it scored for every v15 candidate measures nothing",
   verdict((12, 16, 0), (12, 16, 0)) == "TOO EASY")
# A FACULTY CAN COST A ROOM. Brock, four trials an arm, the run's own
# status rules against the same spec with none (2026-09-21): 3 fights of 8
# with them and 7 of 8 without, three blackouts against one. Read as TOO
# EASY that is true and useless; the rules were spending two of the
# fight's turns on GROWL and LEECH_SEED with a L12 BULBASAUR in front of a
# L14 ONIX.
ck("a faculty that costs the room is named as costing it",
   verdict((3, 8, 3), (7, 8, 1), trials=4) == "HARMFUL")
ck("...by blackouts alone as well",
   verdict((8, 8, 3), (8, 8, 0), trials=4) == "HARMFUL")
ck("...and a faculty that costs one fight in sixteen is not",
   verdict((15, 16, 0), (16, 16, 0)) != "HARMFUL")
SRC2 = (ROOT / "planner/calibrate_arenas.py").read_text()
ck("the harmful verdict is tried before any other",
   SRC2.index("HARMFUL — the {_noun} COSTS it")
   < SRC2.index("TOO HARD — it wipes every trial"))
ck("...and says how much of the room it cost",
   '{-gap:.0%} of the room' in SRC2 and "{-swing} more blackout(s)" in SRC2)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:220]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
