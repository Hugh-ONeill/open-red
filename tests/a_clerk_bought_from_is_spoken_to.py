#!/usr/bin/env python3
"""A clerk the party bought from counts as spoken to (run 68, 2026-10-28:
Celadon Mart 5F's clerks stayed "never spoken to" after a buy). Source pin:
a successful buy marks the clerk standing within two cells of the party."""
from pathlib import Path
src = (Path(__file__).resolve().parents[1] / "planner/executor.py").read_text()
i = src.find("A CLERK YOU BOUGHT FROM HAS BEEN SPOKEN TO")
blk = src[i:i + 1800]
checks = [
    ("the rule exists", i > 0),
    ("only a buy that went through", 'if op == "buy" and r.get("ok"):' in blk),
    ("the nearest clerk within two cells is marked", "<= 2:" in blk and "self._mark_touch(_hr, _c[\"name\"], obs)" in blk),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
