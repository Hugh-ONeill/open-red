#!/usr/bin/env python3
"""A press by coordinates that fails at a cell nobody stands on says so,
and names who this room has lost.

Run 65, 2026-10-25: the Game Corner Rocket was beaten at (9,5), said "Our
hideout might be discovered! I better tell BOSS!" and left the room. The run
pressed (9,5) to ask him for the Secret Key, and "no reachable tile adjacent
to target -- standing on the tiles you would press from: POSTER at (9,4)"
read as a man still standing there, out of reach, for rounds (user: "it
thinks the rocket is still there just unreachable").

Pinned: an empty cell says nothing is there, and names the room's departed;
a cell with something on it says nothing; the round loop carries it.
"""
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

fake = types.SimpleNamespace(_gone={"GAME_CORNER|8,5": {"GAMECORNER_ROCKET"}},
                             _where=lambda o: "GAME_CORNER|8,5")
obs = {"map": {"id": "GAME_CORNER", "objects": [
    {"name": "POSTER", "x": 9, "y": 4}, {"name": "GAMECORNER_CLERK1", "x": 5, "y": 6}]}}
t = E.Executor._empty_cell_note(fake, obs, 9, 5)
ck("an empty cell is said to be empty", "Nothing this observation lists stands at (9,5) now" in t, t)
ck("...and names who the room has lost", "not in it now: GAMECORNER_ROCKET" in t, t)
ck("a cell with something on it gets nothing", E.Executor._empty_cell_note(fake, obs, 9, 4) == "")
fake2 = types.SimpleNamespace(_gone={}, _where=lambda o: "GAME_CORNER|8,5")
t2 = E.Executor._empty_cell_note(fake2, obs, 9, 5)
ck("with nobody lost, only the cell is said", t2.endswith("no person, sign or item is there."), t2)
src = (ROOT / "planner" / "executor.py").read_text()
ck("the press-by-coordinates failure carries it",
   '_e9 = self._empty_cell_note(obs, step["x"], step["y"])' in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
