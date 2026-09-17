#!/usr/bin/env python3
"""A building directory reaches the page one floor to an entry.

Run 27, 2026-09-16: Celadon's directory read "... 5F: DRUG STORE ROOFTOP
SQUARE: VENDING MACHINES", run together with the sign's line-wrap padding
("SERVICE     COUNTER"), so the roof read as part of 5F (user: "it could
very well just be part of 5F since ROOFTOP SQUARE: breaks the number
pattern"). The sign itself prints each floor on its own line.

Pinned: two or more floor labels split into " / " entries with the padding
squeezed; anything else is untouched; every place a hint is quoted goes
through it. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


SIGN = ("TEXT_CELADONMART1F_DIRECTORY_SIGN: 1F: SERVICE     COUNTER 2F: "
        "TRAINER'S     MARKET 3F: TV GAME SHOP 4F: WISEMAN GIFTS 5F: DRUG STORE "
        "ROOFTOP SQUARE: VENDING MACHINES")
got = E._floor_list_spaced(SIGN)
ck("each floor is its own entry",
   got == "TEXT_CELADONMART1F_DIRECTORY_SIGN: 1F: SERVICE COUNTER / 2F: "
          "TRAINER'S MARKET / 3F: TV GAME SHOP / 4F: WISEMAN GIFTS / 5F: DRUG "
          "STORE / ROOFTOP SQUARE: VENDING MACHINES")
ck("the roof is not part of 5F", "5F: DRUG STORE / ROOFTOP SQUARE:" in got)
ck("a basement label counts", E._floor_list_spaced("B1F: A B2F: B") == "B1F: A / B2F: B")
for plain in ("OAK: Hello there!", "GUARD: 1F: is closed", ""):
    ck(f"text with fewer than two labels is untouched: {plain!r}",
       E._floor_list_spaced(plain) == plain)

src = (ROOT / "planner/executor.py").read_text()
dated = src[src.index("    def _dated(self"):]
dated = dated[:dated.index("\n    def ", 10)]
ck("the dated hint lines use it", dated.count("_floor_list_spaced(line)") == 3)
ck("the building directory line uses it", 'f"on {am}: {_floor_list_spaced(h)}"' in src)
ck("the stuck note's hints use it", "f\"{_floor_list_spaced(_l)}\")" in src)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
