#!/usr/bin/env python3
"""The fired events shown to the done-check fold one place's numbered
trainers into one entry, so the deed's own flag is not cut.

Run 58, 2026-10-18: "Defeat the Team Rocket Boss in the Celadon hideout"
was asked about with ten EVENT_BEAT_ROCKET_HIDEOUT_n_TRAINER_m flags filling
all ten places; EVENT_BEAT_ROCKET_HIDEOUT_GIOVANNI was eleventh and cut. The
model argued from the Silph Scope, was refused, and the run went back into
the beaten hideout looking for the boss. Synthetic: a crafted run/obs.json
in a temporary directory, never the live run.
"""
from __future__ import annotations
import json, os, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

flags = ([f"EVENT_BEAT_ROCKET_HIDEOUT_{f}_TRAINER_{t}" for f, t in
          ((1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (3, 0), (3, 1), (4, 0), (4, 1), (4, 2))]
         + ["EVENT_BEAT_ROCKET_HIDEOUT_GIOVANNI", "EVENT_FOUND_ROCKET_HIDEOUT"]
         + [f"EVENT_BEAT_CELADON_GYM_TRAINER_{t}" for t in range(7)]
         + ["EVENT_BEAT_ERIKA"])
d = Path(tempfile.mkdtemp())
(d / "run").mkdir()
(d / "run/obs.json").write_text(json.dumps({"flags": flags}))
cwd = os.getcwd()
os.chdir(d)
try:
    boss = author._events_bearing("Defeat the Team Rocket Boss in the Celadon hideout")
    erika = author._events_bearing("Defeat Erika for the Rainbow Badge")
finally:
    os.chdir(cwd)
ck("the boss's own flag is shown", "EVENT_BEAT_ROCKET_HIDEOUT_GIOVANNI" in boss, boss)
ck("...and the grunts are one entry with their count",
   "EVENT_BEAT_ROCKET_HIDEOUT_1_TRAINER_N x4" in boss
   and "EVENT_BEAT_ROCKET_HIDEOUT_4_TRAINER_N x3" in boss
   and "EVENT_BEAT_ROCKET_HIDEOUT_1_TRAINER_0" not in boss, boss)
ck("...gym trainers fold the same way",
   "EVENT_BEAT_CELADON_GYM_TRAINER_N x7" in boss, boss)
ck("a lone flag is said by its own name", "EVENT_BEAT_ERIKA" in erika
   and "x1" not in erika, erika)
ck("...and a place with one numbered trainer keeps that trainer's own name",
   "EVENT_BEAT_ROCKET_HIDEOUT_2_TRAINER_0" in boss
   and "EVENT_BEAT_ROCKET_HIDEOUT_2_TRAINER_N" not in boss, boss)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
