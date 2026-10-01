#!/usr/bin/env python3
"""The whole Kanto overworld under the run's fog of war: every outdoor map the
game connects (36 of them, Pallet Town to Indigo Plateau), stitched by their
own connection offsets and drawn from the real tiles, with every cell the run
has never had on screen dimmed, and Red where the party stands.

The shim's seen overlay draws only the map the player is on; run/seen.json
already holds every map's seen cells, so this shows all of them at once.

Everything comes from the game's extraction of YOUR ROM: maps.lua (blocks,
sizes, connections), tilesets.lua (each block's 4x4 tiles) and the tileset
images. Read through a Lua interpreter once and cached as JSON; the stitched
base picture is cached as a PNG. Read-only toward the run.

  tools/worldmap.py --png out.png [--scale 0.25]

VIEWER-ONLY: drawn for people watching, never put in front of the model.
"""
import argparse
import json
import os
import re
import subprocess
import sys

from PIL import Image

GEN = os.path.expanduser("~/.local/share/love/pokemon-love2d/red/")
DATA = GEN + "data/generated/"
STATE = os.path.expanduser("~/.local/state/red-recomp/")
CACHE = STATE + "worldmap.json"
BASE = STATE + "worldmap_base.png"
HERE = os.path.dirname(os.path.abspath(__file__))
SEEN = os.path.join(HERE, "..", "run", "seen.json")
OBS = os.path.join(HERE, "..", "run", "obs.json")
PLAYER = GEN + "assets/generated/sprites/red.png"

# the four DMG greys -> a muted green-gray, the HUD's own map shades
SHADES = {0: (26, 29, 28), 85: (58, 66, 61), 170: (96, 108, 98), 255: (140, 152, 138)}
FOG = 0.28                # what is left of an unseen cell's brightness

DUMP_LUA = r"""
local G = arg[1]
local maps = dofile(G .. "maps.lua")
local tilesets = dofile(G .. "tilesets.lua")
local function q(s) return '"' .. tostring(s):gsub('\\', '\\\\'):gsub('"', '\\"') .. '"' end
local function arr(t) local o = {} for i = 1, #t do o[i] = tostring(t[i]) end return "[" .. table.concat(o, ",") .. "]" end
local out, used = {}, {}
for name, m in pairs(maps) do
  if type(m) == "table" and m.connections and next(m.connections) then
    local c = {}
    for d, x in pairs(m.connections) do
      c[#c + 1] = q(d) .. ':{"map":' .. q(x.map) .. ',"offset":' .. (x.offset or 0) .. '}'
    end
    used[m.tileset] = true
    out[#out + 1] = q(name) .. ':{"w":' .. m.width .. ',"h":' .. m.height .. ',"tileset":' .. q(m.tileset)
      .. ',"border":' .. (m.borderBlock or 0) .. ',"blocks":' .. arr(m.blocks) .. ',"conn":{' .. table.concat(c, ",") .. '}}'
  end
end
local ts = {}
for name in pairs(used) do
  local t = tilesets[name]
  local b = {}
  for i = 1, #t.blocks do b[i] = arr(t.blocks[i]) end
  ts[#ts + 1] = q(name) .. ':{"image":' .. q(t.image) .. ',"per":' .. t.tilesPerRow .. ',"blocks":[' .. table.concat(b, ",") .. ']}'
end
print('{"maps":{' .. table.concat(out, ",") .. '},"tilesets":{' .. table.concat(ts, ",") .. '}}')
"""


def load():
    """{maps: {ID: {w, h, tileset, blocks, conn}}, tilesets: {...}}, cached."""
    src = max(os.path.getmtime(DATA + "maps.lua"), os.path.getmtime(DATA + "tilesets.lua"))
    try:
        if os.path.getmtime(CACHE) >= src:
            with open(CACHE) as f:
                return json.load(f)
    except OSError:
        pass
    for lua in ("lua5.4", "lua", "luajit", "lua5.1"):
        try:
            r = subprocess.run([lua, "-", DATA], input=DUMP_LUA, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            continue
        if r.returncode == 0 and r.stdout.strip():
            data = json.loads(r.stdout)
            os.makedirs(STATE, exist_ok=True)
            with open(CACHE, "w") as f:
                json.dump(data, f)
            return data
    sys.exit("could not read the map data (need a lua interpreter)")


def layout(data):
    """Each outdoor map's top-left in blocks, walked out from Pallet Town along
    the maps' own connections: a neighbour to the north sits its height above,
    shifted by the connection's offset, and so on round the compass."""
    maps = data["maps"]
    pos, todo = {"PALLET_TOWN": (0, 0)}, ["PALLET_TOWN"]
    while todo:
        a = todo.pop()
        ax, ay = pos[a]
        A = maps[a]
        for d, c in A["conn"].items():
            b = c["map"]
            if b not in maps or b in pos:
                continue
            B, o = maps[b], c["offset"]
            pos[b] = {"north": (ax + o, ay - B["h"]), "south": (ax + o, ay + A["h"]),
                      "west": (ax - B["w"], ay + o), "east": (ax + A["w"], ay + o)}[d]
            todo.append(b)
    x0 = min(x for x, _ in pos.values())
    y0 = min(y for _, y in pos.values())
    return {k: (x - x0, y - y0) for k, (x, y) in pos.items()}


def base(data, pos):
    """The stitched overworld at full size (32 px a block), cached."""
    try:
        if os.path.getmtime(BASE) >= os.path.getmtime(CACHE):
            return Image.open(BASE).convert("RGB")
    except OSError:
        pass
    maps = data["maps"]
    W = max(pos[k][0] + maps[k]["w"] for k in pos) * 32
    H = max(pos[k][1] + maps[k]["h"] for k in pos) * 32
    img = Image.new("RGB", (W, H), SHADES[0])
    tiles = {}
    for name, ts in data["tilesets"].items():
        sheet = Image.open(GEN + ts["image"]).convert("L")
        lut = [SHADES[min(SHADES, key=lambda s: abs(s - v))] for v in range(256)]
        rgb = Image.new("RGB", sheet.size)
        rgb.putdata([lut[v] for v in sheet.get_flattened_data()])
        per = ts["per"]
        cells = {}
        for bi, block in enumerate(ts["blocks"]):
            b = Image.new("RGB", (32, 32))
            for i, t in enumerate(block):
                b.paste(rgb.crop(((t % per) * 8, (t // per) * 8, (t % per) * 8 + 8, (t // per) * 8 + 8)),
                        ((i % 4) * 8, (i // 4) * 8))
            cells[bi] = b
        tiles[name] = cells
    for name, (bx, by) in pos.items():
        m = maps[name]
        cells = tiles[m["tileset"]]
        for i, blk in enumerate(m["blocks"]):
            img.paste(cells.get(blk, cells.get(0)), ((bx + i % m["w"]) * 32, (by + i // m["w"]) * 32))
    img.save(BASE)
    return img


def read_seen(path=SEEN):
    """run/seen.json is a Lua table: ["MAP"] = { "x,y", ... }."""
    try:
        text = open(path).read()
    except OSError:
        return {}
    out = {}
    for m in re.finditer(r'\["([A-Z0-9_]+)"\]\s*=\s*\{([^}]*)\}', text):
        out[m.group(1)] = {tuple(int(v) for v in c.split(",")) for c in re.findall(r'"(\d+,\d+)"', m.group(2))}
    return out


_sprite = None


def player_sprite(k):
    global _sprite
    if _sprite is None:
        sheet = Image.open(PLAYER).convert("L").crop((0, 0, 16, 16))
        spr = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        tint = {0: (24, 24, 30, 255), 85: (200, 70, 60, 255), 170: (236, 190, 150, 255)}
        for y in range(16):
            for x in range(16):
                v = sheet.getpixel((x, y))
                if v < 250:
                    spr.putpixel((x, y), tint.get(v, (236, 236, 230, 255)))
        _sprite = spr
    return _sprite.resize((max(8, int(16 * k)),) * 2, Image.NEAREST)


def render(scale=0.25, seen=None, here=None):
    """The overworld at `scale` of full size (0.25: a 16 px cell is 4 px),
    unseen cells dimmed, Red on `here` = (MAP_ID, x, y) if it is outdoors."""
    data = load()
    pos = layout(data)
    full = base(data, pos)
    W, H = full.size
    small = full.resize((max(1, int(W * scale)), max(1, int(H * scale))), Image.BOX)
    dark = small.point(lambda v: int(v * FOG))
    # the seen mask, one pixel a 16 px cell, stretched to the picture
    seen = read_seen() if seen is None else seen
    mask = Image.new("L", (W // 16, H // 16), 0)
    for name, (bx, by) in pos.items():
        for x, y in seen.get(name, ()):
            if 0 <= x < data["maps"][name]["w"] * 2 and 0 <= y < data["maps"][name]["h"] * 2:
                mask.putpixel((bx * 2 + x, by * 2 + y), 255)
    mask = mask.resize(small.size, Image.NEAREST)
    out = Image.composite(small, dark, mask)
    if here and here[0] in pos:
        name, x, y = here
        bx, by = pos[name]
        k = 16 * scale
        cx, cy = int((bx * 2 + x) * k + k / 2), int((by * 2 + y) * k + k / 2)
        spr = player_sprite(max(0.5, scale * 2))
        out.paste(spr, (cx - spr.width // 2, cy - spr.height + spr.height // 4), spr)
    return out


def where():
    try:
        obs = json.load(open(OBS))
    except (OSError, ValueError):
        return None
    m = (obs.get("map") or {}).get("id")
    p = obs.get("player") or {}
    x, y = p.get("x", p.get("cellX")), p.get("y", p.get("cellY"))
    return (m, x, y) if m and isinstance(x, int) and isinstance(y, int) else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--png", required=True)
    ap.add_argument("--scale", type=float, default=0.25)
    a = ap.parse_args()
    render(a.scale, here=where()).save(a.png)


if __name__ == "__main__":
    main()
