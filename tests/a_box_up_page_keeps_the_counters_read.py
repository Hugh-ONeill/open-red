#!/usr/bin/env python3
"""With a prize list open, the page still says what the counters listed.

Run 67, 2026-10-28, leg 52: all three Game Corner counters were read and
kept, but a round ending on a prize list rendered the box-up page, which
returned before the run's records, and the "not a prize here" note read
its map from a snapshot with none. The model, looking at TM23/TM15/TM50,
wrote that it would go back to the slots for more coins for a SECRET_KEY.

Pinned: both box-up pages carry PRIZE COUNTERS YOU HAVE READ, and the
not-a-prize note answers on the floor under the box.
"""
import os
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
import ledger as L  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

X = E.Executor
V = "TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_"
PL = {"GAME_CORNER_PRIZE_ROOM": {
    V + "1": ["ABRA (180 coins)"], V + "2": ["DRATINI (2800 coins)"],
    V + "3": ["TM23 (3300 coins)"]}}
ex = types.SimpleNamespace(
    _prize_lists=PL, _shelves={},
    sightings={"GAME_CORNER_PRIZE_ROOM|0,3": [V + "1", V + "2", V + "3"]},
    _last_mapped_obs={"map": {"id": "GAME_CORNER_PRIZE_ROOM", "region": "0,3"}})
ex._prize_lists_line = lambda: X._prize_lists_line(ex)
line = L._box_prize_line(ex)
ck("the box-up line carries the counters read",
   "PRIZE COUNTERS YOU HAVE READ" in line and "DRATINI" in line, line)
ck("...and nothing when none were read",
   L._box_prize_line(types.SimpleNamespace(_prize_lists_line=lambda: "")) == "")
src = (ROOT / "planner" / "ledger.py").read_text()
ck("both box-up returns append it",
   src.count("_box_prize_line(ex))") == 2)

box = {"map": {"id": None}, "ui": {"rows": ["1=TM23 (3300 coins)", "4=CANCEL"]}}
note = X._shelf_note(ex, "I will gamble more coins to buy the SECRET_KEY", box)
ck("the not-a-prize note answers under a box",
   "SECRET_KEY" in note and "not a prize here" in note, note)

note = X._shelf_note(ex, "I have the COIN_CASE; I will buy the SECRET_KEY",
                     {"map": {"id": None}, "bag": {"COIN_CASE": 1}})
ck("...naming only what is not already in the bag",
   "SECRET_KEY" in note and "COIN_CASE" not in note, note)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
