#!/usr/bin/env python3
"""A floor whose every counter has been read without the item says so.

Run 67, 2026-10-26, Celadon Mart 2F, buying FRESH_WATER: CLERK2's shelf was
read (TMs), then CLERK1's (balls and heals), and each reading's "THIS FLOOR HAS
OTHER COUNTERS ... reads that one instead" pointed at the counter read the
round before.

Pinned: the two shim results as the run got them parse to both counters'
names and shelves; the note fires once both are on the record without the
item, and says only that it is not sold on this floor.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

R11 = ("FRESH_WATER is not on CELADONMART2F_CLERK2's shelf, which holds: TM_DOUBLE_TEAM, "
       "TM_REFLECT. THIS FLOOR HAS OTHER COUNTERS and in this game they carry different stock: "
       "CELADONMART2F_CLERK1 — {\"op\":\"buy\"} reads that one instead")
R12 = ("FRESH_WATER is not on CELADONMART2F_CLERK1's shelf, which holds: GREAT_BALL, "
       "SUPER_POTION. THIS FLOOR HAS OTHER COUNTERS and in this game they carry different stock: "
       "CELADONMART2F_CLERK2 — {\"op\":\"buy\"} reads that one instead")
read = {}
fired = []
for det in (R11, R12):
    sh = re.search(r"shelf, which holds: ([A-Z0-9_, ]+)", det)
    c = re.search(r" is not on ([A-Z0-9_]+)'s shelf", det)
    oth = re.search(r"carry different stock: ([A-Z0-9_, ]+?) —", det)
    read[c.group(1)] = [x.strip() for x in sh.group(1).split(",") if x.strip()]
    names = [x.strip() for x in oth.group(1).split(",")] + [c.group(1)]
    fired.append(all(n in read and "FRESH_WATER" not in read[n] for n in names))
ck("the first reading does not say the floor is read", fired[0] is False, fired)
ck("the second does", fired[1] is True, fired)
ck("the executor uses the same three patterns",
   """is not on ([A-Z0-9_]+)'s shelf""" in src
   and "carry different stock: ([A-Z0-9_, ]+?) —" in src)
ck("the note says only that it is not sold on this floor",
   "it is not sold on this \"\n" in src or "it is not sold on this " in src)
ck("...and names no other shop", "Nothing here says where it IS sold." in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
