#!/usr/bin/env python3
"""explore with until=map_change takes the way its arrival sweep uncovers, in
the same round, instead of handing the round back on the first sighting.

Run of record 13 (2026-09-27), leg "Reach Vermilion City" with the S.S. Ticket
in hand: {"op":"explore","until":"map_change"} walked into Cerulean's robbed
house, swept it, and the sweep stopped at "came into view: a doorway at
(3,0)" — the back door, the one way south out of the city. The round ended
there; the next round the model left "with no reason to stay here", and the
chain later stopped at that leg believing the CUT tree was the only way.

Checked on the game from run 13's last save with the house unseen: the
arrival sweep uncovered (3,0) and the same step went on "taking door (3,0)
... which the sweep uncovered — you asked to go until the map changes" into
the city's southern part.

Pinned: the continuation fires only for until=map_change, only when the sweep
left the party on the same map, takes only an untried reachable way, and says
why in its own words. Source checks.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()
checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


i = src.index('"sweeping the ground there never on screen")')
blk = src[i:i + 3200]
ck("the arrival sweep runs first, as before",
   "self._note_swept(region)" in blk and "self._count_dry_walk(region, t2)" in blk)
ck("the continuation is only for until=map_change",
   'if (not ok and _params.get("until") == "map_change"' in blk)
ck("...only while the sweep left the party on the same map",
   '((cur2.get("map") or {}).get("id")\n'
   '                         == ((cur or {}).get("map") or {}).get("id"))' in blk)
ck("...takes only an untried way that can be walked to",
   'c.status == "untried"\n                       and c.kind in ("door", "seam") and c.reachable' in blk)
ck("...and says why in its own words",
   "which the sweep uncovered — you \"\n" in blk
   and "asked to go until the map changes" in blk)
ck("otherwise the round ends as it did", "return ok, tr + t2, cl" in blk)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
