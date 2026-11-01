#!/usr/bin/env python3
"""A walk leg a wild encounter cut is walked on from where the fight left
the party, and a route whose walk fell short goes on to the next door when
that door is in reach where the party stands.

Run 69 (2026-10-30, travel_to_vermilion r4): `go` Cerulean -> Vermilion
landed on Route 5, a MANKEY cut the walk to ROUTE_5|1,0 at (10,5), the leg
was filed route_walk_lost_world_cut, and every later go re-planned the same
walk from the part the fight had left the party in and found no path (a
ledge between). The recorded route's next hop, the underground path's door
(17,27), was on reachable ground from (10,5) the whole time. The door hop
has resumed after a fight since Mt Moon; the walk hop gave up.

Pinned: the walk hop resumes while a world cut stopped it and the party is
still getting somewhere, through the same helper the cut-detector uses; a
cut walk whose next hop is a reachable door on this map continues to it
instead of abandoning the route; a door not in reach is left alone."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


src = (ROOT / "planner/executor.py").read_text()
i = src.index("# A WALK A WILD CUT IS WALKED ON FROM WHERE IT STOPPED.")
blk = src[i:i + 2600]
ck("the walk hop resumes after a world cut",
   'self._walk_cut_by_the_world(str(_wdet or ""))' in blk
   and 'self._send_safe("walk_to", x=_ax, y=_ay)' in blk)
ck("...only while the party still gets somewhere, a few times at most",
   "if self._pos(o) == _p0:\n                            break" in blk and "_resumes < 4" in blk)
ck("...and each resume is journaled with where it went",
   'self.log("route_walk_resumed"' in blk and "landed=bool(self._same_area(self._where(o), nxt))" in blk)
ck("...inside the on-foot walk, before the ride fallback",
   src.index("# A WALK A WILD CUT IS WALKED ON") < src.index("_rode_walk = _ride_first"))
j = src.index("# ...AND THE NEXT DOOR MAY BE RIGHT HERE.")
blk2 = src[j:j + 2200]
ck("after a world cut, the next hop is looked at",
   "_nk = (str(path[_hop_i + 1][0])" in blk2 and "_is_door_key(_nk)" in blk2)
ck("...only a door on the map the party stands on, in the overworld",
   'str(_om.get("id") or "") == _mid' in blk2 and '(o or {}).get("mode") == "overworld"' in blk2)
ck("...and only one the observation says is reachable",
   'and w.get("reachable")' in blk2 and 'for w in (_om.get("warps") or [])' in blk2)
ck("...then the route goes on to it", 'self.log("route_walk_short_door_in_reach"' in blk2
   and blk2.index('self.log("route_walk_short_door_in_reach"') < blk2.index("continue"))
ck("a cut with no such door still ends the route as before",
   "return o\n" in blk2[blk2.index("continue"):])
ck("the cut detector reads the shim's interruption words",
   E.Executor._walk_cut_by_the_world("interrupted (battle or script)"))
ck("the shim marks each warp's reach in the observation",
   "reachable = reach[w.x .. \",\" .. w.y] and true" in (ROOT / "harness/shim.lua").read_text())

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
