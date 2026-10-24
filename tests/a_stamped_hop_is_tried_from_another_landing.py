#!/usr/bin/env python3
"""A hop stamped blocked from one cell of a part is still routed when the
route comes into that part at another recorded cell.

Run 62, 2026-10-24: Mansion 2F|10,1 names both the 1F stairs' landing (5,11)
and a 3F hole's landing; the (6,1) stair to 3F failed from the hole's side
with the statues UNPRESSED and took a blocked_at stamp, and `go` from 1F
then refused 1F -> 2F -> (6,1) -> 3F -> (16,14) -> 1F|12,14 ("not being
replayed because one leg of it would not land"), though from the stairs'
landing the stair walks UNPRESSED (probed on the leg 45 checkpoint).

Pinned: a stamp records the cell the failed try stood on; a route landing
elsewhere in that part routes through it; one landing on that cell, or with
no landing on record, skips it as before; a stamp older than the cell is
tried from a known landing (it takes its cell if it fails again).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

MARK = [6, "b4bfec25", "ebd54e52"]
F1, F2, F3, S1 = ("POKEMON_MANSION_1F|1,1", "POKEMON_MANSION_2F|10,1",
                  "POKEMON_MANSION_3F|1,1", "POKEMON_MANSION_1F|12,14")


def build(blocked_from, land="5,11"):
    ex = E.Executor.__new__(E.Executor)
    stair = {"to": F3, "n": 24, "land": "6,2", "blocked_at": MARK}
    if blocked_from is not None:
        stair["blocked_from"] = blocked_from
    up = {"to": F2, "n": 68}
    if land is not None:
        up["land"] = land
    ex.explored = {F1: {"5,10": up}, F2: {"6,1": stair},
                   F3: {"16,14": {"to": S1, "n": 4, "land": "16,14"}}}
    ex.visits = {F1: 9, F2: 9, F3: 9, S1: 9}
    ex._mark_now = MARK
    ex._bad_seam = set()
    return ex


r = build("19,12")._route(F1, S1)
ck("a route landing elsewhere routes through the stamped hop",
   r and [k for k, _ in r] == ["5,10", "6,1", "16,14"], r)
ck("one landing on the cell the try failed from skips it", build("5,11")._route(F1, S1) is None)
ck("a stamp with no cell (older) is tried once from a known landing",
   build(None)._route(F1, S1) is not None)
ck("no landing on record skips it", build("19,12", land=None)._route(F1, S1) is None)
ck("ignore_blocked is unchanged", build("5,11")._route(F1, S1, ignore_blocked=True))

src = (ROOT / "planner" / "executor.py").read_text()
ck("the stamp records the cell", 'rec["blocked_from"] = f"{_pp.get(\'x\')},{_pp.get(\'y\')}"' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
