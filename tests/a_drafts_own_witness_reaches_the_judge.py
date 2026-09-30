#!/usr/bin/env python3
"""A draft's own already-set witness reaches the done judge before another
plan is run for the same deed.

The drink leg's first draft ended on EVENT_GAVE_GUARDS_DRINK, which had
already fired; it was refused, the next draft ended on lacks_item
FRESH_WATER, and the run spent three waters at the gate to meet it (run 19,
2026-09-29). The refused flag is the model naming the deed's record.

Synthetic.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


d = Path(tempfile.mkdtemp(prefix="witness_"))
(d / "run").mkdir()
(d / "run/obs.json").write_text(json.dumps({"flags": ["EVENT_GAVE_GUARDS_DRINK"]}))
(d / "run/executor_log.jsonl").write_text(json.dumps(
    {"kind": "flag_fired", "flag": "EVENT_GAVE_GUARDS_DRINK", "t": 1}) + "\n")
here = os.getcwd()
os.chdir(d)
try:
    A.OWN_WITNESS.clear()
    G = "Give FRESH WATER to the guard on Route 6"
    plan = {"goal": G, "subgoals": [{"id": "give", "goal_text": "Give the water",
                                     "done_when": {"flag": "EVENT_GAVE_GUARDS_DRINK"}}]}
    probs = A.validate(plan)
    ck("the draft is still refused", any("ALREADY FIRED" in p for p in probs))
    ck("...and its flag is kept as the model's own witness",
       A.OWN_WITNESS == {"EVENT_GAVE_GUARDS_DRINK"}, A.OWN_WITNESS)
    A._record_witness(G)
    t = A.witness_text(G)
    ck("the judges are shown it",
       "YOUR OWN PLANS FOR THIS OBJECTIVE NAMED EVENT_GAVE_GUARDS_DRINK" in t, t)
    ck("...and a doubt note on the leg does not lose it",
       A.witness_text(G + " (a doubt you recorded when outlining: for: x)") == t)
    (d / "run/obs.json").write_text(json.dumps({"flags": []}))
    ck("a witness the game no longer has is not shown", A.witness_text(G) == "")
finally:
    os.chdir(here)
src = (ROOT / "planner/author.py").read_text()
ck("check_done and the already-done rung both carry it",
   src.count("witness_text(") >= 3)
ck("the author asks once with it before any other plan runs",
   "if OWN_WITNESS:\n        _record_witness(args.goal)" in src and "sys.exit(6)" in src)
ck("a fresh chain forgets it", "run/leg_witness.json" in (ROOT / "fresh_discovery.sh").read_text())

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
