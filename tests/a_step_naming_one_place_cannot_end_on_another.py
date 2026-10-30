#!/usr/bin/env python3
"""validate refuses a step whose words name one place and whose map
condition is another of the same kind.

Run 68, 2026-10-29: "enter_saffron_gym", "Enter the Saffron City Gym",
done_when {"map": "CELADON_GYM"}; the run walked to Celadon's gym and the
step read done. Pinned: that is refused; the same step on SAFFRON_GYM is
not; a step naming both places is not; a condition of another kind
(a city) with a gym in the words is not.
"""
import os, sys, tempfile
from pathlib import Path
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))
def probs(goal, m, sid="enter_saffron_gym"):
    return [p for p in A.validate({"subgoals": [{"id": sid, "goal_text": goal, "done_when": {"map": m}}]})
            if "a different place" in p]
p = probs("Enter the Saffron City Gym", "CELADON_GYM")
ck("Saffron words on CELADON_GYM are refused", p and "SAFFRON_GYM" in p[0], p)
ck("...SAFFRON_GYM is not", probs("Enter the Saffron City Gym", "SAFFRON_GYM") == [])
ck("...words naming both are not", probs("Leave Saffron Gym for the Celadon Gym", "CELADON_GYM", "to_celadon_gym") == [])
ck("...a city condition with a gym in the words is not", probs("Exit the Celadon Gym to the city", "CELADON_CITY", "exit_celadon_gym") == [])
bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
sys.exit(1 if bad else 0)
