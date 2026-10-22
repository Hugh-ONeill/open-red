#!/usr/bin/env python3
"""A few cells of another part's paint inside this component do not join
the two parts.

Run 60, 2026-10-22: after the Mansion's south half was walked, a corner of
its paint ("12,14") sat inside the north half's component in one statue
setting while its basement stairs stayed walled off. parts_here reported
both names, the executor aliased them, and `go` from 1F north planned
['21,23', '23,22'] (the south half's stairs) and called itself arrived:
eight misfires, each right after a "parts_joined" with both names (12:38,
13:09). A fresh boot did not reproduce it, since the paint is the process's
own history.

Pinned: joined_parts keeps the name stood in; keeps another name when most
of its ground is walkable from here (a tree cut, a switch that truly joins);
drops one whose ground is mostly elsewhere; keeps a name with too little
ground to judge; and parts_here is computed by it.
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
i = shim.index("function joined_parts(known, rreach, name)")
j = shim.index("\nend\n", i) + 5
helper = shim[i:j]
prog = helper + """
local function case(spec)
  local known, rreach = {}, {}
  for _, s in ipairs(spec) do
    local nm, n, reach = s[1], s[2], s[3]
    for c = 1, n do
      local k = nm .. ":" .. c
      known[k] = nm
      if c <= reach then rreach[k] = true end
    end
  end
  return table.concat(joined_parts(known, rreach, "1,1"), " ")
end
print(case({ {"1,1", 100, 100}, {"12,14", 60, 5} }))
print(case({ {"1,1", 100, 100}, {"12,14", 60, 60} }))
print(case({ {"1,1", 100, 100}, {"12,14", 60, 45} }))
print(case({ {"1,1", 100, 100}, {"9,9", 5, 1} }))
print(case({ {"1,1", 100, 100}, {"12,14", 60, 0} }))
"""
with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
    f.write(prog)
r = subprocess.run(["luajit", f.name], capture_output=True, text=True, timeout=30)
got = r.stdout.strip().split("\n") if r.returncode == 0 else []
ck("the helper runs", r.returncode == 0, r.stderr[:300])
if len(got) == 5:
    ck("a corner of another part's paint is not a join", got[0] == "1,1", got[0])
    ck("a part wholly walkable from here is joined", got[1] == "1,1 12,14", got[1])
    ck("...and one mostly walkable (75%)", got[2] == "1,1 12,14", got[2])
    ck("a name with too little ground to judge still counts", got[3] == "1,1 9,9", got[3])
    ck("a part with none of its ground here is not named", got[4] == "1,1", got[4])
ck("parts_here is what joined_parts says",
   "local parts = joined_parts(known, rreach, name)" in shim
   and "o.map.parts_here = parts" in shim)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
