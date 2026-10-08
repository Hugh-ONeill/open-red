#!/usr/bin/env python3
"""An objective naming the Pokedex is not refused as done for want of it in
the bag.

The game's item list numbers the POKEDEX and the elevator's FLOOR_ buttons,
but no bag ever holds them. _item_not_held read every name on that list, so
"Obtain the Pokedex from Professor Oak and reach Pewter City" was refused as
done twice with EVENT_GOT_POKEDEX fired and Pewter walked, and the leg was
re-authored into a walk back south through Viridian Forest (run 39,
2026-10-08). The check still refuses a real item the bag lacks.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A                                        # noqa: E402

checks = []
def ck(n, ok): checks.append((n, bool(ok)))

start = "BADGES: none. BAG: POTION x1. PARTY: IVYSAUR L17."
ck("the Pokedex is not asked of the bag",
   A._item_not_held("Obtain the Pokedex from Professor Oak and reach Pewter City",
                    start) is None)
ck("...nor an elevator floor button",
   A._item_not_held("Ride the elevator to the 5th floor first", start) is None)
ck("a real item the bag lacks is still refused",
   A._item_not_held("Obtain the MOON STONE in Mt. Moon", start) == "MOON_STONE")
ck("...and one the bag holds is not",
   A._item_not_held("Pick up a POTION", start) is None)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)
