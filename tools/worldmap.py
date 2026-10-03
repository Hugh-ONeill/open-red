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
import time
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
JOURNAL = os.path.join(HERE, "..", "run", "executor_log.jsonl")
TRAIL = STATE + "trail.jsonl"            # tools/events.py writes a breadcrumb per cell the player stands on
STEPS = os.path.join(HERE, "..", "run", "steps.log")   # the shim writes every cell stepped on

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
local rooms = {}
for name, m in pairs(maps) do
  if type(m) == "table" and m.blocks and m.width and not (m.connections and next(m.connections)) then
    local w = {}
    for _, x in ipairs(m.warps or {}) do
      w[#w + 1] = '[' .. x.x .. ',' .. x.y .. ',' .. q(x.destMap or "") .. ',' .. (x.destWarp or 0) .. ']'
    end
    used[m.tileset] = true
    rooms[#rooms + 1] = q(name) .. ':{"w":' .. m.width .. ',"h":' .. m.height .. ',"tileset":' .. q(m.tileset)
      .. ',"blocks":' .. arr(m.blocks) .. ',"warps":[' .. table.concat(w, ",") .. ']}'
  end
end
local ts = {}
for name in pairs(used) do
  local t = tilesets[name]
  local b = {}
  for i = 1, #t.blocks do b[i] = arr(t.blocks[i]) end
  ts[#ts + 1] = q(name) .. ':{"image":' .. q(t.image) .. ',"per":' .. t.tilesPerRow .. ',"blocks":[' .. table.concat(b, ",") .. ']}'
end
local doors = {}
for name, m in pairs(maps) do
  if type(m) == "table" and m.warps then
    for _, w in ipairs(m.warps) do
      if w.destMap and w.destMap ~= "LAST_MAP" then
        doors[#doors + 1] = '[' .. q(name) .. ',' .. w.x .. ',' .. w.y .. ',' .. q(w.destMap) .. ']'
      end
    end
  end
end
print('{"maps":{' .. table.concat(out, ",") .. '},"tilesets":{' .. table.concat(ts, ",") ..
      '},"doors":[' .. table.concat(doors, ",") .. '],"rooms":{' .. table.concat(rooms, ",") .. '}}')
"""


def load():
    """{maps: {ID: {w, h, tileset, blocks, conn}}, tilesets: {...}}, cached."""
    src = max(os.path.getmtime(DATA + "maps.lua"), os.path.getmtime(DATA + "tilesets.lua"))
    try:
        if os.path.getmtime(CACHE) >= src:
            with open(CACHE) as f:
                data = json.load(f)
            if "doors" in data and "rooms" in data:     # an older cache lacks them
                return data
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


_cells = {}


def block_cells(data):
    """{tileset: {block id: 32x32 image}} from each tileset's 8x8 tiles."""
    if not _cells:
        lut = [SHADES[min(SHADES, key=lambda s: abs(s - v))] for v in range(256)]
        for name, ts in data["tilesets"].items():
            sheet = Image.open(GEN + ts["image"]).convert("L")
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
            _cells[name] = cells
    return _cells


_rooms_img = {}


def room_image(data, mid):
    """One indoor map at full size (32 px a block), cached."""
    if mid not in _rooms_img:
        m = data["rooms"][mid]
        cells = block_cells(data)[m["tileset"]]
        img = Image.new("RGB", (m["w"] * 32, m["h"] * 32), SHADES[0])
        for i, blk in enumerate(m["blocks"]):
            img.paste(cells.get(blk, cells.get(0)), ((i % m["w"]) * 32, (i // m["w"]) * 32))
        _rooms_img[mid] = img
    return _rooms_img[mid]


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
    tiles = block_cells(data)
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


def anchors(data):
    """{INTERIOR: [(OUTDOOR_MAP, x, y), ...]}: where each cave floor or
    building sits on the overworld, found by walking back up the doors that
    lead into it until an outdoor map is reached (Rock Tunnel B1F <- 1F <- the
    two doors on Route 10). Interiors' own exits mostly say LAST_MAP, so the
    search reads the doors pointing IN. All the doors at the shallowest depth
    are kept; a place with two entrances sits between them."""
    outdoor = set(data["maps"])
    into = {}
    for src, x, y, dst in data.get("doors") or []:
        into.setdefault(dst, []).append((src, x, y))
    out = {}

    def find(mid):
        frontier, seen = [mid], {mid}
        while frontier:
            found, nxt = [], []
            for m in frontier:
                for src, x, y in into.get(m, []):
                    if src in outdoor:
                        found.append((src, x, y))
                    elif src not in seen:
                        seen.add(src)
                        nxt.append(src)
            if found:
                return found
            frontier = nxt
        return []
    for mid in into:
        if mid not in outdoor:
            out[mid] = find(mid)
    return out


def authoring_view(phase, history, here, size, start_map=None):
    """The overworld under the fog, fitted to `size` (w, h) px, with the run's
    walk (earlier legs gray to white, the last attempt in gold) through the
    cells it actually entered, every draft from where the party is (picked in
    green, the rest faded), and Red. Caves and buildings sit at their doors on
    the overworld (anchors), so nothing the run or a draft names falls off."""
    sys.path.insert(0, HERE)
    import townmap as tm
    data = load()
    pos = layout(data)
    anc = anchors(data)
    full_w = max(pos[k][0] + data["maps"][k]["w"] for k in pos) * 32
    full_h = max(pos[k][1] + data["maps"][k]["h"] for k in pos) * 32
    scale = min(size[0] / full_w, size[1] / full_h)
    img = render(scale, here=None)
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    k = 16 * scale
    lw = max(2, int(round(3 * scale * 4)))           # ~3 px at a quarter scale

    def pt(mid, xy=None, near=None):
        """A map (and optionally a cell in it) as a point on the picture. A
        cave or building is its door; with several doors (Diglett's Cave
        opens on Route 2 AND Route 11) the one nearest `near`, the point
        the line arrives from, else their middle."""
        if mid in pos:
            bx, by = pos[mid]
            x, y = xy if xy else (data["maps"][mid]["w"], data["maps"][mid]["h"])
            return (int((bx * 2 + x) * k + k / 2), int((by * 2 + y) * k + k / 2))
        a = anc.get(mid)
        if a:
            xs = [pt(m, (x, y)) for m, x, y in a]
            if near:
                return min(xs, key=lambda q: (q[0] - near[0]) ** 2 + (q[1] - near[1]) ** 2)
            return (sum(p[0] for p in xs) // len(xs), sum(p[1] for p in xs) // len(xs))
        return None

    def walk(stops, start=None):
        """[(MAP, xy-or-None), ...] -> points, each place resolved near the last."""
        out, last = [], start
        for mid, xy in stops:
            q = pt(mid, xy if mid in pos else None, near=last)
            out.append(q)
            last = q or last
        return out

    def trail_(points, col, width):
        p = []
        for q in points:
            if q and (not p or p[-1] != q):
                p.append(q)
        if len(p) > 1:
            d.line(p, fill=col, width=width, joint="curve")
        return p

    # the walk so far: the actual path (trail()) when there is one, cell by
    # cell outdoors; a cave or building is its door, and a visit to one from
    # its own street is left out as before
    path = trail()
    if path:
        last = path[-1][1]
        legs = sorted({p_[0] for p_ in path if p_[1] != last})
        shade = {leg: tm.ramp(i, len(legs)) for i, leg in enumerate(legs)}
        pts, outside = [], None
        for leg, att, m, x, y, kind in path:
            if m in pos:
                outside = m
                q = pt(m, (x, y))
            elif outside and any(a[0] == outside for a in anc.get(m, [])):
                continue
            else:
                q = pt(m, None, near=pts[-1][2] if pts else None)
            if q and (not pts or pts[-1][2] != q):
                pts.append((leg, att, q, kind))
        # recorded steps are a cell apart; a longer gap between two of them is
        # a warp (a door, a hole, Fly) and is not walked, so no line crosses it
        gap = 3 * k + 2

        def joined(a, b):
            return not (b[3] == "step" and a[3] == "step"
                        and abs(a[2][0] - b[2][0]) + abs(a[2][1] - b[2][1]) > gap)
        for p0, p1 in zip(pts, pts[1:]):
            if p1[1] == last or not joined(p0, p1):
                continue
            d.line((p0[2], p1[2]), fill=shade.get(p1[0], tm.PAST_NEW), width=max(1, lw - 1))
        i0 = next((i for i, p_ in enumerate(pts) if p_[1] == last), None)
        if i0 is not None:
            run = pts[max(0, i0 - 1):]
            for p0, p1 in zip(run, run[1:]):
                if joined(p0, p1):
                    d.line((p0[2], p1[2]), fill=tm.LAST_ATTEMPT, width=lw + 1)
    elif history:
        last = history[-1][1]
        legs = sorted({h[0] for h in history if h[1] != last})
        shade = {leg: tm.ramp(i, len(legs)) for i, leg in enumerate(legs)}
        # a building or cave entered from the map its door is on is a visit,
        # not a move: on the walk it would draw a spoke to the door and back
        # (a star over every town), so the walk leaves it out
        rows, outside = [], None
        for h in history:
            leg, att, m, xy = (*h, None)[:4]
            if m in pos:
                if m == outside:
                    continue         # back out of a door onto the same street: no move
                outside = m
            elif outside and any(a[0] == outside for a in anc.get(m, [])):
                continue
            rows.append((leg, att, m, xy))
        if not rows:
            rows = [(*history[-1], None)[:4]]
        points = walk([(m, xy) for _, _, m, xy in rows])
        prev = None
        for (leg, att, _, _), q in zip(rows, points):
            if att == last:
                break
            if q and prev and q != prev:
                d.line((prev, q), fill=shade.get(leg, tm.PAST_NEW), width=max(1, lw - 1))
            prev = q or prev
        # the last attempt can collapse away entirely (a gym and its city:
        # every entry a building or the same street again), which means it
        # never left that street: nothing to draw in gold
        first = next((i for i, r in enumerate(rows) if r[1] == last), None)
        if first is not None:
            trail_(points[max(0, first - 1):], tm.LAST_ATTEMPT, lw + 1)
    # the drafts
    drafts = phase.get("drafts") or []
    picked = (phase.get("picked") or {}).get("n")
    origin = pt(here[0], (here[1], here[2]) if here and here[0] in pos else None) if here else \
        (pt(start_map) if start_map else None)
    for dr in [x for x in drafts if x["n"] != picked] + [x for x in drafts if x["n"] == picked]:
        on = dr["n"] == picked
        col = tm.PICKED if on else tm.DRAFT_COLORS[(dr["n"] - 1) % len(tm.DRAFT_COLORS)]
        if picked and not on:
            col = tuple(int(c * 0.55 + 20) for c in col)
        p = trail_([origin] + walk([(m, None) for m in tm.to_ids(dr["route"])], origin),
                  col, lw + (2 if on else 0))
        r = lw + 2
        for x, y in p[1:]:
            d.rectangle((x - r, y - r, x + r, y + r), fill=col)
    # Red: on his cell outdoors, at the door of the cave or building he is in
    if here:
        q = pt(here[0], (here[1], here[2]) if here[0] in pos else None)
        if q:
            spr = player_sprite(max(2.0, scale * 6))       # findable at any zoom (32 px at least)
            img.paste(spr, (q[0] - spr.width // 2, q[1] - spr.height + spr.height // 4), spr)
    return img


# ------- dungeons: a cave's (or tower's, ship's...) floors, side by side

FLOOR = re.compile(r"^(.+?)_(B?\d+F|ROOF|ELEVATOR|EAST|WEST|NORTH|CENTER)(_.*)?$")


DUNGEON_MIN_BLOCKS = 90       # floors' total size: houses, gates and the Museum stay out
# by hand, for watchers (user, 2026-10-03): the three gyms the size rule let in
# and the Underground Path's corridors are not dungeons; the Elite Four's rooms
# are one dungeon run through in order; the Game Corner is the way down into
# the Rocket Hideout. Stitched groups keep the order given, then their floors.
DUNGEON_EXCLUDE = {"CINNABAR_GYM", "SAFFRON_GYM", "VIRIDIAN_GYM", "UNDERGROUND_PATH"}
DUNGEON_STITCH = {
    "ELITE_FOUR": ["LORELEIS_ROOM", "BRUNOS_ROOM", "AGATHAS_ROOM", "LANCES_ROOM", "CHAMPIONS_ROOM"],
    "ROCKET_HIDEOUT": ["GAME_CORNER", "GAME_CORNER_PRIZE_ROOM"],
}


_groups = {}


def dungeons(data):
    """{key: [floor ids]}: every indoor place big enough to be worth a floor
    map. Rooms group by name up to their floor (MT_MOON_1F, MT_MOON_B1F ->
    MT_MOON); a group whose name continues a bigger one joins it (SS_ANNE_BOW
    -> SS_ANNE, DIGLETTS_CAVE_ROUTE_2 -> DIGLETTS_CAVE). A group counts when
    its floors add up to DUNGEON_MIN_BLOCKS: the caves, towers, ship and
    hideout, Silph Co., Celadon Mart and Mansion, and the two puzzle gyms
    (Saffron, Cinnabar), but not the houses, gates or the Museum (user,
    2026-10-03: "i lean towards excluding them because they are generally
    small simple rooms as well, the only ones that break that are celadons
    mart and mansion")."""
    if _groups:
        return _groups
    rooms = data.get("rooms") or {}
    raw = {}
    for r in rooms:
        m = FLOOR.match(r)
        raw.setdefault(m.group(1) if m else r, []).append(r)
    size = {k: sum(rooms[f]["w"] * rooms[f]["h"] for f in v) for k, v in raw.items()}
    for k in sorted(raw, key=len, reverse=True):          # longest names first
        if k.endswith("POKECENTER"):                      # Mt. Moon's Center is on Route 4
            continue
        for h in raw:
            if h != k and k.startswith(h + "_") and size[h] >= DUNGEON_MIN_BLOCKS:
                raw[h] += raw.pop(k)
                size[h] += size.pop(k)
                break

    def order(r):
        # entry first: 1F and up, then the basements going down, then the rest
        f = FLOOR.match(r)
        tag = f.group(2) if f else ""
        n = re.match(r"(B?)(\d+)F", tag)
        if n:
            return (1 if n.group(1) else 0, int(n.group(2)), r)
        return (2, 0, r)
    stitched = {m for ms in DUNGEON_STITCH.values() for m in ms}
    for k, v in raw.items():
        if k in DUNGEON_EXCLUDE or size[k] < DUNGEON_MIN_BLOCKS:
            continue
        v = [r for r in v if r not in stitched]
        if v:
            _groups[k] = sorted(v, key=order)
    for k, members in DUNGEON_STITCH.items():
        _groups[k] = [m for m in members if m in rooms] + [r for r in _groups.get(k, []) if r not in members]
    return _groups


def dungeon_of(data, mid):
    """(key, [floor ids in order]) for a map inside a dungeon, else None."""
    for k, floors in dungeons(data).items():
        if mid in floors:
            return k, floors
    return None


def dungeon_view(data, key, floors, size, path, here, label=None):
    """The dungeon's floors in a grid fitted to `size`, each fogged by its own
    seen cells, the path drawn on each floor cell by cell (broken where it
    climbs a ladder), thin lines from each ladder to where it lands, and Red
    on his floor. `label(img, x, y, text)` names each floor (the HUD passes
    its Game Boy font)."""
    from PIL import ImageDraw
    sys.path.insert(0, HERE)
    import townmap as tm
    seen = read_seen()
    cw = max(data["rooms"][f]["w"] for f in floors) * 32
    chh = max(data["rooms"][f]["h"] for f in floors) * 32 + 40      # room for a label
    best = None
    for cols in range(1, len(floors) + 1):
        rows = -(-len(floors) // cols)
        sc = min(size[0] / (cols * cw), size[1] / (rows * chh))
        if best is None or sc > best[0]:
            best = (sc, cols, rows)
    sc, cols, rows = best
    img = Image.new("RGB", (max(1, int(cols * cw * sc)), max(1, int(rows * chh * sc))), (21, 21, 20))
    d = ImageDraw.Draw(img)
    k = 16 * sc
    origin = {}
    for i, f in enumerate(floors):
        r = data["rooms"][f]
        ox = int((i % cols) * cw * sc + (cw - r["w"] * 32) * sc / 2)
        oy = int((i // cols) * chh * sc + 40 * sc)
        origin[f] = (ox, oy)
        full = room_image(data, f).resize((max(1, int(r["w"] * 32 * sc)), max(1, int(r["h"] * 32 * sc))), Image.BOX)
        dark = full.point(lambda v: int(v * FOG))
        mask = Image.new("L", (r["w"] * 2, r["h"] * 2), 0)
        for x, y in seen.get(f, ()):
            if 0 <= x < r["w"] * 2 and 0 <= y < r["h"] * 2:
                mask.putpixel((x, y), 255)
        img.paste(Image.composite(full, dark, mask.resize(full.size, Image.NEAREST)), (ox, oy))
        name = f[len(key) + 1:] if f.startswith(key + "_") else f
        for other in floors:                   # GAME_CORNER_PRIZE_ROOM -> PRIZE ROOM
            # only by a room stitched in from outside the dungeon's own name:
            # SS_ANNE_1F_ROOMS keeps its 1F
            if other != f and not other.startswith(key) and f.startswith(other + "_"):
                name = f[len(other) + 1:]
        name = re.sub(r"S?_ROOM$", "", name) if name.endswith("S_ROOM") else name   # LORELEIS_ROOM -> LORELEI
        name = name.replace("_", " ")
        if label:
            label(img, ox, max(0, oy - 12), name or key.replace("_", " "), full.width)
        else:
            d.text((ox, max(0, oy - 12)), name, fill=(124, 196, 155))

    def at(f, x, y):
        ox, oy = origin[f]
        return (int(ox + x * k + k / 2), int(oy + y * k + k / 2))
    # every ladder (and door between floors) as a small dot where it stands;
    # a line from floor to floor only where the run actually took one, below
    r_ = max(2, int(k / 3))
    for f in floors:
        for x, y, dest, dw in data["rooms"][f]["warps"]:
            if dest in origin and dest != f:
                cx, cy = at(f, x, y)
                d.ellipse((cx - r_, cy - r_, cx + r_, cy + r_), outline=(150, 170, 186), width=1)
    # the path, floor by floor: steps a cell apart are joined, a jump is a ladder
    lw = max(2, int(k / 3))
    if path:
        last = path[-1][1]
        links = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(links)
        prev = None
        for leg, att, m, x, y, kind in path:
            if m not in origin:
                prev = None
                continue
            q = at(m, x, y)
            col = tm.LAST_ATTEMPT if att == last else tm.PAST_NEW
            if prev and prev[0] == m:
                if kind != "step" or abs(prev[1][0] - q[0]) + abs(prev[1][1] - q[1]) <= 3 * k:
                    d.line((prev[1], q), fill=col, width=lw)
            elif prev:
                # a floor change the run made: a faint line from where it left
                # one floor to where it arrived on the other
                ld.line((prev[1], q), fill=col + (90,), width=max(1, lw // 2))
            prev = (m, q)
        img.paste(links, (0, 0), links)
    if here and here[0] in origin:
        q = at(here[0], here[1], here[2])
        spr = player_sprite(max(2.0, sc * 2))
        img.paste(spr, (q[0] - spr.width // 2, q[1] - spr.height + spr.height // 4), spr)
    return img


def current_dungeon(data, path, here, recent=20):
    """The dungeon this leg is about, if any, and whether it should be the big
    view: the most recent dungeon floor in the path within the current leg;
    big when at least half of the last `recent` points are on its floors (so
    a step through a cave mouth does not swap the view, either way)."""
    if not path:
        here_d = dungeon_of(data, here[0]) if here else None
        return (here_d, True) if here_d else (None, False)
    leg = path[-1][0]
    found = None
    for p in reversed(path):
        if p[0] != leg:
            break
        dd = dungeon_of(data, p[2])
        if dd:
            found = dd
            break
    if not found and here:
        found = dungeon_of(data, here[0])
    if not found:
        return None, False
    floors = set(found[1])
    tail = path[-recent:]
    inside = sum(1 for p in tail if p[2] in floors)
    return found, inside * 2 >= len(tail)


def _cell(key):
    """'ROUTE_4|24,5' -> ('ROUTE_4', 24, 5), or None."""
    try:
        m, xy = key.split("|", 1)
        x, y = xy.split(",")
        return m, int(x), int(y)
    except (AttributeError, ValueError):
        return None


def trail(journal=JOURNAL, crumbs=TRAIL, steps=STEPS):
    """The run's actual path, [(leg, attempt, MAP, x, y)] in order. Before
    breadcrumbs exist it is approximate: the journal's region-to-region moves
    (explored frm -> to), each region pinned to one real cell. From the first
    breadcrumb on (tools/events.py records the player's cell whenever it
    changes) it is cell by cell, straight between two readings. A fresh run
    starts a fresh journal, so the journal is this run; breadcrumbs older than
    it belong to an earlier one and are left out. Finest of all, from the
    first line of run/steps.log on: every cell the shim saw the player stand
    on. Each item carries its source ("hop", "crumb", "step"). Leg and attempt come from
    the journal's plan_start records (leg from the plan's file name, a new
    attempt at every plan_start)."""
    starts, hops, first_t = [], [], None
    leg, attempt = 0, 0
    try:
        with open(journal) as f:
            for line in f:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                t = d.get("t") or 0
                first_t = first_t or t
                k = d.get("kind")
                if k == "plan_start":
                    m = re.match(r"leg_(\d+)", str(d.get("plan") or ""))
                    leg = int(m.group(1)) if m else leg
                    attempt += 1
                    starts.append((t, leg, attempt))
                elif k == "explored":
                    for key in (d.get("frm"), d.get("to")):
                        c = _cell(key)
                        if c:
                            hops.append((t, leg, attempt, *c))
    except OSError:
        pass
    crumbs_ = []
    try:
        with open(crumbs) as f:
            for line in f:
                try:
                    c = json.loads(line)
                except ValueError:
                    continue
                if first_t and c.get("t", 0) >= first_t and c.get("map"):
                    crumbs_.append((c["t"], c["map"], c["x"], c["y"]))
    except OSError:
        pass

    def tag(t):
        lg, at = 0, 0
        for st, l, a in starts:
            if st > t:
                break
            lg, at = l, a
        return lg, at
    steps_ = []
    try:
        with open(steps) as f:
            for line in f:
                parts = line.split()
                if len(parts) == 4:
                    try:
                        t, m, x, y = int(parts[0]), parts[1], int(parts[2]), int(parts[3])
                    except ValueError:
                        continue
                    if first_t and t >= int(first_t):
                        steps_.append((t, m, x, y))
    except OSError:
        pass
    # each source covers the stretch before the next, finer one starts
    step_cut = steps_[0][0] if steps_ else None
    crumb_cut = crumbs_[0][0] if crumbs_ else step_cut
    out = [(lg, at, m, x, y, "hop") for t, lg, at, m, x, y in hops
           if crumb_cut is None or t < crumb_cut]
    out += [(*tag(t), m, x, y, "crumb") for t, m, x, y in crumbs_
            if step_cut is None or t < step_cut]
    out += [(*tag(t), m, x, y, "step") for t, m, x, y in steps_]
    return out


# what the 1x copy shows (tools/shadow), while it is playing: on stream the
# map's "you are here" follows the game on screen, not the 200x run ahead of it
COPY = os.path.expanduser("~/.local/state/red-recomp/shadow_obs.json")
COPY_FRESH_S = 15


def current_obs(path=OBS):
    """The copy's snapshot while it is fresh, else the run's observation."""
    for p in (COPY, path):
        try:
            if p == COPY and time.time() - os.stat(p).st_mtime > COPY_FRESH_S:
                continue
            with open(p) as f:
                return json.load(f)
        except (OSError, ValueError):
            continue
    return None


def where():
    obs = current_obs()
    if obs is None:
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
