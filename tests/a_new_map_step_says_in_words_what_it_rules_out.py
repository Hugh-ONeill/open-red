#!/usr/bin/env python3
"""A new_map_from step says in words what holds it, and when its own words
name a map it rules out.

Run 66, 2026-10-25, leg 1: "Enter Professor Oak's lab" over {"new_map_from":
"PALLET_TOWN", "not_maps": ["BLUES_HOUSE", "OAKS_LAB", "REDS_HOUSE_1F"]},
frozen as the step began, after the step before it (talk to Oak, carried
past) had searched the lab. The page showed only the JSON, and the run walked
out of the lab and back in "to trigger the new_map_from condition", rounds
running, with Route 1 (where Oak waits) the one road left.

Pinned: the condition is said in words with the maps it rules out; the words
naming a ruled-out map are said to; nothing names the map that is left.
"""
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

fake = types.SimpleNamespace(_condition_place_words=lambda g, d, o: "")
DW = {"new_map_from": "PALLET_TOWN", "not_maps": ["BLUES_HOUSE", "OAKS_LAB", "REDS_HOUSE_1F"]}
t = E.Executor._words_vs_condition(fake, "Enter Professor Oak's lab", DW)
ck("the condition is said in words, with what it rules out",
   "entered from PALLET_TOWN" in t and "any map but BLUES_HOUSE, OAKS_LAB, REDS_HOUSE_1F" in t, t)
ck("...and that the step's words name a map it rules out",
   "This step's words name OAKS_LAB, which the condition rules out" in t, t)
ck("...without naming the map that is left", "ROUTE_1" not in t and "ROUTE_21" not in t, t)
t2 = E.Executor._words_vs_condition(fake, "Go into the hideout under the Game Corner",
                                    {"new_map_from": "GAME_CORNER", "not_maps": ["CELADON_CITY"]})
ck("words naming no ruled-out map get only the plain condition",
   "entered from GAME_CORNER" in t2 and "words name" not in t2, t2)
ck("an unfrozen new_map_from says nothing new",
   "THE CONDITION IS THE STEP: it holds the moment" not in
   E.Executor._words_vs_condition(fake, "x", {"new_map_from": "PALLET_TOWN"}))

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
