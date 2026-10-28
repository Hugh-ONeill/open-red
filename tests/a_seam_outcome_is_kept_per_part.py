#!/usr/bin/env python3
"""The step's done-so-far sheet keeps a seam crossing per part of the map.

Run 67, 2026-10-28: from the pond east of Seafoam, where every west cross
had failed, the sheet read "west on ROUTE_20 x14 — ok (crossed — now on
CINNABAR_ISLAND ...)": the success was from the part past the island, and
the two parts' rows summed into one with the success shown last.

Pinned: a compass key is bucketed by the whole area; a door or press key
stays bucketed by map. Source-anchored: it runs inside escalate.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
src = (ROOT / "planner" / "executor.py").read_text()
i = src.find("A SEAM CROSSED FROM ONE PART OF A MAP IS NOT")
blk = src[i:i + 900]
ck("the sheet names the rule", i > 0)
ck("...a compass key buckets by the whole area",
   '_mapk = (_area if _dir else _area.split("|")[0], _key)' in blk)
ck("...north, south, east and west, skips folded",
   'str(_key).split("#")[0] in (' in blk and '"north", "south", "east", "west")' in blk)
ck("...and it is the key the sheet sums on",
   '_e = _agg.setdefault(_mapk,' in src[i:i + 1400])
bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n)
sys.exit(1 if bad else 0)
