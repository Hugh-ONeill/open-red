#!/usr/bin/env python3
"""The Dramatic Shape voxel mod, on the 1x copy only, and logic-neutral.

The copy replays the run step for step, so a mod on it may change what is
drawn but never a logic step, a random draw or an audio question. Dramatic
Shape (gen1recomp/mods_disabled/DRAMATIC_SHAPE, v1.8.2) draws a voxel diorama
and 3D battles, but some of it touches logic even at its defaults (audit
2026-10-04). This installs a PRIVATE copy into the copy's own love identity
(~/.local/share/love/red-shadow/mods/, which only that identity sees) with
those parts patched out, and enables only the draw-only options:

  patched out   BattleExit (its fade held battle.finish 12 logic steps)
                Shiny.decide (rewrote DVs and stats; could draw love.math)
                Horde / the Konami code and the SELECT camera cycle
                the OPTIONS menu rows it adds and removes
  kept off      VOXEL 1 (FULL) / 6 (1ST) / 7 (3RD), LET'S GO, VR
  on            VOXEL at a fixed camera angle (2-5), T-SHIFT, 2D-3D battles

The run's own identity never sees the mod. Viewer-only.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

GAME = Path(os.environ.get("GEN1RECOMP_DIR") or Path.home() / "Developer/gen1recomp")
SOURCE = GAME / "mods_disabled/DRAMATIC_SHAPE"
LEAVE_OUT = {"oxr", "oxr.zip", "model_extract", "tests", "tools"}

# (file, exact text, replacement): each must match once, or the install stops
# (a mod update moved the code; re-audit before trusting it on the copy)
PATCHES = [
    ("lib/BattleExit.lua", "\nreturn BattleExit",
     "\n-- red-recomp copy: the exit fade holds BattleState:finish for 12 logic\n"
     "-- steps, which the unmodded run never takes\n"
     "function BattleExit.modeOn() return false end\n\nreturn BattleExit"),
    ("lib/Shiny.lua", "\nreturn Shiny",
     "\n-- red-recomp copy: never rewrite DVs or stats (and never draw from the\n"
     "-- game's generator); only report what the mon already is\n"
     "function Shiny.decide(mon) return Shiny.mark(mon) end\n\nreturn Shiny"),
    ("lib/Horde.lua", "\nreturn Horde",
     "\n-- red-recomp copy: no Konami horde (it eats presses and draws love.math),\n"
     "-- and a locked view refuses the SELECT / 3 camera cycle\n"
     "function Horde.canStart() return false end\n"
     "function Horde.viewLocked() return true end\n\nreturn Horde"),
    # THE RUN'S SEEN GROUND, IN THE DIORAMA (user, 2026-10-04: "mod the mod to
    # include our shadow overlay"). The copy keeps which cells have been seen
    # and hands each map's mask over through Game.redFog (tools/shadow); the
    # terrain shader darkens an unseen cell and lines a seen cell's sides that
    # border unseen ground in red, in the mesh's own space (one unit a world
    # pixel, a map cell 16), so perspective, height and buildings come free.
    ("lib/Voxel3D.lua", """  varying LOVE_HIGHP_OR_MEDIUMP vec3 vGrid;
#endif
#ifdef VERTEX""", """  varying LOVE_HIGHP_OR_MEDIUMP vec3 vGrid;
#endif
  // red-recomp copy: the run's seen ground, one texel per map cell
  varying LOVE_HIGHP_OR_MEDIUMP vec3 vSeenPos;
  uniform Image seenMask;
  uniform vec4 seenInfo;      // cells wide, cells high, on, unused
#ifdef VERTEX"""),
    ("lib/Voxel3D.lua", "    vec4 w = model * vertex_position;",
     "    vSeenPos = vertex_position.xyz;\n    vec4 w = model * vertex_position;"),
    ("lib/Voxel3D.lua", "    rgb = mix(rgb, fogColor, vFog);", """    if (seenInfo.z > 0.5) {
      vec2 cell = floor(vSeenPos.xz / 16.0);
      if (cell.x >= 0.0 && cell.y >= 0.0 && cell.x < seenInfo.x && cell.y < seenInfo.y) {
        vec2 inv = 1.0 / seenInfo.xy;
        if (Texel(seenMask, (cell + 0.5) * inv).r < 0.5) {
          rgb *= 0.45;
        } else {
          vec2 f = fract(vSeenPos.xz / 16.0);
          float e = 0.08, edge = 0.0;
          if (f.x < e && cell.x > 0.0 && Texel(seenMask, (cell + vec2(-0.5, 0.5)) * inv).r < 0.5) edge = 1.0;
          if (f.x > 1.0 - e && cell.x < seenInfo.x - 1.0 && Texel(seenMask, (cell + vec2(1.5, 0.5)) * inv).r < 0.5) edge = 1.0;
          if (f.y < e && cell.y > 0.0 && Texel(seenMask, (cell + vec2(0.5, -0.5)) * inv).r < 0.5) edge = 1.0;
          if (f.y > 1.0 - e && cell.y < seenInfo.y - 1.0 && Texel(seenMask, (cell + vec2(0.5, 1.5)) * inv).r < 0.5) edge = 1.0;
          rgb = mix(rgb, vec3(1.0, 0.15, 0.15), edge * 0.9);
        }
      }
    }
    rgb = mix(rgb, fogColor, vFog);"""),
    ("lib/Voxel3D.lua", "function Voxel3D.draw(mesh, texture, model, pull, sunModel)",
     """-- red-recomp copy: the seen-ground mask for the map whose terrain draws
-- next (nil: none, for everything that is not terrain)
function Voxel3D.fogFor(map)
  if not (active and activeShader) then return end
  local okG, G = pcall(require, "src.core.Game")
  local img, w, h
  if map and okG and G and G.redFog then img, w, h = G.redFog(map.id) end
  if img then
    pcall(activeShader.send, activeShader, "seenMask", img)
    pcall(activeShader.send, activeShader, "seenInfo", { w, h, 1, 0 })
  else
    pcall(activeShader.send, activeShader, "seenInfo", { 0, 0, 0, 0 })
  end
end

function Voxel3D.draw(mesh, texture, model, pull, sunModel)"""),
    ("lib/VoxelScene.lua", "  Voxel3D.draw(terrain, atlasFor(state.map), nil)",
     "  Voxel3D.fogFor(state.map)\n  Voxel3D.draw(terrain, atlasFor(state.map), nil)"),
    ("lib/VoxelScene.lua", """    if ViewBox.showsMap(nb) then
      Voxel3D.draw(nbMesh[i], atlasFor(nb.map),
                   Mat4.translate(nb.ox, 0, nb.oy))
    end
  end""", """    if ViewBox.showsMap(nb) then
      Voxel3D.fogFor(nb.map)
      Voxel3D.draw(nbMesh[i], atlasFor(nb.map),
                   Mat4.translate(nb.ox, 0, nb.oy))
    end
  end
  Voxel3D.fogFor(nil)"""),
    # how many mesh builds are still queued, for the copy to keep its
    # CONTINUING card up until the map it boots onto is built
    ("lib/ChunkMesher.lua", """function ChunkMesher.pending()
  return #jobs
end""", """function ChunkMesher.pending()
  return #jobs
end
pcall(function() require("src.core.Game").redMeshPending = ChunkMesher.pending end)"""),
    ("main.lua", 'mod.hooks:wrap("ui.options.rows", function(next, game, rows)',
     '-- red-recomp copy: the OPTIONS menu keeps the rows the run had\n'
     'local _ds_rows_off = (function(next, game, rows)'),
]


def install(ident_dir: Path) -> Path:
    """The patched mod into this identity's own mods folder, fresh each time."""
    dest = ident_dir / "mods" / "DRAMATIC_SHAPE"
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, dest, ignore=lambda d, names: [n for n in names if n in LEAVE_OUT and Path(d) == SOURCE])
    for rel, old, new in PATCHES:
        p = dest / rel
        s = p.read_text()
        if s.count(old) != 1:
            raise SystemExit(f"dramatic: {rel} has changed ({s.count(old)} matches): re-audit the mod")
        p.write_text(s.replace(old, new))
    return dest


ENABLE = r"""
package.path = "./?.lua;./?/init.lua;" .. package.path
local S = require("src.core.SaveSerializer")
local path, voxel, tilt, extra = arg[1], tonumber(arg[2]), tonumber(arg[3]), arg[4] or ""
local f = assert(io.open(path, "r")); local body = f:read("*a"); f:close()
local o = assert(S.decode(body))
o.mods = o.mods or {}; o.mods.DRAMATIC_SHAPE = true
o.modsByVersion = o.modsByVersion or {}
o.modsByVersion.red = o.modsByVersion.red or {}
o.modsByVersion.red.DRAMATIC_SHAPE = true
o.pipelines = o.pipelines or {}
o.pipelines.voxel, o.pipelines.tiltshift = voxel, tilt
o.modOptions = o.modOptions or {}
local m = o.modOptions.DRAMATIC_SHAPE or {}
m.letsgo, m.vr, m.battles = false, false, true
-- the draw-only options from SHADOW_DS_OPTS ("water=false,shadows=false")
for k, v in extra:gmatch("([%w_]+)=([^,]+)") do
  if v == "true" then v = true elseif v == "false" then v = false
  elseif tonumber(v) then v = tonumber(v) end
  if k ~= "letsgo" and k ~= "vr" then m[k] = v end
end
o.modOptions.DRAMATIC_SHAPE = m
local g = assert(io.open(path, "w")); g:write(S.encode(o)); g:close()
"""


def enable(ident_dir: Path, voxel: int = 3, tilt: int = 1, extra: str = "") -> None:
    """Turn the mod on in this identity's options: a fixed camera angle only."""
    if voxel not in (2, 3, 4, 5):
        raise SystemExit("dramatic: VOXEL must be a fixed angle, 2-5 (1/6/7 change logic)")
    opts = ident_dir / "options.lua"
    script = ident_dir / "dramatic_enable.lua"
    script.write_text(ENABLE)
    subprocess.run(["luajit", str(script), str(opts), str(voxel), str(tilt), extra],
                   cwd=GAME, check=True, timeout=60, stdin=subprocess.DEVNULL)
