#!/usr/bin/env python3
"""A ladder that fires on the step onto it, mid-walk, is the door use_warp
was asked for, not "a DIFFERENT door".

Run 37, 2026-10-06: in Rock Tunnel every use_warp to a ladder reported
"couldn't reach the door at (27,3) — unreachable — and on the way the
party was carried through a DIFFERENT door (door unknown)". The step log
of the same call, replayed on a copy of the live save, reads B1F (27,4)
(27,3) then 1F (5,3): the ladder asked for, fired on arrival while the map
was still loading. The run read the tunnel's ladders as failures and went
1F, B1F, 1F for an hour. With this change the same call reports "warped".

Pinned (source; the behaviour was proven in-game): the step recorder keeps
the last cell entered on each map; attempt's crossed() and use_warp's
outer check both call the warp the one asked for when the last cell on the
floor left was the target tile; and the luajit chunk still compiles under
the local cap."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "harness/shim.lua").read_text()
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


ck("the recorder keeps the last cell on each map",
   "S.last_on[m.id] = { x = p.cellX, y = p.cellY }" in src)
ck("crossed() calls the door asked for by the last cell on the floor left",
   "local _lo = wd.steps.last_on and wd.steps.last_on[startMap]\n"
   "      if _lo and _lo.x == x and _lo.y == y then" in src)
ck("...and so does the outer check, before 'a DIFFERENT door'",
   src.index("if _lo and _lo.x == t.x and _lo.y == t.y then")
   < src.index("way the party was carried through a DIFFERENT door"))
lj = shutil.which("luajit")
if lj:
    r = subprocess.run([lj, "-b", str(ROOT / "harness/shim.lua"), "/dev/null"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                       text=True, errors="replace")
    ck("shim.lua still compiles under LuaJIT's local cap", r.returncode == 0,
       r.stderr[-300:])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
