#!/usr/bin/env python3
"""The walker's page says when its plan puts a thing on a floor this run has
walked to its end, as the rewrite and sentence rungs already were told.

Run 67, 2026-10-28, Rocket Hideout: every part of B4F on screen and all of
it pressed or taken, and the run wrote "The Secret Key is located on the
bottom floor (B4F)" round after round and went back down to look again.

Pinned: said for an unheld item on the floor named or stood on; not for
an item in the bag; not for an elevator FLOOR_ value; not for a floor with
something untouched. Synthetic, on a temp record.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

REC = {"visits": {"ROCKET_HIDEOUT_B4F|17,1": 3, "ROCKET_HIDEOUT_B3F|1,1": 2},
       "frontier_here": {"ROCKET_HIDEOUT_B4F|17,1": 0},
       "sightings": {"ROCKET_HIDEOUT_B4F|17,1": ["ITEM_ROCKET_HIDEOUT_B4F_10_12"]},
       "touched": {"ROCKET_HIDEOUT_B4F|17,1": ["ITEM_ROCKET_HIDEOUT_B4F_10_12"]}}
d = Path(tempfile.mkdtemp(prefix="floornote_"))
(d / "run").mkdir()
here = os.getcwd()
os.chdir(d)
try:
    (d / "run/explored.json").write_text(json.dumps(REC))
    ex = E.Executor.__new__(E.Executor)
    ex.visits = REC["visits"]
    ex._last_mapped_obs = None
    B3 = {"map": {"id": "ROCKET_HIDEOUT_B3F"}, "bag": {}}
    n = ex._emptied_floor_note("The SECRET KEY is on ROCKET HIDEOUT B4F, FLOOR_B4F", B3)
    ck("a floor the plan names, walked to its end, is said",
       "You said SECRET_KEY" in n and "not on ROCKET_HIDEOUT_B4F" in n, n)
    ck("...and an elevator floor value is not taken for an item", "FLOOR_B4F IS" not in n, n)
    n = ex._emptied_floor_note("I will search for the SECRET KEY here",
                               {"map": {"id": "ROCKET_HIDEOUT_B4F"}, "bag": {}})
    ck("the floor stood on counts too", "not on ROCKET_HIDEOUT_B4F" in n, n)
    ck("an item already held is not said",
       ex._emptied_floor_note("the SECRET KEY on ROCKET HIDEOUT B4F",
                              {"map": {"id": "ROCKET_HIDEOUT_B4F"}, "bag": {"SECRET_KEY": 1}}) == "")
    REC["sightings"]["ROCKET_HIDEOUT_B4F|17,1"].append("ROCKETHIDEOUTB4F_ROCKET1")
    (d / "run/explored.json").write_text(json.dumps(REC))
    ck("a floor with something untouched is not said",
       ex._emptied_floor_note("the SECRET KEY on ROCKET HIDEOUT B4F", B3) == "")
finally:
    os.chdir(here)

src = (ROOT / "planner" / "executor.py").read_text()
ck("the round's results carry it beside the shelf note",
   "_floor = self._emptied_floor_note(self._plan_said, self.settle() or obs)" in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
