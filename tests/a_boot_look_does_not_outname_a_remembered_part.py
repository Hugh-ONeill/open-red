#!/usr/bin/env python3
"""The boot look does not out-name a remembered part.

Mt Moon B2F, run 68, 2026-10-30. The shim observes once at boot, before
any command, so the floor the game boots on was painted with a name minted
from its top-left cell. seed_regions then skipped every remembered anchor
already painted, and the ground the run knew as MT_MOON_B2F|20,5 came back
as |3,2: two names for one floor, and every `go` through the cave found no
chain for 35 rounds.

Pinned: the first seed in a process drops what the boot look painted on a
remembered map and plants the remembered names; a later seed adds only
cells not yet named; a map nobody remembers keeps its paint.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


shim = (ROOT / "harness/shim.lua").read_text()
i = shim.index("function OPS.seed_regions(G, c)")
j = shim.index("\nend\n", i) + 5
prog = "local wd = {}\nlocal region_of = {}\nlocal OPS = {}\n" + shim[i:j] + """
region_of.MT_MOON_B2F = { ["3,2"] = "3,2", ["20,5"] = "3,2" }
region_of.ROUTE_4 = { ["1,1"] = "1,1" }
local ok, msg = OPS.seed_regions(nil, { regions = { MT_MOON_B2F = { ["20,5"] = "20,5" } } })
print(region_of.MT_MOON_B2F["20,5"], tostring(region_of.MT_MOON_B2F["3,2"]),
      region_of.ROUTE_4["1,1"], msg)
region_of.MT_MOON_B2F["9,9"] = "9,9"
OPS.seed_regions(nil, { regions = { MT_MOON_B2F = { ["20,5"] = "x", ["1,1"] = "1,1" } } })
print(region_of.MT_MOON_B2F["20,5"], region_of.MT_MOON_B2F["9,9"], region_of.MT_MOON_B2F["1,1"])
"""
with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
    f.write(prog)
r = subprocess.run(["luajit", f.name], capture_output=True, text=True, timeout=30)
got = r.stdout.strip().split("\n") if r.returncode == 0 else []
ck("the function runs", r.returncode == 0, r.stderr[:300])
if len(got) == 2:
    a, b = got[0].split("\t"), got[1].split("\t")
    ck("the first seed plants the remembered name over the boot paint", a[0] == "20,5", a)
    ck("...and drops the boot look's own name on that map", a[1] == "nil", a)
    ck("a map nobody remembers keeps its paint", a[2] == "1,1", a)
    ck("a later seed does not overwrite a named cell", b[0] == "20,5" and b[1] == "9,9", b)
    ck("...but adds one not yet named", b[2] == "1,1", b)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
