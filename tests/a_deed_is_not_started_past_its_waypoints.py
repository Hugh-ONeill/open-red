#!/usr/bin/env python3
"""A plan does not resume past a deed that has not happened.

Run 66, 2026-10-25, leg 31 v3, written from Saffron City:
  enter_silph_co {map SILPH_CO_1F} / reach_giovanni {map SILPH_CO_11F} /
  defeat_giovanni {flag} / exit_silph_co {map SAFFRON_CITY} /
  enter_saffron_gym {map SAFFRON_GYM} / defeat_sabrina {badge}
exit_silph_co held where the party stood, so the resume honored both travel
steps and the Giovanni step began on the street; the model went back to
pressing the gym's Rockets.

Pinned: with the deed undone the plan resumes from its first step; with it
done the old resume stands; a deed before a waypoint that holds earlier is
started from that waypoint.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

SG = [{"id": "enter_silph_co", "done_when": {"map": "SILPH_CO_1F"}},
      {"id": "reach_giovanni", "done_when": {"map": "SILPH_CO_11F"}},
      {"id": "defeat_giovanni", "done_when": {"flag": "EVENT_BEAT_SILPH_CO_GIOVANNI"}},
      {"id": "exit_silph_co", "done_when": {"map": "SAFFRON_CITY"}},
      {"id": "enter_saffron_gym", "done_when": {"map": "SAFFRON_GYM"}},
      {"id": "defeat_sabrina", "done_when": {"badge": "MARSHBADGE"}}]

def obs(m, flags=()):
    return {"mode": "overworld", "map": {"id": m, "region": "12,0"},
            "player": {"x": 25, "y": 12}, "flags": list(flags), "badges": [], "bag": {}}

r, d = E.Executor._resume_before_deed(SG, 4, obs("SAFFRON_CITY"))
ck("an undone deed before the resume sends it back to the first step",
   (r, d) == (0, "defeat_giovanni"), (r, d))
r, d = E.Executor._resume_before_deed(SG, 4, obs("SAFFRON_CITY", ["EVENT_BEAT_SILPH_CO_GIOVANNI"]))
ck("with the deed done the resume stands", (r, d) == (4, None), (r, d))
r, d = E.Executor._resume_before_deed(SG, 4, obs("SILPH_CO_11F"))
ck("standing on the deed's waypoint resumes at the deed", (r, d) == (2, "defeat_giovanni"), (r, d))
r, d = E.Executor._resume_before_deed(SG, 0, obs("PALLET_TOWN"))
ck("a plan resuming at 0 is untouched", (r, d) == (0, None), (r, d))

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
