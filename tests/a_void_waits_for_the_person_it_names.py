#!/usr/bin/env python3
"""A leg is not VOIDed while the person it names stands there unspoken-to.

Run 23 (2026-10-02): "Visit Bill in his house on Route 25" met Bill and ran
the Cell Separator; check-done refused it twice because BILLSHOUSE_BILL1, the
restored Bill who hands over the S.S. Ticket, had never been spoken to; then
the wording rung VOIDed it ("the run has already met Bill and used the cell
separator") and the run walked out one press from the ticket. Run of record
14 lost it the same way.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


td = Path(tempfile.mkdtemp())
obs = td / "explored.json"
obs.write_text(json.dumps({
    "sightings": {"BILLS_HOUSE|0,2": ["BILLSHOUSE_BILL1", "CELL_SEPARATION_SYSTEM"]},
    "touched": {"BILLS_HOUSE|0,2": ["CELL_SEPARATION_SYSTEM", "POKEMON_BILLS_HOUSE_6_5"]},
    "visits": {"BILLS_HOUSE|0,2": 2}}))
why = ("The run has already met Bill and used the cell separator to resolve his "
       "situation (EVENT_MET_BILL, EVENT_USED_CELL_SEPARATOR_ON_BILL).")
r = A.void_refused_why("Visit Bill in his house on Route 25", obs, why=why)
ck("a VOID is refused while the person the leg names stands unspoken-to",
   "BILLSHOUSE_BILL1" in r and "never spoken to" in r, r)
ck("...even when its reason cites events that really fired",
   r.startswith("this objective names"))
obs.write_text(json.dumps({
    "sightings": {"BILLS_HOUSE|0,2": ["BILLSHOUSE_BILL1"]},
    "touched": {"BILLS_HOUSE|0,2": ["BILLSHOUSE_BILL1"]},
    "visits": {"BILLS_HOUSE|0,2": 2}}))
ck("once spoken to, the VOID is judged as before",
   "never spoken to" not in A.void_refused_why("Visit Bill in his house on Route 25", obs, why=why))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
