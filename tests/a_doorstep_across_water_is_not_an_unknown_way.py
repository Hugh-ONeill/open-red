#!/usr/bin/env python3
"""A doorway whose doorstep lies across water says so, even when nobody in
the party knows SURF, and stops reading as a way whose start is unknown.

Run 27, 2026-09-16: Cerulean Cave's mat at (4,11) sits past the pond. The
shim only asked the water question while a party Pokemon knew SURF, so
without it every Cerulean page said "this area is NOT finished ... WHERE THAT
WAY STARTS IS NOT RECORDED — it may be a corner of this floor you have not
walked", "THIS FLOOR IS NOT FINISHED ... How to get there is not known", and
listed "4,11(the way onto it is blocked; nobody)" under every part of the
city as a way never taken. The run hunted a corner of Cerulean to walk to it
(user: "its a little fixated on the entrance at 4,11 to cerulean cave").

Pinned: the shim marks over_water from the same flood asked regardless of
SURF; the executor keeps it per map and drops it from the unreached ways
and the never-taken lists while SURF is unknown; the ledger's rows and
header stop counting it and say the water instead. Once SURF is known,
nothing here applies (by_water takes over). Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
import ledger as L    # noqa: E402

checks = []


def ck(name, cond):
    checks.append((name, bool(cond)))


shim = (ROOT / "harness/shim.lua").read_text()
ck("the shim asks the water question whether or not SURF is known",
   "_wet_memo = warp_reach(G, nil, true)" in shim
   and "swim_step_to(w.x, w.y,\n" in shim and "wet_cells())" in shim
   and "and not party_knows_surf()" in shim)

ck("...or the doorway's own patch: all on screen, joined to nothing, off no "
   "edge, no other doorway, water at its edge",
   "pocket_of = function(G, sx, sy, reach, cap)" in shim
   and "return pk and pk.wet and pk.all_seen" in shim
   and "and not pk.joins and not pk.edge" in shim
   and "and not pk.big and #pk.doors == 0" in shim)
ck("the patch flood ignores who stands on it and stops at doorways",
   "Collision.canMove(map, {}, probe, dn)" in shim
   and "if warps[ck] and not (cur.x == sx and cur.y == sy) then" in shim)
ck("a bush reports what lies past it", "past = _past," in shim)

ex = object.__new__(E.Executor)
ex._door_over_water = {"CERULEAN_CITY": ["4,11"]}
ex._knows_surf = False
ck("a recorded doorstep across water is known per map",
   ex._over_water_doors("CERULEAN_CITY") == {"4,11"}
   and ex._over_water_doors("ROUTE_9") == set())
ex._knows_surf = True
ck("once SURF is known it no longer applies", ex._over_water_doors("CERULEAN_CITY") == set())
ex._knows_surf = False

wet = L.Candidate(key="4,11", kind="door", status="unreachable")
wet.over_water = True
dry = L.Candidate(key="9,9", kind="door", status="unreachable")
ck("an over-water door is not an unreached way",
   L.unreached_ways([wet, dry]) == [dry])

ex.unreached_at = {"CERULEAN_CITY|8,7": ["4,11"]}
ex._frontier_left = lambda r: []
ex._touched_on_map = lambda r: set()
ex._taken_here = lambda r: {}
ex.sightings, ex._gone, ex.region_seen = {}, {}, {}
ex._bush_ways, ex._knows_cut = {}, False
ck("a remote part's row stops counting it as a way no walk reached",
   L._left_parts(ex, "CERULEAN_CITY|8,7") == [])

src = (ROOT / "planner/executor.py").read_text()
led = (ROOT / "planner/ledger.py").read_text()
ck("unreached_at leaves it out",
   "and f\"{w.get('x')},{w.get('y')}\" not in _ow}" in src)
ck("the shut-door record says the water, not 'nobody'",
   "its doorstep is across water; nobody in the " in src)
ck("the never-taken list skips it",
   "not in self._over_water_doors(r.split(\"|\")[0])" in src)
ck("the floor note names it apart from unfinished floor",
   "DOORWAYS ACROSS WATER:" in src and "unseen -= _wet" in src)
ck("the doorways-you-cannot-walk-to line leaves it out",
   "shut = [t for t in shut if t[0] not in _ow_here]" in src)
ck("the door row says the water instead of unseen ground",
   "the ground beside it is reached only " in led)
ck("the other-room line leaves it out", "and not w0.get(\"over_water\")" in led)
ck("the record is saved and loaded",
   '"door_over_water": getattr(self, "_door_over_water", {})' in src
   and 'self._door_over_water = data.get("door_over_water") or {}' in src)

failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
