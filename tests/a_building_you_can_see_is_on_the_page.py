#!/usr/bin/env python3
"""A building whose roof is on screen reaches the page, and a building
with a word on its front is described the way it is drawn.

Celadon, run 17 (2026-09-15): the step was enter_celadon_gym, the gym's
pale roof and the GYM written twice across its face were on screen, and
the run worked through every other door in the city. Two harness faults,
both on the page rather than in the eyes. The shim keeps a building once
any of its footprint has been seen and filters its doors one by one, on
the reading that making out a doorway is a nearer thing than seeing a
roof; the page then showed buildings only through their doors, so the gym
sat in the observation and never reached the prompt. And the look word
tested the Center's and Mart's roof corners alone, so the gym — same pale
roof, its own corners — came out "house".

The lettering is read from the tiles the engine draws it with. Each word
is a pair of glyph tiles living in exactly one block of the outdoor
tileset: GYM, POKé and MART, the three signs a player reads off a wall
from across the street. Across Kanto they pick out the eight city gyms
plus Saffron's FIGHTING DOJO, which is drawn the same way, every Pokemon
Center, and every Mart. So the words are "a building with GYM written
across its face", never "the gym". What is inside one is not said.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import ledger as L                                        # noqa: E402
import engine_buildings as EB                             # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

# ---- the tiles: what reads as a gym face, and where ------------------------------
B = EB.buildings()
dests = sorted({d for mid in B for b in B[mid] if b.get("face") == "GYM" for _x, _y, d in b["doors"]})
ck("every city gym is drawn with GYM on its face",
   dests == ["CELADON_GYM", "CERULEAN_GYM", "CINNABAR_GYM", "FIGHTING_DOJO", "FUCHSIA_GYM",
             "PEWTER_GYM", "SAFFRON_GYM", "VERMILION_GYM", "VIRIDIAN_GYM"], dests)
ck("...and so is Saffron's FIGHTING DOJO, which is why the words stay at what is drawn",
   "FIGHTING_DOJO" in dests and sum(1 for mid in B for b in B[mid]
                                    if b.get("face") == "GYM" and mid == "SAFFRON_CITY") == 2)
ck("every Center wears POK\u00e9 and every Mart wears MART",
   sorted({d for mid in B for b in B[mid] if b.get("face") == "POK\u00e9" for _x, _y, d in b["doors"]}
          ) == sorted({d for mid in B for b in B[mid] for _x, _y, d in b["doors"] if d.endswith("POKECENTER")})
   and all(any(b.get("face") == "MART" for b in B[mid] if any(d.endswith("_MART") or d == "CELADON_MART_1F"
                                                              for _x, _y, d in b["doors"]))
           for mid in B if any(d.endswith("_MART") for b in B[mid] for _x, _y, d in b["doors"])))
ck("the three words are the engine's own glyph pairs, one block each",
   EB.FACE_WORDS["OVERWORLD"] == {"GYM": {47, 63}, "POK\u00e9": {66, 67}, "MART": {68, 69}})
ck("a signed building reads as flat-roofed, not as a house",
   all(b.get("flat") for mid in B for b in B[mid] if b.get("face")))
ck("the pale public roof is what the flat test reads",
   83 in EB.ROOF_FLAT["OVERWORLD"] and {76, 77} <= EB.ROOF_FLAT["OVERWORLD"])
w = EB.size_word(8, 4, flat=True, face="GYM")
ck("the words say what is written on it, after the size",
   w == "large flat-roofed building with GYM written across its face", w)
ck("...and never that it IS a gym", " the gym" not in w and "gym leader" not in w.lower())
ck("a Center and a Mart are worded the same way, from their own walls",
   EB.size_word(4, 4, True, "MART") == "small flat-roofed building with MART written across its face"
   and "POK\u00e9 written across its face" in EB.size_word(4, 4, True, "POK\u00e9"))
ck("Celadon's department store and a corner Mart both wear MART, and the size still parts them",
   EB.size_word(8, 8, True, "MART").startswith("large")
   and EB.size_word(4, 4, True, "MART").startswith("small"))
ck("an ordinary building keeps its old words",
   EB.size_word(4, 4, flat=True) == "small flat-roofed building"
   and EB.size_word(4, 3) == "small house")
ck("the shim carries the regenerated table",
   'look = "large flat-roofed building with GYM written across its face", doors = { "12,27" }'
   in (ROOT / "harness" / "shim.lua").read_text())

# ---- the page: a building seen, its doorway not made out --------------------------
GYM = {"x0": 6, "y0": 24, "x1": 13, "y1": 27,
       "look": "large flat-roofed building with GYM written across its face", "doors": []}
MART = {"x0": 6, "y0": 6, "x1": 13, "y1": 13, "look": "large flat-roofed building", "doors": ["10,13"]}
OBS = {"mode": "overworld", "map": {"id": "CELADON_CITY", "region": "2,1",
                                    "buildings": [GYM, MART], "objects": [], "warps": [], "seen": {}}}

class Ex:
    visits = {"CELADON_CITY|2,1": 3}
    explored = {}
    hints = {}
    def _where(self, obs): return "CELADON_CITY|2,1"

out = L.render([], Ex(), OBS)
ck("a building whose doorway is not made out is on the page",
   "BUILDINGS IN SIGHT HERE WHOSE DOORWAY YOU HAVE NOT MADE OUT" in out, out[:300])
ck("...with what is written on it", "GYM written across its face" in out)
ck("...and where its walls are", "(6,24) to (13,27)" in out)
ck("...and that walking up to it is what shows the way in",
   "walking up to it is what brings a doorway into view" in out)
ck("...and that the drawing says nothing about the inside",
   "What is inside one is not said by what is drawn on it" in out)
ck("a building whose door HAS been seen is not listed there (its door is a candidate)",
   "large flat-roofed building, its walls" not in out, out)
ck("no buildings in sight: no line",
   "BUILDINGS IN SIGHT" not in L.render([], Ex(), {"mode": "overworld", "map": {"id": "X", "region": "0,0", "buildings": [MART]}}))
ck("...and none at all is no line either",
   "BUILDINGS IN SIGHT" not in L.render([], Ex(), {"mode": "overworld", "map": {"id": "X", "region": "0,0"}}))

# ---- the shim still decides what is visible --------------------------------------
lua = (ROOT / "harness" / "shim.lua").read_text()
ck("a building is kept once any of its footprint has been on screen",
   "A building is kept once ANY of its footprint has been on screen" in lua)
ck("...and its doors one by one", "its doors are kept one" in lua and "if dx and seen(tonumber(dx), tonumber(dy)) then" in lua)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok  " if ok else "FAIL"), n)
    if not ok and dd: print("      ", str(dd)[:400])
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)
