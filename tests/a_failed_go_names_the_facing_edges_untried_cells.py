#!/usr/bin/env python3
"""A failed go names the facing edge's untried cells (run 19, 2026-09-29).

Run 19 answered "go: no walked way from SAFFRON_CITY|12,0 to ROUTE_7|0,2"
twenty times with the same three ops, every crossing from Saffron landing in
Route 7's ledge-bound pocket, while Saffron's west edge had cells never
crossed at (user: "still stuck"; "why is the go command failing though?").
The reply now lists them, from the run's own record. Source checks.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()
checks = [
    ("the facing edge is found from the printed map",
     "_face = next((d for d, t in (MAP_EDGES.get(_hm) or {}).items()" in src),
    ("its untried cells are the reachable ones less the crossed skips",
     '_fresh = [(i, c) for i, c in enumerate(_cells) if i not in _taken]' in src),
    ("each is given with the op that crosses there",
     "'{\"op\":\"cross\",\"dir\":\"' + _face + '\"'" in src),
    ("the note rides on go's failure reply", "_note_b + _note_g + _note_m + _note_c]" in src),
]
failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
