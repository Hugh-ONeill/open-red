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
PLAYER = GEN + "assets/generated/sprites/red.png"
CHAIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "run", "chain.log")
FIELD = GEN + "data/generated/field.lua"
CACHE = os.path.expanduser("~/.local/state/red-recomp/townmap.json")

W, H = 160, 144          # the town map screen, 20x18 tiles of 8x8

# drafts in draw order; the picked one is drawn last and brightest. Gold is
# kept off this list: it belongs to the last attempt's trail.
DRAFT_COLORS = [(122, 162, 247), (187, 154, 247), (125, 207, 255), (247, 118, 142),
                (158, 206, 106), (230, 150, 200)]
PICKED = (124, 196, 155)
LAST_ATTEMPT = (255, 205, 80)
# earlier legs of THIS run: a ramp from the first leg to the latest
PAST_OLD, PAST_NEW = (128, 132, 140), (240, 240, 236)   # gray -> white: no draft uses them
# the four DMG greys of the tiles -> a muted, dark-ish map so routes pop
SHADES = {0: (26, 29, 28), 85: (46, 52, 49), 170: (74, 83, 76), 255: (104, 115, 104)}

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


def run_history(path=CHAIN, tail_bytes=4_000_000):
    """The current run's walk, read off chain.log from the last new_game:
    [(leg, attempt_no, MAP_ID), ...] in the order the maps were entered.
    attempt_no counts every '=== attempt' line, so the last group is the
    attempt that ran most recently."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - tail_bytes))
            lines = f.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return []
    start = 0
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("[bootstrap] new_game"):
            start = i
            break
    leg, attempt, out = 0, 0, []
    for line in lines[start:]:
        if line.startswith("=== leg "):
            try:
                leg = int(line[8:].split("/")[0].split()[0].rstrip(":"))
            except ValueError:
                pass
        elif line.startswith("=== attempt"):
            attempt += 1
        elif line.startswith("[info] map: "):
            m = line[12:].split(" at ")[0].strip()
            out.append((leg, attempt, m))
    return out


_sprite = None


def player_sprite(k):
    """Red standing, facing down (frame 0 of the overworld sheet), white
    see-through as the Game Boy draws sprites, at k times its size."""
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
    return _sprite.resize((16 * k, 16 * k), Image.NEAREST)


def ramp(i, n):
    t = 0.0 if n <= 1 else i / (n - 1)
    return tuple(int(a + (b - a) * t) for a, b in zip(PAST_OLD, PAST_NEW))


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


def trail(locs, maps, k):
    """Cell centres along a walk, repeats of the same cell collapsed."""
    pts = []
    for m in maps:
        p = cell_center(locs, m, k)
        if p and (not pts or pts[-1] != p):
            pts.append(p)
    return pts


def render(phase, start_map=None, k=2, history=None):
    """The map at k times the Game Boy's size: this run's walk so far (earlier
    legs on a dim slate ramp, the most recent attempt in gold), every draft a
    line from where the party stands through each map it names (the picked one
    last, in green), and Red standing where the party is. Maps with no
    town-map cell (a few interiors) are skipped, as the game's own map does."""
    data = load() or {}
    locs = data.get("locations") or {}
    img = base_map().resize((W * k, H * k), Image.NEAREST)
    draw = ImageDraw.Draw(img)

    # ---- the walk so far
    hist = run_history() if history is None else history
    if hist:
        last_attempt = hist[-1][1]
        legs = sorted({leg for leg, att, _ in hist if att != last_attempt})
        shade = {leg: ramp(i, len(legs)) for i, leg in enumerate(legs)}
        # every cell this run has stood in, by the leg that first reached it
        seen = {}
        for leg, att, m in hist:
            seen.setdefault(m, leg)
        for m, leg in seen.items():
            p = cell_center(locs, m, k)
            if p:
                x, y = p
                r = max(2, k + 1)
                draw.rectangle((x - r, y - r, x + r, y + r), fill=shade.get(leg, PAST_NEW))
        # earlier attempts' moves, leg by leg
        prev = None
        for leg, att, m in hist:
            if att == last_attempt:
                break
            p = cell_center(locs, m, k)
            if p and prev and p != prev:
                draw.line((prev, p), fill=shade.get(leg, PAST_NEW), width=max(1, k))
            prev = p or prev
        # the last attempt, in gold, thicker; its cells outlined, so an attempt
        # that never left one town still shows
        last = [m for leg, att, m in hist if att == last_attempt]
        for m in set(last):
            p = cell_center(locs, m, k)
            if p:
                x, y = p
                r = 2 * k + 1
                draw.rectangle((x - r, y - r, x + r, y + r), outline=LAST_ATTEMPT, width=max(1, k // 2 + 1))
        pts = trail(locs, ([hist[-len(last) - 1][2]] if len(hist) > len(last) else []) + last, k)
        if len(pts) > 1:
            draw.line(pts, fill=LAST_ATTEMPT, width=max(2, k + 1), joint="curve")

    # ---- the drafts
    drafts = phase.get("drafts") or []
    picked = (phase.get("picked") or {}).get("n")
    order = [d for d in drafts if d["n"] != picked] + [d for d in drafts if d["n"] == picked]
    for d in order:
        pts = trail(locs, ([start_map] if start_map else []) + to_ids(d["route"]), k)
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

    # ---- Red, where the party stands
    if start_map:
        p = cell_center(locs, start_map, k)
        if p:
            spr = player_sprite(k)
            x, y = p
            img.paste(spr, (x - spr.width // 2, y - spr.height + 4 * k // 2), spr)
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
