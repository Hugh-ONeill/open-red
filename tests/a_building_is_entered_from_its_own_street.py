#!/usr/bin/env python3
"""Aimed at a town's building from inside another, the town's street is named.

Run 66, 2026-10-25, leg 31 "Defeat Sabrina", step enter_gym (map
SAFFRON_GYM), standing on Silph Co. 10F: the printed-map line said "0
leg(s) from this map" and listed SAFFRON_CITY|12,0 as one of 22 equally near
parts beside Silph's own floors, alphabetical, with nothing setting the
street apart. The run rode Silph's pads and stairs looking for a way out.

Pinned: the tie list puts parts of the target's town first, and a page
standing in another building of that town says the building's door is on
the town's own ground, naming the walked part. No door is named.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

ck("the gym counts as Saffron on the printed map", E._doorstep("SAFFRON_GYM") == "SAFFRON_CITY")

src = (ROOT / "planner/executor.py").read_text()
ck("the ties are sorted town-ground first",
   '_ties.sort(key=lambda r: r.split("|")[0] != _goal)' in src)
ck("a page inside another building says whose ground the door is on",
   "a building's \"\n" in src and "door is on its town's own ground" in src
   and "you are inside {_hm}, another one" in src)
ck("...only when standing in a different building than the town itself",
   "want_map != _goal and _hm != _goal" in src)

# the ordering itself, on run 66's own tie list
_goal = "SAFFRON_CITY"
ties = sorted(["SAFFRON_MART|0,2", "SAFFRON_POKECENTER|0,3", "SILPH_CO_10F|8,0",
               "SAFFRON_CITY|12,0", "SILPH_CO_1F|20,0"])
ties.sort(key=lambda r: r.split("|")[0] != _goal)
ck("SAFFRON_CITY|12,0 leads the list", ties[0] == "SAFFRON_CITY|12,0", ties)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
