#!/usr/bin/env python3
"""A list of badges is a question, not a shop.

Run 53 (2026-10-12): the Cerulean badge house man asks which badge to hear
about, "1=BOULDERBADGE, 2=CASCADEBADGE, ...". Badges are item ids, so the
list passed the all-items test that lets the Celadon roof machines' price-
less menu count as stock, and CERULEAN_CITY was kept as a shelf of VENDING
MACHINES. Every page said so, and the run went back to Cerulean for a drink
for Saffron's guards across two legs.

Pinned: the badge list is no stock; the roof machines' list still is; a
badge shelf already in memory is dropped on load. Synthetic + real line.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ex = E.Executor.__new__(E.Executor)
BADGES = ("1=BOULDERBADGE, 2=CASCADEBADGE, 3=THUNDERBADGE, 4=RAINBOWBADGE, "
          "5=SOULBADGE, 6=MARSHBADGE, 7=VOLCANOBADGE, 8=EARTHBADGE, 9=CANCEL")
ck("the badge house list is no shop's stock", ex._menu_rows(BADGES) == [], ex._menu_rows(BADGES))
ROOF = "1=FRESH WATER, 2=SODA POP, 3=LEMONADE, 4=CANCEL"
ck("the roof machines' list still is", ex._menu_rows(ROOF) == ["FRESH_WATER", "SODA_POP", "LEMONADE"],
   ex._menu_rows(ROOF))

src = (ROOT / "planner/executor.py").read_text()
load = src[src.index('self._shelf_machine = set(data.get("shelf_machine")'):][:600]
ck("a badge shelf already in memory is dropped on load",
   'endswith("BADGE")' in load and "self._shelf_machine.discard(_bm)" in load)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
