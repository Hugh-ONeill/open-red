#!/usr/bin/env python3
"""A ball a full bag refused keeps its own name and tile on the page.

Run 67, 2026-10-28, Pokemon Mansion B1F: two presses in one round, (5,13) and
(5,4), both "No more room for items!"; the first one's words were filed as
"someone", so the refused-things line read "someone in POKEMON_MANSION_B1F
said ..." with no tile, for the ball that held the Secret Key.

Pinned: a recorded refusal is listed as "a ball at (5,13) in
POKEMON_MANSION_B1F"; a ball since picked up (gone) drops off; the record is
saved and loaded; the line still waits for bag room.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ex = E.Executor.__new__(E.Executor)
ex.hints, ex.visits, ex._gone, ex._item_from = {}, {}, {}, {}
ex._where = lambda o: "POKEMON_MANSION_3F|5,8"
ex._route = lambda a, b: None
ex._refused_balls = {"ITEM_POKEMON_MANSION_B1F_5_13": "POKEMON_MANSION_B1F"}
room = {"bag": {f"K{i}": 1 for i in range(18)}}
t = ex._refused_gifts_line(room)
ck("the ball is named by its tile", "a ball at (5,13) in POKEMON_MANSION_B1F" in t, t)
ck("the line waits for room", ex._refused_gifts_line({"bag": {f"K{i}": 1 for i in range(20)}}) == "")
ex._gone = {"POKEMON_MANSION_B1F|20,1": {"ITEM_POKEMON_MANSION_B1F_5_13"}}
ck("a ball picked up since drops off", "(5,13)" not in ex._refused_gifts_line(room))
src = (ROOT / "planner/executor.py").read_text()
ck("the record is saved and loaded",
   '"refused_balls": getattr(self, "_refused_balls", None) or {},' in src
   and 'self._refused_balls = data.get("refused_balls") or {}' in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
