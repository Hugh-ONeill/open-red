#!/usr/bin/env python3
"""A Seafoam current sets the rider down somewhere, and the swim flood
follows it there.

Run 27, 2026-09-18, Seafoam B3F: the flood treated a current cell as "the
ride carries you off it again, so it is nowhere", so everything reached
only by riding a current read, from the west part, as "its way in is ground
you have not stood on" — the ladder up at (25,14) among it — while the run
had surfed there (user: "it could reach, just with surf ... at least for
25,14 i mean").

Pinned: the landing of each current is computed from the engine's own
scripted moves (B3F: (15,8) -> (20,17); (18,7) and (19,7) -> (20,17)); a
non-current cell has none; the flood, still refusing the current cell
itself, marks and continues from the landing. The helper runs in Lua
against the recomp's field data.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = Path.home() / "Developer/gen1recomp"
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


shim = (ROOT / "harness/shim.lua").read_text()
i = shim.index("function seafoam_landing(G, x, y)")
j = shim.index("\nend\n", i) + 5
helper = shim[i:j]
prog = f"""
package.path = "{GEN}/?.lua;" .. package.path
local field = dofile("{GEN}/data/generated/field.lua")
local G = {{ overworld = {{ map = {{ id = "SEAFOAM_ISLANDS_B3F" }} }}, data = {{ field = field }} }}
{helper}
for _, c in ipairs({{ {{15, 8}}, {{18, 7}}, {{19, 7}}, {{10, 10}} }}) do
  print(c[1], c[2], seafoam_landing(G, c[1], c[2]))
end
"""
with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
    f.write(prog)
r = subprocess.run(["luajit", f.name], capture_output=True, text=True, timeout=30)
got = [l.split("\t") for l in r.stdout.strip().split("\n")] if r.returncode == 0 else []
ck("the helper runs on the recomp's field data", r.returncode == 0, r.stderr[:300])
if got:
    ck("the entry current (15,8) lands at (20,17)", got[0][2:] == ["20", "17"], got[0])
    ck("(18,7) lands at (20,17)", got[1][2:] == ["20", "17"], got[1])
    ck("(19,7) lands at (20,17)", got[2][2:] == ["20", "17"], got[2])
    ck("a cell that is not a current has no landing", got[3][2:] in ([], ["nil"]), got[3])

wr = shim[shim.index("  local FORCED = ((surf or (p and p.surfing)) and seafoam_forced(G)) or nil"):]
wr = wr[:4000]
ck("the flood still refuses the current cell itself",
   'seen[key(nx, ny)] = nil' in wr)
ck("...and marks and continues from where the current sets the rider down",
   'if FORCED[key(nx, ny)] == "carried" then' in wr
   and "local cx2, cy2 = seafoam_landing(G, nx, ny)" in wr
   and "q[#q + 1] = { x = cx2, y = cy2 }" in wr)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
