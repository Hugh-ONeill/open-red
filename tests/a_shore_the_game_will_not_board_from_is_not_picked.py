#!/usr/bin/env python3
"""The shim does not pick a boarding shore the game refuses, and a refusal
said again is still the game's refusal.

Run 58, 2026-10-19: walk_to(surf=true) chose Seafoam B3F (16,4) -> (16,3),
cave floor $05 beside water $14, the CAVERN pair pokered's ItemUseSurfboard
refuses (TilePairCollisionsWater). The port boarded there anyway (engine
fix: gen1recomp b785b5ae) into a pocket it could not walk out of. With the
engine fixed, the same pick was refused, and the second "No SURFing on FIZZY
here!" in one walk read "SURF did not fire (the menus closed without it)",
because the refusal was found by its text changing. Probed in game with
both fixes: both presses quote the game, walk_to(19,9) boards from a legal
shore, walk_to(17,3) says there is no path.
"""
from __future__ import annotations
import subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = Path.home() / "Developer/gen1recomp"
checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

shim = (ROOT / "harness/shim.lua").read_text()
i = shim.index("function board_blocked(map, sx, sy, wx, wy)")
j = shim.index("\nend\n", i) + 5
helper = shim[i:j]
red = Path.home() / ".local/share/love/pokemon-love2d/red"
prog = f"""
package.path = "{GEN}/?.lua;{GEN}/?/init.lua;" .. package.path
if not _G.love then _G.love = require("tests.love_stub") end
local Data = require("src.core.Data"); Data:load()
local Collision = require("src.world.Collision"); Collision.load(Data)
local MapLoader = require("src.world.MapLoader")
local m = MapLoader.load(Data, "SEAFOAM_ISLANDS_B3F")
{helper}
print(tostring(board_blocked(m, 16, 4, 16, 3)), tostring(board_blocked(m, 19, 10, 19, 9)))
"""
with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
    f.write(prog)
r = subprocess.run(["luajit", f.name], capture_output=True, text=True, timeout=120,
                   cwd=str(GEN), env={"RED_CACHE": str(red), "PATH": "/usr/bin:/bin"})
last = (r.stdout.strip().splitlines() or [""])[-1].split()
ck("the helper runs on the engine's own collision data", r.returncode == 0 and len(last) == 2,
   (r.stderr or r.stdout)[-300:])
if len(last) == 2:
    ck("B3F (16,4) -> (16,3) is a shore the game will not board from", last[0] == "true", last)
    ck("water to water is not a boarding pair", last[1] == "false", last)

ck("walk_to's mount skips such a shore",
   "and real_water(G, ow.map, wx, wy)\n               and not board_blocked(ow.map, sx, sy, wx, wy) then" in shim)
ck("grind's surf mount skips it",
   "and not board_blocked(map, sx, sy, wx, wy)\n           and map:isWaterCell(wx, wy) then" in shim)
ck("sweep's mount asks nearest_shore for a boarding shore",
   "nearest_shore(G, true)" in shim
   and "and not (to_board and board_blocked(map, sx, sy, wx, wy)) then" in shim)
ck("a rod still casts from any shore", "local bx, by, bland = nearest_shore(G)\n" in shim)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
raise SystemExit(1 if failed else 0)
