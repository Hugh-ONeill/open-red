#!/usr/bin/env python3
"""Among events sharing as many of an objective's words, a named deed is
shown before a group of numbered trainers, so the cap of ten keeps it.

Run 62, 2026-10-24: asked whether "Clear the Team Rocket takeover of Silph
Co. in Saffron City" was done, the judge's list went alphabetically and ten
places went to hideout, Saffron Gym and Silph floor grunts; the deed itself,
EVENT_BEAT_SILPH_CO_GIOVANNI (with the Master Ball in the bag), was cut. The
judge argued from the Silph Scope, was refused, and the beaten building went
back in front of Giovanni's gym.

Pinned: with twelve grunt rooms sharing one word and one named deed sharing
the same word, the named deed is in the list; grunt rooms are still listed,
counted.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

flags = [f"EVENT_BEAT_SILPH_CO_{n}F_TRAINER_{i}" for n in range(2, 12) for i in (0, 1)]
flags += [f"EVENT_BEAT_ROCKET_HIDEOUT_{n}_TRAINER_0" for n in (1, 2, 3, 4)]
flags += ["EVENT_BEAT_SILPH_CO_GIOVANNI", "EVENT_GOT_MASTER_BALL"]
tmp = tempfile.mkdtemp()
os.chdir(tmp)
Path("run").mkdir()
Path("run/obs.json").write_text(json.dumps({"flags": flags}))
t = A._events_bearing("Clear the Team Rocket takeover of Silph Co. in Saffron City")
ck("the named deed survives the cap", "EVENT_BEAT_SILPH_CO_GIOVANNI" in t, t)
ck("...and grunt rooms are still said, counted", "(numbered trainers beaten)" in t, t)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
