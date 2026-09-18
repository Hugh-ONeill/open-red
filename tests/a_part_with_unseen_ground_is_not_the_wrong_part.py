#!/usr/bin/env python3
"""The backtrack's relocate mode stands down while the part the party is on
still has ground never on screen.

Run 27, 2026-09-17, Route 12 after the flute: cross_route_12_gate (map
ROUTE_13) ran out of rounds, and the backtrack re-opened cross_route_11_gate
(map ROUTE_12, still true) in relocate mode — "you ALREADY satisfy DONE_WHEN
but you are in the WRONG PLACE ... get to a DIFFERENT place" — because
Route 12 had another walked part. The run went north to |8,0 and back
through the gate, three rounds, while the strip it stood on had four
unseen-ground spots, two of them south toward Route 13 (user: "now its
pingponging instead of exploring south").

Pinned: with the shim's frontier for the standing part above zero, the
relocate is skipped, the journal says why, and the plan ends for a rewrite
from where the party stands; the relocate for a finished part is
untouched. Source-anchored: the scan lives inside the plan runner.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


src = (ROOT / "planner/executor.py").read_text()
i = src.index("for back in range(idx - 1, max(-1, idx - 5), -1):")
loop = src[i:i + 7000]
ck("the relocate asks the shim's frontier for the part the party stands on",
   '.get("seen")\n                                   or {}).get("frontier_n") or 0)' in loop)
ck("...and stands down while it is above zero, ending the scan",
   "if _fn > 0:" in loop and "cand = None\n                            break" in loop.split("if _fn > 0:", 1)[1][:900])
ck("...saying why in the journal",
   "it is not the wrong part " in loop and '"backtrack_skipped"' in loop.split("if _fn > 0:", 1)[1][:600])
ck("the relocate for a finished part is untouched",
   "cand, holds, elsewhere = c, True, elw" in loop
   and loop.index("if _fn > 0:") < loop.index("cand, holds, elsewhere = c, True, elw"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
