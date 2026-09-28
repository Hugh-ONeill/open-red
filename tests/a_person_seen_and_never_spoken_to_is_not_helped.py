#!/usr/bin/env python3
"""A person seen and never spoken to has not been helped (2026-09-28).

The leg's own judge (check_done) lacked the refusal the sweep over other
legs had: "Help Bill at Sea Cottage" stopped at the door with Bill on
screen, was judged NOT done, and a minute later "done: the player is
currently inside Bill's house". The ticket leg then set off for Vermilion.

Synthetic.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


d = Path(tempfile.mkdtemp(prefix="bill_"))
ex = d / "explored.json"
ex.write_text(json.dumps({"visits": {"BILLS_HOUSE|0,2": 1},
                          "sightings": {"BILLS_HOUSE|0,2": ["BILLSHOUSE_BILL_POKEMON", "CELL_SEPARATION_SYSTEM"]},
                          "touched": {}}))
called = []
A.brock_probe.chat = lambda *a, **k: called.append(1) or '{"done": true, "why": "inside the house"}'
ck("the leg's own judge refuses before asking the model",
   A.check_done("Help Bill at Sea Cottage", "standing in BILLS_HOUSE", "m", observed=str(ex)) is False
   and not called)
src = (ROOT / "planner/author.py").read_text()
n = src.index("def check_done")
ck("check_done carries the same refusal the sweep has",
   "_un = untouched_named(goal, observed)" in src[n:n + 6000])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
