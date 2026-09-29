#!/usr/bin/env python3
"""The events line names the deed's own event, not every win on the road.

"Give FRESH WATER to the guard on Route 6" matched on ROUTE, so the ten
slots were Route 10 and 11 trainer wins and EVENT_GAVE_GUARDS_DRINK, fired
legs earlier, never reached the judge; GUARD never met GUARDS either. The
leg was judged "no record of it being given" and pushed (run 19,
2026-09-29).

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


d = Path(tempfile.mkdtemp(prefix="bearing_"))
(d / "run").mkdir()
flags = ([f"EVENT_BEAT_ROUTE_10_TRAINER_{i}" for i in range(6)]
         + [f"EVENT_BEAT_ROUTE_11_TRAINER_{i}" for i in range(6)]
         + ["EVENT_GAVE_GUARDS_DRINK", "EVENT_BEAT_ROUTE16_SNORLAX",
            "EVENT_BEAT_CINNABAR_GYM_TRAINER_0"])
(d / "run/obs.json").write_text(json.dumps({"flags": flags}))
A._announced = lambda fl: list(fl)
here = os.getcwd()
os.chdir(d)
try:
    got = A._events_bearing("Give FRESH WATER to the guard on Route 6")
    ck("the guards' drink is named", "EVENT_GAVE_GUARDS_DRINK" in got, got)
    ck("...and no trainer on some road is, on ROUTE alone", "TRAINER" not in got, got)
    got = A._events_bearing("Wake the Snorlax sleeping on Route 12")
    ck("the other Snorlax still reaches the place guard",
       "EVENT_BEAT_ROUTE16_SNORLAX" in got, got)
    got = A._events_bearing("Defeat the trainers in the Cinnabar Island gym")
    ck("the town's own trainers rank ahead of the road's",
       got.split(": ", 1)[1].startswith("EVENT_BEAT_CINNABAR_GYM_TRAINER_0"), got)
    ck("a road alone brings nothing", A._events_bearing("Walk Route 10") == "")
finally:
    os.chdir(here)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
