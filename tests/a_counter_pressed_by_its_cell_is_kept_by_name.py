#!/usr/bin/env python3
"""A prize counter opened by an x,y press is kept under the counter's name.

Run 67, 2026-10-28, leg 52: VENDOR_2 (4,2) and VENDOR_3 (6,2) were opened
with x,y presses while VENDOR_1's list was still up. The press carried no
name and the snapshot no map, so neither list was kept, and every page
after said both were "never read" while the leg was rewritten to buy the
Secret Key there again.

The same day, presses by name with VENDOR_1's box still up were lost the
same way: the snapshot read no map.

Pinned: the cell gives the name the map lists there, a box-hidden map
falls back to the last mapped one, and the recorder is reached for such a
press.
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

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

X = E.Executor
V2 = "TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_2"
ROOM = {"map": {"id": "GAME_CORNER_PRIZE_ROOM", "region": "0,3", "objects": [
    {"kind": "sign", "name": "TEXT_GAMECORNERPRIZEROOM_PRIZE_VENDOR_1", "x": 2, "y": 2},
    {"kind": "sign", "name": V2, "x": 4, "y": 2}]}}
st = types.SimpleNamespace(_where=X._where, _last_mapped_obs=ROOM)
ck("a cell on the map names its counter",
   X._press_at_cell(st, {"x": 4, "y": 2}, ROOM) == ("GAME_CORNER_PRIZE_ROOM|0,3", V2))
ck("...and with a box up, the last mapped map stands in",
   X._press_at_cell(st, {"x": 4, "y": 2}, {"map": {}}) == ("GAME_CORNER_PRIZE_ROOM|0,3", V2))
ck("a cell with nothing listed names nothing",
   X._press_at_cell(st, {"x": 5, "y": 5}, ROOM)[1] is None)
ck("a named press with a box up keeps its name on the last mapped map",
   X._press_at_cell(st, {"name": V2}, {"map": {}}) == ("GAME_CORNER_PRIZE_ROOM|0,3", V2))
st2 = types.SimpleNamespace(_where=X._where, _last_mapped_obs=None)
ck("no map anywhere names nothing",
   X._press_at_cell(st2, {"x": 4, "y": 2}, {"map": {}}) == (None, None))

src = (ROOT / "planner" / "executor.py").read_text()
i = src.find("A COUNTER PRESSED BY ITS CELL IS STILL THAT COUNTER")
ck("the landing path records a cell press", i > 0
   and "self._press_at_cell(step, pre_obs)" in src[i:i + 900]
   and "self._record_prize_list(_hr, _nm, obs)" in src[i:i + 900])

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
