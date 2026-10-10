#!/usr/bin/env python3
"""A struck use_warp is lifted only when the WALK can reach the doorway, not
when the engine's look past unseen ground says it can.

Seafoam B3F, party surfing at (14,2): the doorway (20,17) read `reachable`
(warp_reach asks the engine about every cell, seen or not) while every
use_warp and walk_to(surf=true) to it said "no path", and the strike was
lifted five times on the first answer (run 41, 2026-10-09). The shim now adds
`seen_reachable`, the walk's own path search (bfs_dir); probed on run 41's
save it reads False there and True for Victory Road 1F's walkable ladder. The
water advice also stops telling a walk that already rode the water to "take
surf=true".
"""
import sys
import types
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E                                      # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

o = types.SimpleNamespace(_dead_why={}, _BLOCKED_WHY=E.Executor._BLOCKED_WHY)
o._strike_reason_lifted = types.MethodType(E.Executor._strike_reason_lifted, o)
sig = ("t", "SEAFOAM_ISLANDS_B3F|14,0", "use_warp", (20, 17), None, None, None, None, None)
o._dead_why[sig] = "couldn't reach the warp tile (no path — ...)"
def obs(**w):
    return {"map": {"warps": [dict(x=20, y=17, **w)]}}
step = {"x": 20, "y": 17}
ck("engine says reachable, the walk does not: no lift",
   o._strike_reason_lifted(sig, "use_warp", step, obs(reachable=True, seen_reachable=False)) == "")
ck("the walk reaches it: lifted",
   o._strike_reason_lifted(sig, "use_warp", step, obs(reachable=True, seen_reachable=True)) != "")
ck("an older shim without the flag falls back to reachable",
   o._strike_reason_lifted(sig, "use_warp", step, obs(reachable=True)) != "")

src = (ROOT / "harness/shim.lua").read_text()
ck("the shim adds seen_reachable from the walk's own search",
   "seen_reachable = (reach[w.x" in src and "wd.walk_dir = bfs_dir" in src
   and "local dir = wd.walk_dir and wd.walk_dir(G, x, y)" in src)
ck("...memoized per observation", "wd.sr_dist = nil" in src)
ck("the water advice knows the walk already rode it",
   "this walk already rode the water (surf was on)" in src
   and "wd.walk_surf = c.surf and true or nil" in src)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("  ok   " if ok else "  FAIL ") + n)
print(("FAIL %d/%d" % (len(bad), len(checks))) if bad else "ok %d checks" % len(checks))
sys.exit(1 if bad else 0)
