#!/usr/bin/env python3
"""A deed the missing rung names that is a LATER leg is pulled, not refused.

Stuck at "Reach Viridian City Gym", the rung named "Defeat Blaine for the
Volcano Badge" three times and was told "already on your own list" while
that leg sat two places behind; the chain stopped (run 19, 2026-09-30).

Synthetic: the model's reply is stubbed.
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


d = Path(tempfile.mkdtemp(prefix="pull_"))
(d / "run").mkdir()
(d / "run/obs.json").write_text(json.dumps({"flags": [], "bag": {}}))
here = os.getcwd()
os.chdir(d)
AHEAD = [(48, "Reach Viridian City Gym"), (49, "Defeat Giovanni for the Earth Badge"),
         (50, "Defeat Blaine for the Volcano Badge"), (51, "Reach the Indigo Plateau")]
try:
    for f in ("attempt_yield_text", "new_ground_text"):
        setattr(A, f, (lambda *a, **k: ("", 0)) if f == "attempt_yield_text" else (lambda *a, **k: ""))
    A.done_ledger_text = lambda *a, **k: ""
    A.read_counters_text = lambda *a, **k: ""
    A.inserts_that_did_not_unblock = lambda *a, **k: []
    A._wording_lineage = lambda *a, **k: ""
    reply = {"v": '{"insert": "Defeat Blaine for the Volcano Badge", "why": "Viridian only opens after the Volcano Badge"}'}
    A.chat_json = lambda msgs, model: reply["v"]
    got = A.check_missing("Reach Viridian City Gym", AHEAD, "standing in VIRIDIAN_CITY", "m", behind=[])
    ck("a later leg the rung names comes back as a pull of that leg", got == "PULL:50", got)
    reply["v"] = '{"insert": "Reach Viridian City Gym", "why": "x"}'
    got = A.check_missing("Reach Viridian City Gym", AHEAD, "s", "m", behind=[], tries=1)
    ck("the stuck leg itself is still turned down, not pulled", not str(got).startswith("PULL:"), got)
finally:
    os.chdir(here)

sh = (ROOT / "fresh_discovery.sh").read_text()
ck("the chain carries the pull out with the blocker rung's guard",
   'if [ "${missing#PULL:}" != "$missing" ]; then' in sh
   and 'python planner/pull_leg.py pull "$i" "$_pn"' in sh
   and "run/outline_pullbacks" in sh.split('if [ "${missing#PULL:}"', 1)[1][:1500])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
