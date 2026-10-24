#!/usr/bin/env python3
"""A thing pressed from another part of the floor, out of reach from this
one, is not "the way in is what is missing".

Run 62, 2026-10-24: Mansion 2F's book at (3,22) was read from parts 10,1 and
6,1; from part 24,9 it stood behind the statue walls, the row was
"unreachable" (that branch is tested before "pressed"), and explore's line
said "Everything you can REACH here is done (BOOK_POKEMON_MANSION_2F_3_22
sits where no walk from here goes — the way in is what is missing, not the
thing)". The run flipped the statues for it, plan after plan, while the
basement held the Secret Key.

Pinned: such a thing keeps its unreachable row but is not on the stuck list;
one never pressed still is.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
sys.path.insert(0, str(ROOT / "tests"))
import candidates as C  # noqa: E402
import ledger as L  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

M = "POKEMON_MANSION_2F"
BOOK = "BOOK_POKEMON_MANSION_2F_3_22"


def stuck(pressed):
    ex = C.make()
    ex._where = lambda o: M + "|24,9"
    ex._tried_objs = {M + "|10,1": {BOOK}} if pressed else {}
    o = C.obs(ex, [], objects=[{"name": BOOK, "kind": "npc", "x": 3, "y": 22,
                                "reachable": False}], region="24,9")
    o["map"]["id"] = M
    cands = L.build(ex, o, "")
    row = next((c for c in cands if c.key == BOOK), None)
    return row, [c.key for c in L._stuck_things(cands)]


row, st = stuck(True)
ck("a thing pressed from another part keeps its unreachable row",
   row is not None and row.status == "unreachable", row and row.status)
ck("...but is not on the stuck list", BOOK not in st, st)
row2, st2 = stuck(False)
ck("one never pressed still is", BOOK in st2, st2)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
