#!/usr/bin/env python3
"""Where a door leads is known by going through it, or by its sign (audit
PT-11, 2026-09-28). door_dests is the engine's warp table for every door on
a map, and it was read as the run's record: "SAFFRON_CITY door 18,21 ->
SILPH_CO_1F" refused plans, and EVERY WAY OFF THIS FLOOR named where untaken
doors lead. Now a destination counts once the run has walked through the
door, or the building is signed outside (a gym, a Mart, a Pokemon Center).

Synthetic, plus a source check.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


o = {"door_dests": {"SAFFRON_CITY": {"18,21": "SILPH_CO_1F", "34,3": "SAFFRON_GYM",
                                     "9,29": "SAFFRON_POKECENTER", "26,3": "FIGHTING_DOJO"},
                    "CELADON_CITY": {"10,13": "CELADON_MART_1F"},
                    "VIRIDIAN_CITY": {"29,19": "VIRIDIAN_MART"}},
     "explored": {"SAFFRON_CITY|12,0": {"26,3": {"to": "FIGHTING_DOJO|4,11"},
                                        "north": {"to": "ROUTE_5|10,0"}}}}
e = A.earned_door_dests(o)
ck("a door walked through is known", e.get("SAFFRON_CITY", {}).get("26,3") == "FIGHTING_DOJO")
ck("signed buildings are known from outside",
   e["SAFFRON_CITY"].get("34,3") == "SAFFRON_GYM" and e["SAFFRON_CITY"].get("9,29") == "SAFFRON_POKECENTER"
   and e.get("VIRIDIAN_CITY", {}).get("29,19") == "VIRIDIAN_MART")
ck("an unsigned door never used is not", "18,21" not in e["SAFFRON_CITY"])
ck("Celadon's store has no MART sign", "CELADON_CITY" not in e)
ck("an edge is not a door", "north" not in e["SAFFRON_CITY"])
exs = (ROOT / "planner/executor.py").read_text()
ck("the ways-off line no longer folds in the warp table",
   "led.setdefault(str(k), str(d))" not in exs)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
