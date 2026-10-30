#!/usr/bin/env python3
"""A go whose walked chain is far longer than the printed map's road is
said, with both lengths, before a step of it is walked.

Run 68, 2026-10-30: go ROUTE_11 from ROUTE_12_GATE_1F ran a 47-leg chain
through Route 19, Seafoam, Cinnabar, Pallet, Viridian and Mt Moon with the
printed map drawing Route 11 one leg away. Pinned: _printed_legs counts the
map's legs (a gate counts as its road); the guard needs both a long chain
and a short map; "long": true walks it anyway.
"""
import os, sys, tempfile
from pathlib import Path
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
ex = E.Executor.__new__(E.Executor)
ex.explored = {"ROUTE_12_GATE_1F|3,0": {"4,7": {"to": "ROUTE_12|10,21"}}}
ck("next-door roads are one leg", ex._printed_legs("ROUTE_12|10,21", "ROUTE_11|9,0") == 1,
   ex._printed_legs("ROUTE_12|10,21", "ROUTE_11|9,0"))
ck("a gate counts as the road it opens off",
   ex._printed_legs("ROUTE_12_GATE_1F|3,0", "ROUTE_11|9,0") in (0, 1, 2),
   ex._printed_legs("ROUTE_12_GATE_1F|3,0", "ROUTE_11|9,0"))
ck("same road is zero", ex._printed_legs("ROUTE_12|1,1", "ROUTE_12|10,21") == 0)
ck("an unknown interior says nothing", ex._printed_legs("NOWHERE_X|0,0", "ROUTE_11|9,0") is None)
src = (ROOT / "planner" / "executor.py").read_text()
i = src.find("A ROUND-THE-WORLD CHAIN IS SAID BEFORE IT IS WALKED")
blk = src[i:i + 2200]
ck("the guard sits before the walk", i > 0 and src.index("A ROUND-THE-WORLD CHAIN") < src.index('self.log("go_step", subgoal=sg.get("id"), to=region, legs=len(path),'))
ck("...needs a long chain and a short map", "len(path) >= 10 and len(path) > 3 * _pl + 3" in blk)
ck("...and long:true walks it anyway", 'if not step.get("long") and _held:' in blk and '"long":true' in blk)
bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
sys.exit(1 if bad else 0)
