#!/usr/bin/env python3
"""The elevator example names a floor this car's panel offers.

Run 70 (2026-11-02): every lift's example read {"floor":"5F"} and "(1F, 5F,
B4F, ROOF)"; the Rocket Hideout's panel is B1F, B2F, B4F, and the run
hunted a hideout 5th floor for the Secret Key across two legs, quoting that
list as the panel's. Pinned: the example uses the panel as read, CANCEL
left out; an unread panel names no floor; the old fixed text is gone.
Synthetic.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import ledger as L  # noqa: E402

checks = []


class Ex:
    lift_floors = {"ROCKET_HIDEOUT_ELEVATOR": ["B1F", "B2F", "B4F", "CANCEL"]}


obs = {"map": {"id": "ROCKET_HIDEOUT_ELEVATOR",
               "lift_floors": ["B1F", "B2F", "B4F", "CANCEL"]}}
w = L._lift_ride_words(Ex(), obs)
checks.append(("inside the car: this panel's floors", '"floor":"B1F"' in w
               and "B1F, B2F, B4F" in w and "CANCEL" not in w and "5F" not in w))
w = L._lift_ride_words(Ex(), {"map": {"id": "GAME_CORNER"}}, "ROCKET_HIDEOUT_ELEVATOR")
checks.append(("from a door row: the car's recorded panel", "B4F" in w and "5F" not in w))
w = L._lift_ride_words(Ex(), {"map": {"id": "SILPH_CO_1F"}}, "SILPH_CO_ELEVATOR")
checks.append(("an unread panel names no floor", "<a floor as the panel spells it>" in w))
src = (ROOT / "planner" / "ledger.py").read_text()
checks.append(("the fixed 5F example is gone",
               'floor\\":\\"5F\\"} from where' not in src and "— 1F, 5F, B4F, ROOF)" not in src))
bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
