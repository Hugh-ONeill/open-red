#!/usr/bin/env python3
"""A leg still unconfirmed after two plans is asked about before it is pushed.

"Give FRESH WATER to the guard on Route 6" met its plans' conditions twice,
the judge would not confirm it, and it was pushed 30->32 without the
reword/done-under-another-name/VOID rung ever being asked (run 19,
2026-09-29).

Source checks (the chain script).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


sh = (ROOT / "fresh_discovery.sh").read_text()
i = sh.index("printf '%s\\n' \"$leg\" >> run/leg_unconfirmed")
blk = sh[i:i + 1500]
j_ask = blk.find('if wording_rung "done"; then continue; fi')
j_push = blk.find("python planner/push_leg.py")
ck("the wording rung is asked on that path", j_ask >= 0)
ck("...before the push", 0 <= j_ask < j_push, (j_ask, j_push))
ck("the rung it calls answers reword, done-under-another-name and VOID",
   "--check-wording" in sh and "if [ $wrc = 4 ]; then" in sh and "if [ $wrc = 5 ]; then" in sh)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
