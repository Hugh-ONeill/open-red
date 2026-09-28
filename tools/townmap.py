#!/usr/bin/env python3
"""The Kanto town map with the model's plan drafts drawn on it as routes, for
the screen while the model authors (the game is closed then).

Everything comes from the game's extraction of YOUR ROM: the 8x8 tiles
(assets/generated/townmap/tiles.png) and the town map layout + every map's
cell (data/generated/field.lua townMap, pret's town_map_entries). The Lua
table is read once through a Lua interpreter and cached as JSON.

VIEWER-ONLY. This is the printed map drawn for people watching; it is never
put in front of the model.

  tools/townmap.py --png out.png    # the current authoring phase, one frame
"""
import argparse
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw

GEN = os.path.expanduser("~/.local/share/love/pokemon-love2d/red/")
TILES = GEN + "assets/generated/townmap/tiles.png"
FIELD = GEN + "data/generated/field.lua"
CACHE = os.path.expanduser("~/.local/state/red-recomp/townmap.json")

W, H = 160, 144          # the town map screen, 20x18 tiles of 8x8

# drafts in draw order; the picked one is drawn last and brightest
DRAFT_COLORS = [(122, 162, 247), (224, 175, 104), (187, 154, 247), (125, 207, 255),
                (247, 118, 142), (158, 206, 106)]
PICKED = (124, 196, 155)
YOU = (236, 236, 230)
# the four DMG greys of the tiles -> a muted, dark-ish map so routes pop
SHADES = {0: (32, 36, 34), 85: (62, 70, 64), 170: (104, 116, 104), 255: (150, 162, 146)}

DUMP_LUA = r"""
local f = dofile(arg[1])
local t = f.townMap
local out = {}
local function q(s) return '"' .. tostring(s):gsub('\\', '\\\\'):gsub('"', '\\"') .. '"' end
local m = {}
for i, v in ipairs(t.background.map) do m[#m + 1] = tostring(v) end
out[#out + 1] = '"map":[' .. table.concat(m, ",") .. ']'
local l = {}
for name, loc in pairs(t.locations) do
  l[#l + 1] = q(name) .. ':{"x":' .. loc.x .. ',"y":' .. loc.y .. ',"name":' .. q(loc.name or name) .. '}'
end
out[#out + 1] = '"locations":{' .. table.concat(l, ",") .. '}'
print('{' .. table.concat(out, ",") .. '}')
"""


def load():
    """{map: [360 tile ids], locations: {MAP_ID: {x, y, name}}}, cached."""
    try:
        if os.path.getmtime(CACHE) >= os.path.getmtime(FIELD):
            with open(CACHE) as f:
                return json.load(f)
    except OSError:
        pass
    for lua in ("lua5.4", "lua", "luajit", "lua5.1"):
        try:
            out = subprocess.run([lua, "-", FIELD], input=DUMP_LUA, capture_output=True,
                                 text=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            continue
        if out.returncode == 0 and out.stdout.strip():
            data = json.loads(out.stdout)
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            with open(CACHE, "w") as f:
                json.dump(data, f)
            return data
    return None


_base = None


def base_map():
    """The bare town map at 1x, in SHADES."""
    global _base
    if _base is None:
        data = load()
        tiles = Image.open(TILES).convert("L")
        img = Image.new("RGB", (W, H), SHADES[0])
        per = tiles.width // 8
        for i, t in enumerate((data or {}).get("map") or []):
            tile = tiles.crop(((t % per) * 8, (t // per) * 8, (t % per) * 8 + 8, (t // per) * 8 + 8))
            col, row = i % 20, i // 20
            for y in range(8):
                for x in range(8):
                    img.putpixel((col * 8 + x, row * 8 + y), SHADES.get(tile.getpixel((x, y)), SHADES[0]))
        _base = img
    return _base


def cell_center(locations, map_id, k):
    loc = locations.get(map_id)
    if not loc:
        return None
    # the grid sits 16 px in and 8 px down on the screen (TownMap.lua's
    # markerXY: x*8+16, y*8+8); +4 is the middle of the 8x8 cell
    return (loc["x"] * 8 + 16 + 4) * k, (loc["y"] * 8 + 8 + 4) * k


def to_ids(route):
    """'route 24 -> cerulean city' (events.py wording) -> ['ROUTE_24', 'CERULEAN_CITY']"""
    return [s.strip().upper().replace(" ", "_") for s in route.split("->") if s.strip()]


def render(phase, start_map=None, k=2):
    """The map at k times the Game Boy's size, every draft a line from where the
    party stands through each map it names, the picked one drawn last in green.
    Maps with no town-map cell (a few interiors) are skipped, as the game's own
    town map does."""
    data = load() or {}
    locs = data.get("locations") or {}
    img = base_map().resize((W * k, H * k), Image.NEAREST)
    draw = ImageDraw.Draw(img)
    drafts = phase.get("drafts") or []
    picked = (phase.get("picked") or {}).get("n")
    order = [d for d in drafts if d["n"] != picked] + [d for d in drafts if d["n"] == picked]
    for d in order:
        ids = ([start_map] if start_map else []) + to_ids(d["route"])
        pts = []
        for m in ids:
            p = cell_center(locs, m, k)
            if p and (not pts or pts[-1] != p):
                pts.append(p)
        on = d["n"] == picked
        col = PICKED if on else DRAFT_COLORS[(d["n"] - 1) % len(DRAFT_COLORS)]
        if picked and not on:
            col = tuple(int(c * 0.55 + 20) for c in col)      # the losers fade
        # offset each draft a little so overlapping routes stay readable
        off = 0 if on else ((d["n"] % 3) - 1) * max(1, k // 2)
        pts = [(x + off, y + off) for x, y in pts]
        if len(pts) > 1:
            draw.line(pts, fill=col, width=max(2, k + (1 if on else 0)), joint="curve")
        for x, y in pts[1:]:
            r = k + (1 if on else 0)
            draw.rectangle((x - r, y - r, x + r, y + r), fill=col)
        if pts:
            x, y = pts[-1]
            r = 2 * k
            draw.rectangle((x - r, y - r, x + r, y + r), outline=col, width=max(1, k // 2))
    if start_map:
        p = cell_center(locs, start_map, k)
        if p:
            x, y = p
            r = 2 * k
            draw.ellipse((x - r, y - r, x + r, y + r), fill=YOU)
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--png", required=True)
    ap.add_argument("--scale", type=int, default=4)
    args = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import events
    phase = events.read_phase() or {}
    try:
        with open(events.OBS) as f:
            start = (json.load(f).get("map") or {}).get("id")
    except (OSError, ValueError):
        start = None
    render(phase, start, args.scale).save(args.png)


if __name__ == "__main__":
    main()
