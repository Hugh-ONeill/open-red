#!/usr/bin/env python3
"""Floors of a building the leg has searched lead the unseen-ground list.

103 regions had unseen ground, the page named the nearest 30, and
POKEMON_MANSION_B1F (4 spots) sat in "and 73 more floor(s)" on every page
of the Blaine leg, whose attempts had searched the Mansion's other floors
and whose key lay on B1F; the chain stopped (run 19, 2026-09-30).

Source checks plus the family grouping the ranking relies on.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ck("a building's floors are one family",
   len({E.map_family(m) for m in ("POKEMON_MANSION_1F", "POKEMON_MANSION_B1F",
                                    "POKEMON_MANSION_3F")}) == 1)
src = (ROOT / "planner/executor.py").read_text()
blk = src.split("_urows = []", 1)[1][:4500]
ck("the leg's searched maps are read for the ranking",
   '_leg_fams = {map_family(str(m)) for m in' in blk and "_leg_looked" in blk)
ck("a row of a searched building sorts ahead of every other",
   "(0 if map_family(_ur.split(\"|\")[0]) in _leg_fams else 1," in blk)
ck("every reader of the rows unpacks the new first field",
   "for _pri, _d, _n, _m in _shown" in blk and "r[1] >= 99" in blk
   and "for _d, _n, _m in" not in blk)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
