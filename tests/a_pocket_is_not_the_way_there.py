#!/usr/bin/env python3
"""A pocket is not the way there (run 19, 2026-09-29).

Aimed at Celadon from Saffron, the page named ROUTE_7|18,12 "the closest
ground you HAVE walked ... the way there from here is walk west", while the
same page called it fully worked: the ledge-bound strip whose one way out is
back into Saffron (user: "it keeps getting directed to the pocket"). A part
whose only way out leads back here is not offered as the way there; it is
named as what it is. Source checks.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()
checks = [
    ("a pocket is skipped when picking the closest walked ground",
     "if region != here and self._is_pocket(region, here):\n                        _pockets.append(region)\n                        continue" in src),
    ("...and said to lead back here", "leads back here: going there is not a way on." in src),
    ("the old fallbacks still run when nothing was picked",
     "if _pick or _pockets:\n                    pass\n                elif not self._holding_town_map(obs):" in src),
]
failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
