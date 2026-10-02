#!/usr/bin/env python3
"""An attempt's yield says which maps were never stood on before, apart from
new parts of maps already walked, so roll-with-it rests on new areas only.

Run 25 (2026-10-02) rolled onto "Retrieve the Secret Key from the Game
Corner" citing CELADON_CITY, a new part of a city walked all afternoon, and
went back into a Game Corner it had cleared. User: "the roll-with-it is
supposed to be for new areas not already searched ones".
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


import json
import subprocess
cwd = Path(tempfile.mkdtemp()); (cwd / "run").mkdir()
obs = {"flags": [], "bag": {}, "badges": [], "party": [], "map": {"id": "CELADON_CITY"}}
(cwd / "run/obs.json").write_text(json.dumps(obs))
(cwd / "run/explored.json").write_text(json.dumps({"visits": {"CELADON_CITY|2,1": 9, "GAME_CORNER|8,5": 3}}))
LD = str(ROOT / "planner/leg_delta.py")
subprocess.run([sys.executable, LD, "snap", "run/before.json"], cwd=cwd, check=True)
(cwd / "run/explored.json").write_text(json.dumps({"visits": {
    "CELADON_CITY|2,1": 9, "GAME_CORNER|8,5": 3, "CELADON_CITY|30,20": 1,
    "GAME_CORNER|1,1": 1, "ROCKET_HIDEOUT_B1F|21,2": 1}}))
t = subprocess.run([sys.executable, LD, "diff", "run/before.json"], cwd=cwd,
                   capture_output=True, text=True).stdout
ck("new parts are still counted as places", "3 place(s) entered for the first time" in t, t)
ck("...and only the map new at all is named as never stood on",
   "1 map(s) never stood on before: ROCKET_HIDEOUT_B1F" in t, t)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
