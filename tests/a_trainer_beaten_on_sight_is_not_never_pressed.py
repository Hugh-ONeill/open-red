#!/usr/bin/env python3
"""A trainer beaten on sight is not "a thing never pressed" anywhere.

Run 66, 2026-10-25, leg "every party member is at least level 40": Silph
4F's ROCKET1 and ROCKET2 had walked up and fought (EVENT_BEAT_SILPH_CO_4F_
TRAINER_0..2 fired) and were never pressed, so the touched ledger never
learned them, and the rows for doors into 4F read "4 thing(s) never pressed
(DOOR_SILPH_CO_4F_4_12, SILPHCO4F_ROCKET1, SILPHCO4F_ROCKET2)". The model went
4F -> 6F -> 4F -> 11F -> 4F for "the remaining unpressed trainers".

Pinned: a trainer the screen showed as beaten is recorded, kept across a
save, and dropped from untouched_in; an unbeaten one stays.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
import ledger  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = E.Executor.__new__(E.Executor)
ex.sightings = {"SILPH_CO_4F|20,0": ["DOOR_SILPH_CO_4F_4_12", "SILPHCO4F_ROCKET1",
                                     "SILPHCO4F_ROCKET2", "SILPHCO4F_SCIENTIST"]}
ex._tried_objs = {}
ex._gone = {}
ex._touched_on_map = lambda r: set()
ex._where = lambda o: "SILPH_CO_4F|20,0"
ex._note_bush_ways = lambda o, h: None
ex._note_sides_unseen = lambda o: None
ex.log = lambda *a, **k: None
ex._save_memory = lambda: None

before = ledger.untouched_in(ex, "SILPH_CO_4F|20,0")
ck("before, the beaten pair read as never pressed",
   {"SILPHCO4F_ROCKET1", "SILPHCO4F_ROCKET2"} <= set(before), before)

obs = {"map": {"id": "SILPH_CO_4F", "region": "20,0", "objects": [
    {"name": "SILPHCO4F_ROCKET1", "kind": "trainer", "beaten": True, "reachable": True},
    {"name": "SILPHCO4F_ROCKET2", "kind": "trainer", "beaten": True, "reachable": True},
    {"name": "SILPHCO4F_SCIENTIST", "kind": "trainer", "beaten": False, "reachable": True},
    {"name": "DOOR_SILPH_CO_4F_4_12", "kind": "shut_door", "reachable": True}]}}
try:
    ex.note_sightings(obs)
except Exception:  # the rest of note_sightings needs more rig; the record is first
    pass
ck("the screen's beaten trainers are recorded",
   {"SILPHCO4F_ROCKET1", "SILPHCO4F_ROCKET2"} <= set(getattr(ex, "_beaten_seen", ())),
   getattr(ex, "_beaten_seen", None))
after = ledger.untouched_in(ex, "SILPH_CO_4F|20,0")
ck("...and are no longer things never pressed",
   "SILPHCO4F_ROCKET1" not in after and "SILPHCO4F_ROCKET2" not in after, after)
ck("an unbeaten trainer and a door stay",
   "SILPHCO4F_SCIENTIST" in after and "DOOR_SILPH_CO_4F_4_12" in after, after)

src = (ROOT / "planner/executor.py").read_text()
ck("the record is saved and loaded",
   '"beaten_seen": sorted(getattr(self, "_beaten_seen", None) or ())' in src
   and 'self._beaten_seen = set(data.get("beaten_seen") or [])' in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
