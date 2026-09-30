#!/usr/bin/env python3
"""The state text counts the badges and names the leaders still to beat.

Holding six, the run wrote "I have all 8 badges" at Viridian's locked gym
with Blaine unbeaten (run 19, 2026-09-30). The eight badges and their
leaders are the booklet's. The missing ones are named by leader, so the
done guards, which search this text for badge names, still read them as
not held.

Synthetic.
"""
from __future__ import annotations

import importlib.util
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


SIX = ["BOULDERBADGE", "CASCADEBADGE", "MARSHBADGE", "RAINBOWBADGE", "SOULBADGE", "THUNDERBADGE"]
d = Path(tempfile.mkdtemp(prefix="badges_"))
(d / "run").mkdir()
(d / "run/obs.json").write_text(json.dumps({"map": {"id": "VIRIDIAN_CITY"}, "party": [{"species": "GRAVELER", "level": 58, "hp": 150, "max_hp": 150, "moves": []}],
                                            "badges": SIX, "bag": {}, "money": 100}))
here = os.getcwd()
os.chdir(d)
try:
    import subprocess
    st = subprocess.run([sys.executable, str(ROOT / "planner/state_text.py")],
                        capture_output=True, text=True,
                        env=dict(os.environ, RED_BRIDGE_DIR=str(d / "run"))).stdout
finally:
    os.chdir(here)
ck("six held says 6 of the 8", "6 of the 8 badges" in st, st[:300])
ck("...and names who is left by leader",
   "not yet won: Blaine's (Cinnabar Island gym), Giovanni's (Viridian City gym)" in st, st[:300])
ck("the Volcano Badge still reads as not held to the done guard",
   A._badge_not_earned("Defeat Blaine for the Volcano Badge", st) == "VOLCANOBADGE")
ck("...and the Earth Badge", A._badge_not_earned("Defeat Giovanni for the Earth Badge", st) == "EARTHBADGE")
ck("a held one still reads as held", A._badge_not_earned("Defeat Koga for the Soul Badge", st) is None)

spec = importlib.util.spec_from_file_location("st_mod_src", ROOT / "planner/state_text.py")
src = (ROOT / "planner/state_text.py").read_text()
ck("all eight is said as all of them", "all of them" in src and "no badges (8 to win)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
