#!/usr/bin/env python3
"""A catch step's page names the ground the run has never set foot on: the
edges and doors of maps it has walked that it has never taken.

The catch page said "the answer is different ground" and named only ground
already tried: where the party stood, the maps it had fought on, the maps
it had walked through. Run 28's leg 5 (a WATER or GRASS type, CHARMANDER in
hand) searched Route 2 and Viridian Forest four plans running, while the
west edge of VIRIDIAN_CITY, never crossed on the run's own record, went
unmentioned (user, 2026-09-19: "what if rt22 did have a grass pokemon itd
still be getting ignored because it hasnt tried to look there").

Pinned: edges and doors never taken come from the one definition
(_frontier_left); they are named by region, the way the rest of the page
names places; edges and doors are two lists, each nearest first by walked
route; a route that is not known is said; the floor underfoot is included,
first (run 28 stood in Pewter and the line left out Pewter's east edge); no destination is named; nothing untaken, no line;
the catch branch carries the line wherever the party stands. And the page
says once, over every battle of the run, whether the kind it wants has ever
walked out of any grass it has fought on. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


class Ex(E.Executor):
    """A map record and routes, nothing else."""

    def __init__(self, left, hops, here="VIRIDIAN_FOREST|1,0"):
        self.explored = {r: {} for r in left}
        self.frontier = {r: list(v) for r, v in left.items()}
        self._left, self._hops, self._here = left, hops, here

    def _where(self, obs):
        return self._here

    def _frontier_left(self, region):
        return list(self._left.get(region) or [])

    def _route(self, frm, to, avoid=None):
        h = self._hops.get(to)
        return None if h is None else ["x"] * h


LEFT = {"VIRIDIAN_CITY|17,0": ["west", "23,25"],
        "PALLET_TOWN|10,0": ["south"],
        "PEWTER_CITY|4,2": ["east", "13,25", "16,17"],
        "ROUTE_2|3,43": ["north"],
        "VIRIDIAN_FOREST|1,0": ["south", "2,1"],
        "ROUTE_1|10,0": []}
HOPS = {"VIRIDIAN_CITY|17,0": 3, "PALLET_TOWN|10,0": 5,
        "PEWTER_CITY|4,2": 2}
ex = Ex(LEFT, HOPS)
w = ex._never_walked_note({"map": {"id": "VIRIDIAN_FOREST"}})
ck("the line is there, and says what it is",
   w.startswith("GROUND YOU HAVE NEVER SET FOOT ON, on maps you have walked"), w)
ck("an edge never crossed is named by its region",
   "the west edge of VIRIDIAN_CITY|17,0 (never crossed, 3 walked leg(s) away)"
   in w, w)
ck("edges come nearest first",
   w.index("east edge of PEWTER_CITY") < w.index("west edge of VIRIDIAN_CITY")
   < w.index("south edge of PALLET_TOWN"), w)
ck("a route that is not known is said",
   "the north edge of ROUTE_2|3,43 (never crossed, no walked route from here "
   "is known)" in w, w)
ck("doors are their own list, nearest first",
   "Doors never taken: a door at (2,1) in VIRIDIAN_FOREST|1,0 (never taken, "
   "on the ground you stand on); a door at (13,25) in PEWTER_CITY|4,2" in w
   and w.index("Map edges never crossed") < w.index("Doors never taken"), w)
ck("the floor underfoot is included, first, as the ground you stand on",
   "the south edge of VIRIDIAN_FOREST|1,0 (never crossed, on the ground you "
   "stand on)" in w
   and w.index("VIRIDIAN_FOREST|1,0") < w.index("PEWTER_CITY"), w)
ck("a region with nothing left says nothing", "ROUTE_1" not in w)
ck("no destination is named",
   not any(d in w for d in ("ROUTE_22", "ROUTE_21", "ROUTE_3", "->")))
ck("the choice is left to the model", "which is worth the walk is yours to read" in w)
ck("nothing untaken, no line",
   Ex({"ROUTE_1|10,0": []}, {})._never_walked_note({"map": {}}) == "")

many = {f"ROUTE_{i}|0,0": ["north"] for i in range(10)}
wm = Ex(many, {f"ROUTE_{i}|0,0": i + 1 for i in range(10)}
        )._never_walked_note({"map": {}})
ck("a long list is cut, and says how many more", "; and 4 more" in wm, wm)

# ------------------- what every battle of the run has offered, said once
# (user, 2026-09-19: "basically it should see that it cant get a grass
# pokemon anywhere its been before and go somewhere new")
class Met(E.Executor):
    def __init__(self, offered, met_types):
        self._offered, self._met_types = offered, met_types


OFFERED = {"ROUTE_1": {"PIDGEY": 15, "RATTATA": 23},
           "VIRIDIAN_FOREST": {"WEEDLE": 120, "KAKUNA": 80, "PIKACHU": 6}}
TYPES = {"PIDGEY": ["NORMAL", "FLYING"], "RATTATA": ["NORMAL"],
         "WEEDLE": ["BUG", "POISON"], "KAKUNA": ["BUG", "POISON"],
         "PIKACHU": ["ELECTRIC"]}
met = Met(OFFERED, TYPES)
w2 = met._met_types_note("party_type", "WATER|GRASS")
ck("a type met nowhere is said once, over every battle of the run",
   w2 == ("IN EVERY WILD BATTLE THIS RUN HAS HAD — 244, on 2 map(s): "
          "ROUTE_1, VIRIDIAN_FOREST — not one was a GRASS or WATER type. "
          "Every wild ground you have fought on has shown what it holds, "
          "and that was not in it."), w2)
ck("...and one that has been met is named with where and how often",
   met._met_types_note("party_type", "ELECTRIC")
   == "A ELECTRIC type HAS BEEN MET in this run's wild battles: PIKACHU on "
      "VIRIDIAN_FOREST (x6).")
ck("a species goal reads species, not types",
   "not one was a ODDISH" in met._met_types_note("has_species", "ODDISH")
   and "PIKACHU on VIRIDIAN_FOREST (x6)"
   in met._met_types_note("has_species", "PIKACHU"))
ck("a goal that is not about what walks out of the grass says nothing",
   met._met_types_note("party_size", "3") == ""
   and met._met_types_note("map", "PEWTER_CITY") == "")
ck("no battles yet, nothing to say",
   Met({}, {})._met_types_note("party_type", "GRASS") == "")
ck("the types are the ones the battle screen showed",
   met._types_met("PIKACHU") == ["ELECTRIC"])
ck("...and for one met before they were kept, the game's own table",
   Met({}, {})._types_met("ODDISH") == ["GRASS", "POISON"])

src = (ROOT / "planner/executor.py").read_text()
blk = src[src.index("    def _never_walked_note"):
          src.index("    def _wild_elsewhere_fought_note")]
ck("it reads the one definition of an exit never taken",
   "self._frontier_left(r)" in blk)
ck("the catch branch carries both lines, the battles before the ground",
   "_mt = self._met_types_note(kind, dw_val)" in src
   and src.index("_mt = self._met_types_note")
   < src.index("_nw = self._never_walked_note"))
ck("the foe's types are written down as the battle shows them",
   'self._met_types[str(foe["species"])] = [' in src
   and '"met_types": getattr(self, "_met_types", {}),' in src)
ck("the catch branch carries it wherever the party stands",
   "_nw = self._never_walked_note(obs)\n            if _nw:\n"
   "                lines.append(_nw)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
