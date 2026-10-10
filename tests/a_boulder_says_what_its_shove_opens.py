#!/usr/bin/env python3
"""A boulder the party can push says what shoving it opens, the twin of the
bush's "walkable ground past it".

Victory Road 1F's upper part, the barrier shut again behind a party that went
up a floor: the road out was behind VICTORYROAD1F_BOULDER3 at (2,10), and the
page only listed it beside two trainers under "not a claim that any of it is
what stops you". Run 41 never shoved it, nor did run 37 (user, 2026-10-10: "it
just needs to push the boulder out of the way to move past it"). Probed on run
41's save: shoved down once opens 0 cells, twice 2, three times 68 and the
exit's doorstep with them, so the shim (wd.boulder_opens) reports the shove
count that opens the most, and the boulder's row says it. Synthetic here; the
shim half was checked against the save.
"""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
sys.path.insert(0, str(ROOT / "tests"))
import ledger as L  # noqa: E402
import candidates as C  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

def page(opens, strength=True):
    ex = C.make()
    o = C.obs(ex, [], objects=[
        {"name": "VICTORYROAD1F_BOULDER3", "kind": "boulder", "x": 2, "y": 10,
         "reachable": True, "opens": opens},
        {"name": "VICTORYROAD1F_BOULDER2", "kind": "boulder", "x": 14, "y": 2,
         "reachable": True}])
    o["map"]["id"] = "VICTORY_ROAD_1F"
    o["party"] = [{"species": "GRAVELER", "level": 62, "hp": 100, "max_hp": 160,
                   "moves": [{"id": "STRENGTH"}, {"id": "EARTHQUAKE"}]}]
    cands = L.build(ex, o, target="map:ROUTE_23", want_explore=False)
    return cands, L.render(cands, ex, o, target="map:ROUTE_23")

cands, txt = page({"dir": "down", "n": 68, "shoves": 3})
b3 = next(c for c in cands if c.key == "VICTORYROAD1F_BOULDER3")
ck("the shim's opens reaches the candidate", b3.opens == {"dir": "down", "n": 68, "shoves": 3}, b3.opens)
ck("...and its row says what the shove opens",
   "shoved down 3 time(s) from where it sits, it opens 68 cell(s) of ground no walk from here reaches now" in txt, txt[:1500])
ck("a boulder whose shove opens nothing says nothing of the kind",
   txt.count("cell(s) of ground no walk from here reaches now") == 1)
_, txt2 = page(None)
ck("no opens from the shim, no claim", "of ground no walk from here reaches now" not in txt2)

src = (ROOT / "harness/shim.lua").read_text()
ck("the shim computes it on wd, for reachable boulders",
   "wd.boulder_opens = function(G, rock)" in src
   and 'opens = (kind == "boulder" and wd.boulder_opens' in src)
ck("...walking the rock on in a straight line, most ground wins",
   "for k = 1, 8 do" in src and "n > best.n" in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("  ok   " if ok else "  FAIL ") + n + ("" if ok else f"  [{str(d)[:300]}]"))
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)
