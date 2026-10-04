#!/usr/bin/env python3
"""When no reachable seen ground ends anywhere, the spots that still bring
unseen ground into view are the frontier.

Run 27, 2026-09-17, Celadon Mart 4F: the counter clerk stands at (5,7)
behind the counter. The footprint had every reachable cell of the floor
and row 7 only from x=6 on; the frontier is seen ground you can reach that
ends at unseen ground, and no walk borders (5,7), so the floor read
finished with a person on it the page never listed (user: "it just never
appeared in the bots area-footprint").

Pinned: a pure helper lists reachable cells whose view window still covers
unseen cells, nearest first with how many; seen_reach uses it only when
the ordinary frontier is empty and the floor is not dark; the observation
carries the count; the ledger words such a spot. Synthetic, the helper run
in Lua.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


shim = (ROOT / "harness/shim.lua").read_text()
i = shim.index("local function vantage_spots(")
j = shim.index("\nend\n", i) + 5
helper = shim[i:j]

# the 4F shape: 20 x 8, every cell seen except (0..5, 7); reachable ground
# is rows 1..5 across the floor (the counter row 6 and row 7 are not)
prog = helper + """
local mask, dist = {}, {}
for y = 0, 7 do for x = 0, 19 do
  if not (y == 7 and x <= 5) then mask[x .. "," .. y] = true end
end end
for y = 1, 5 do for x = 1, 18 do dist[x .. "," .. y] = math.abs(x - 1) + math.abs(y - 1) end end
local out = vantage_spots(dist, mask, 20, 8, 4, 5, 4, 4)
print(#out)
for i = 1, math.min(3, #out) do print(out[i].x, out[i].y, out[i].d, out[i].vantage) end
-- everything seen: nothing to offer
for x = 0, 5 do mask[x .. ",7"] = true end
print(#vantage_spots(dist, mask, 20, 8, 4, 5, 4, 4))
"""
with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
    f.write(prog)
r = subprocess.run(["lua", f.name], capture_output=True, text=True, timeout=20)
lines = r.stdout.split("\n")
ck("the helper runs", r.returncode == 0, r.stderr[:200])
if r.returncode == 0:
    n = int(lines[0])
    first = lines[1].split("\t")
    ck("reachable cells whose window covers the unseen cells are offered", n > 0, lines[:2])
    ck("...nearest first", int(first[2]) == min(int(l.split("\t")[2]) for l in lines[1:1 + min(3, n)]), lines[1:4])
    fx, fy, fv = int(first[0]), int(first[1]), int(first[3])
    ck("...and the first one really covers (5,7)",
       fx - 4 <= 5 <= fx + 5 and fy - 4 <= 7 <= fy + 4 and fv >= 1, first)
    ck("with everything seen there is nothing to offer", lines[-2] == "0", lines[-3:])

sr = shim[shim.index("seen_reach = function(G, sx, sy, surf)"):]
sr = sr[:sr.index("\nlocal function warp_block")]
ck("seen_reach falls back to them only when the ordinary frontier is empty, and not in the dark",
   "if #front == 0 and not (ow.dark and not (G.save and G.save.flashLit)) then" in sr
   and "front = vantage_spots(dist, mask, W, H, VIEW_L, VIEW_R, VIEW_U, VIEW_D," in sr
   and "ow.map:isCounterCell(x, y)" in sr)

# THE OUTSIDE OF THE WALLS. Pokemon Tower 2F as run 36 had it before the
# sweep that walked eight legs to put its corners on screen (2026-10-04):
# every walkable cell seen, the unseen cells all at the map's edge behind
# wall. With the counter test given, nothing is offered; the Mart's
# counter-side pocket on its edge row still is.
TOWER = [
    '                    ',
    ' ###################',
    '#########.....######',
    '#########.......####',
    '########........####',
    '#####............###',
    '####....######....##',
    '###.....##.........#',
    '###...####..####...#',
    '###...####..####...#',
    '###.....##.........#',
    '####....##........##',
    '#####.######.....###',
    '############..######',
    '  ####..........####',
    '  ######......######',
    '  ##################',
    '  ################# ',
]
lua_rows = "{" + ",".join('"%s"' % r for r in TOWER) + "}"
prog2 = helper + """
local rows = """ + lua_rows + """
local mask, dist = {}, {}
for y = 0, 17 do for x = 0, 19 do
  local c = rows[y + 1]:sub(x + 1, x + 1)
  if c ~= " " then mask[x .. "," .. y] = true end
  if c == "." then dist[x .. "," .. y] = math.abs(x - 9) + math.abs(y - 2) end
end end
local never = function() return false end
print(#vantage_spots(dist, mask, 20, 18, 4, 5, 4, 4))
print(#vantage_spots(dist, mask, 20, 18, 4, 5, 4, 4, never))
-- the Mart 4F shape again, the counter row 6 told as counters
local m2, d2 = {}, {}
for y = 0, 7 do for x = 0, 19 do
  if not (y == 7 and x <= 5) then m2[x .. "," .. y] = true end
end end
for y = 1, 5 do for x = 1, 18 do d2[x .. "," .. y] = math.abs(x - 1) + math.abs(y - 1) end end
print(#vantage_spots(d2, m2, 20, 8, 4, 5, 4, 4, function(x, y) return y == 6 end))
print(#vantage_spots(d2, m2, 20, 8, 4, 5, 4, 4, never))
"""
with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
    f.write(prog2)
r2 = subprocess.run(["lua", f.name], capture_output=True, text=True, timeout=20)
l2 = r2.stdout.split()
ck("the tower case runs", r2.returncode == 0 and len(l2) == 4, r2.stderr[:200])
if len(l2) == 4:
    ck("without the counter test the tower's edge corners still draw a look (old behaviour)",
       int(l2[0]) > 0, l2)
    ck("with it, walled-off cells at the map's edge draw no look", l2[1] == "0", l2)
    ck("a pocket a counter borders on the edge row is still looked for", int(l2[2]) > 0, l2)
    ck("...and the same pocket behind plain wall is not", l2[3] == "0", l2)
ck("the observation carries the count", "vantage = f.vantage or nil" in shim)
led = (ROOT / "planner/ledger.py").read_text()
ck("the ledger words such a spot",
   'elif f.get("vantage"):' in led and "come into view — ground no walk" in led)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:200]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
