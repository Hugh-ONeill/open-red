#!/usr/bin/env python3
"""A sentence names a map only when the map's words stand together in it.

Run 72, 2026-11-03: the VOID rung refused "The run has already traversed
Mt. Moon, obtained the Helix Fossil from B2F, and reached Cerulean City,
which constitutes clearing the cave" as resting on CERULEAN_CAVE_1F, ground
never stood in: maps_named read the sentence as a set of words, and
"Cerulean ... cave" was enough.

Pinned: run 72's reason names Cerulean City and Mt Moon, not Cerulean Cave;
words written together still name their map, possessives included (Diglett's
Cave, Mr. Fuji's house); a map named outright still matches. Synthetic.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

IDS = ["CERULEAN_CAVE_1F", "CERULEAN_CITY", "DIGLETTS_CAVE", "MR_FUJIS_HOUSE",
       "SAFARI_ZONE_EAST", "MT_MOON_1F", "CINNABAR_ISLAND", "CINNABAR_GYM"]
RUN72 = ("The run has already traversed Mt. Moon, obtained the Helix Fossil "
         "from B2F, and reached Cerulean City, which constitutes clearing the cave.")

got = A.maps_named(RUN72, IDS)
ck("run 72's reason does not name Cerulean Cave", "CERULEAN_CAVE_1F" not in got, got)
ck("...and names the places it does", {"CERULEAN_CITY", "MT_MOON_1F"} <= set(got), got)
ck("Cerulean Cave written together is named",
   A.maps_named("Explore the Cerulean Cave", IDS) == ["CERULEAN_CAVE_1F"])
ck("a possessive still names its map",
   A.maps_named("Go through Diglett's Cave", IDS) == ["DIGLETTS_CAVE"])
ck("...and a possessive of a person",
   A.maps_named("Retrieve the Poke Flute from Mr. Fuji's house", IDS) == ["MR_FUJIS_HOUSE"])
ck("a two-word place matches its family",
   A.maps_named("Traverse the Safari Zone", IDS) == ["SAFARI_ZONE_EAST"])
ck("an island is not its gym",
   A.maps_named("Reach Cinnabar Island", IDS) == ["CINNABAR_ISLAND"])

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
