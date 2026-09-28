"""Roads a printed-map place sits in the middle of, in the game's order.

User ruling 2026-09-28 (audit PT-17b): the booklet's World Map is pamphlet
tier, and it draws Mt. Moon, Rock Tunnel, Victory Road and Seafoam BETWEEN
two roads. The game puts each one INSIDE the second road, cutting it in two:
Route 9 reaches Route 10's north part, not Rock Tunnel. The in-game Town Map
shows the place partway along the road, so saying the order in the game's
form is the printed map read correctly (user: "state it, the game's
order"). This used to be left for the model to infer from a door id listed
under one road (the 2026-08-17 call); the run then hunted Route 10 from
Route 11 while ignoring Route 9.

The order of travel only. Nothing about what is inside, or how long each
part is, and never "the only way": Route 2's east side has its own way
round once a tree is cut.
"""
from __future__ import annotations

# road -> (place as the printed map names it, from, near part, far part, to)
SPLITS = {
    "ROUTE_2": ("VIRIDIAN FOREST", "VIRIDIAN_CITY", "south", "north", "PEWTER_CITY"),
    "ROUTE_4": ("MT.MOON", "ROUTE_3", "west", "east", "CERULEAN_CITY"),
    "ROUTE_10": ("ROCK TUNNEL", "ROUTE_9", "north", "south", "LAVENDER_TOWN"),
    "ROUTE_20": ("SEAFOAM ISLANDS", "ROUTE_19", "east", "west", "CINNABAR_ISLAND"),
    "ROUTE_23": ("VICTORY ROAD", "ROUTE_22", "south", "north", "INDIGO_PLATEAU"),
}


def split_roads_text() -> str:
    rows = "\n".join(
        f"  {frm} -> {road}'s {near} part -> {place} -> {road}'s {far} part -> {to}"
        for road, (place, frm, near, far, to) in sorted(SPLITS.items()))
    return ("\n\nROADS A PLACE ON THE PRINTED MAP SITS IN THE MIDDLE OF, in the "
            "order you travel them (either way round). Each place stands "
            "between its road's two parts.\n" + rows)
