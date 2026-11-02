#!/usr/bin/env python3
"""A route hop that lands on a map-less screen settles before it is judged.

Run 70, 2026-11-02, reach_fuchsia_city r3: Route 14's west cross landed on
ROUTE_15 as a trainer's fight was opening; the observation had no map and
was not yet a battle, so _walk_route judged the hop lost (route_walk_lost,
got "None|None", why "crossed — now on ROUTE_15 at (59,6)") and go told the
model "now at None|None" and that the successful cross was what stopped it.

Pinned by source: a landing with no map id that is not a battle is settled
before the battle loop and the landing check, and go never prints a
"None|..." place.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()
checks = []
def ck(n, ok): checks.append((n, bool(ok)))

i = src.index("# A LANDING WITH NO MAP IS A SCREEN BETWEEN TWO THINGS")
blk = src[i:i + 1400]
ck("a map-less, non-battle landing is settled",
   'not (o.get("map") or {}).get("id")' in blk and 'o.get("mode") != "battle"' in blk
   and "o = self.settle() or o" in blk)
ck("...before the battle loop and the landing check",
   blk.index("o = self.settle() or o") < blk.index('while o and o.get("mode") == "battle":'))
j = src.index('"None|None" is a screen with no map read as a place')
ck("go does not print a None| place",
   'arrived.startswith("None|")' in src[j:j + 300])

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
