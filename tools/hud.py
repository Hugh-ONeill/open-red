#!/usr/bin/env python3
"""Run HUD: the team drawn with its own front pics, the Game Boy font and HP
bars, beside what the executor is doing (run/status.txt: plan, step, goal,
what it thinks, what it is doing, what happened last), redrawn whenever
run/obs.json or run/status.txt changes.

Everything it draws comes from the game's extraction of YOUR ROM
(~/.local/share/love/pokemon-love2d/red/assets/generated/), so nothing is
shipped. It only READS: obs.json, status.txt and the asset folder. Safe beside
a live chain. It replaces `watch -n1 cat run/status.txt`.

  tools/hud.py                 # live, in this kitty window (graphics protocol)
  tools/hud.py --png hud.png   # write one frame and exit
  tools/hud.py --scale 3       # force a scale (default: fit the window)

Made for half a screen beside the game: it reads the kitty window's pixel size,
picks the biggest whole-number scale that fits (team | status side by side, or
team over status in a narrow window) and redraws when the window is resized.

In battle the Pokemon that is out is framed and carries its status (SLP, PSN,
...), and the foe gets a line of its own under the team.

The MODEL line says what the model is doing this second: reading its prompt
(with a bar), writing (tokens so far), THINKING when the executor journalled
think_on for the call in flight, or ACTING while the harness plays. It reads the
ollama service log (journalctl) once a second and the journal's tail. The free
space at the bottom is the EVENTS feed that tools/events.py --follow writes.

It titles its window "red-recomp HUD", which is what Hyprland's `opaque`
rule matches (environment/rules.conf), so run it in any kitty window.
"""
import argparse
import base64
import io
import json
import os
import re
import subprocess
import sys
import textwrap
import time

from PIL import Image

import events as feed     # tools/events.py: the run's event feed
import townmap            # tools/townmap.py: drafts drawn on the Kanto map
import worldmap           # tools/worldmap.py: the whole overworld under the fog

HERE = os.path.dirname(os.path.abspath(__file__))
OBS = os.path.join(HERE, "..", "run", "obs.json")
STATUS = os.path.join(HERE, "..", "run", "status.txt")
TITLE = "red-recomp HUD"
ERROR_LOG = os.path.expanduser("~/.local/state/red-recomp/hud_errors.log")
JOURNAL = os.path.join(HERE, "..", "run", "executor_log.jsonl")
ASSETS = os.path.expanduser(
    "~/.local/share/love/pokemon-love2d/red/assets/generated/")

BG = (21, 21, 20)
FG = (236, 236, 230)
ACCENT = (124, 196, 155)
DIM = (154, 154, 146)
TRACK = (51, 51, 47)
YELLOW = (230, 200, 90)
RED = (227, 138, 115)
CARD = (224, 228, 208)
BADGE_TILE = (40, 45, 42)          # an earned badge's tile: a step up from the background
HPLINE = (200, 206, 196)           # the HP bar's outline, light on the dark card
FRAME = (104, 116, 104)            # the border tiles: quiet, the game's own green-gray

W, ROW, TOP = 248, 80, 22          # the team column (a card: pic, lines, HP, then two lines of moves);
                                   # TOP holds the header with its row of badges
COLS = 46                          # the status column, in 8px characters, when
                                   # nothing asks for more (--png, no window)
MIN_COLS = 36                      # the narrowest status column a fit will use
LINE = 10

# The cartridge's own charmap: font.png is tiles $80-$FF, 16 to a row, and a
# pixel is ink where its palette index is 1.
CHARMAP = {c: 0x80 + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
CHARMAP.update({c: 0xA0 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})
CHARMAP.update({c: 0xF6 + i for i, c in enumerate("0123456789")})
CHARMAP.update({"(": 0x9A, ")": 0x9B, ":": 0x9C, ";": 0x9D, "[": 0x9E,
                "]": 0x9F, "'": 0xE0, "-": 0xE3, "?": 0xE6, "!": 0xE7,
                ".": 0xE8, "/": 0xF3, ",": 0xF4, "♂": 0xEF, "♀": 0xF5,
                "é": 0xBA,                     # the e of POKéMON, as the cartridge draws it
                "\ue0bd": 0xBD})               # the cartridge's own 's tile (RED's), one glyph
# What status.txt prints that the cartridge never needed: drawn in its style,
# one byte per row, leftmost pixel in the high bit.
EXTRA = {
    "_": [0, 0, 0, 0, 0, 0, 0, 0xFE],
    "=": [0, 0, 0x7E, 0, 0x7E, 0, 0, 0],
    ">": [0x20, 0x10, 0x08, 0x04, 0x08, 0x10, 0x20, 0],
    "<": [0x04, 0x08, 0x10, 0x20, 0x10, 0x08, 0x04, 0],
    "|": [0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0],
    "+": [0, 0x10, 0x10, 0x7C, 0x10, 0x10, 0, 0],
    "{": [0x0C, 0x10, 0x10, 0x20, 0x10, 0x10, 0x0C, 0],
    "}": [0x30, 0x08, 0x08, 0x04, 0x08, 0x08, 0x30, 0],
    '"': [0x24, 0x24, 0x48, 0, 0, 0, 0, 0],
    "#": [0x24, 0x7E, 0x24, 0x24, 0x7E, 0x24, 0, 0],
    "%": [0x62, 0x64, 0x08, 0x10, 0x26, 0x46, 0, 0],
    "&": [0x30, 0x48, 0x30, 0x52, 0x4C, 0x3A, 0, 0],
    "*": [0, 0x54, 0x38, 0x7C, 0x38, 0x54, 0, 0],
    "@": [0x3C, 0x42, 0x5A, 0x56, 0x5C, 0x40, 0x3C, 0],
    "~": [0, 0, 0x32, 0x4C, 0, 0, 0, 0],
}
SUBST = {"—": "-", "–": "-", "’": "'", "‘": "'", "“": '"', "”": '"'}

# status.txt fields in the order the column shows them, with how each is drawn.
# PARTY is left out: the team column is the party.
FIELDS = [
    ("PLAN", "PLAN", DIM), ("SUBGOAL", "STEP", FG), ("CARRIED", "CARRIED", YELLOW),
    ("GOAL", "GOAL", FG), ("DONE_WHEN", "DONE WHEN", DIM), ("THINKS", "THINKS", FG),
    ("DOING", "DOING", ACCENT), ("LAST", "LAST", DIM), ("WHERE", "WHERE", DIM),
    ("MONEY", "MONEY", DIM),
]
SKIP = {"PARTY"}


class Painter:
    def __init__(self):
        self.font = Image.open(ASSETS + "fonts/font.png")
        self.glyphs = {}
        self.pics = {}

    def glyph(self, ch):
        if ch not in self.glyphs:
            code = CHARMAP.get(ch)
            if code is not None:
                k = code - 0x80
                g = self.font.crop(((k % 16) * 8, (k // 16) * 8,
                                    (k % 16) * 8 + 8, (k // 16) * 8 + 8))
                self.glyphs[ch] = [(x, y) for y in range(8) for x in range(8)
                                   if g.getpixel((x, y)) == 1]
            elif ch in EXTRA:
                self.glyphs[ch] = [(x, y) for y, row in enumerate(EXTRA[ch])
                                   for x in range(8) if row & (0x80 >> x)]
            else:
                self.glyphs[ch] = []
        return self.glyphs[ch]

    # THE CARTRIDGE'S OWN BOX: the text-box border tiles ($79-$7E in
    # font_extra.png, charmap.asm), the frame of every dialogue and menu.
    BORDER = {"tl": 0x79, "h": 0x7A, "tr": 0x7B, "v": 0x7C, "bl": 0x7D, "br": 0x7E}

    def extra(self, code):
        key = ("x", code)
        if key not in self.glyphs:
            if not hasattr(self, "font_extra"):
                self.font_extra = Image.open(ASSETS + "fonts/font_extra.png")
            k = code - 0x60
            g = self.font_extra.crop(((k % 16) * 8, (k // 16) * 8, (k % 16) * 8 + 8, (k // 16) * 8 + 8))
            self.glyphs[key] = [(x, y) for y in range(8) for x in range(8) if g.getpixel((x, y)) != 0]
        return self.glyphs[key]

    def tile(self, img, x, y, code, col):
        for gx, gy in self.extra(code):
            px, py = x + gx, y + gy
            if 0 <= px < img.width and 0 <= py < img.height:
                img.putpixel((px, py), col)

    def box(self, img, x, y, w, h, col=None, title=None, title_col=None):
        """A Game Boy text box, w x h pixels at (x, y), drawn with the border
        tiles; an edge that is not a whole number of tiles ends on a tile
        pulled back to meet the corner. A title sits in the top edge, the way
        a menu labels its box."""
        col = col or FRAME
        b = self.BORDER
        for xx in list(range(x + 8, x + w - 8, 8)) + [x + w - 16]:
            self.tile(img, xx, y, b["h"], col)
            self.tile(img, xx, y + h - 8, b["h"], col)
        for yy in list(range(y + 8, y + h - 8, 8)) + [y + h - 16]:
            self.tile(img, x, yy, b["v"], col)
            self.tile(img, x + w - 8, yy, b["v"], col)
        self.tile(img, x, y, b["tl"], col)
        self.tile(img, x + w - 8, y, b["tr"], col)
        self.tile(img, x, y + h - 8, b["bl"], col)
        self.tile(img, x + w - 8, y + h - 8, b["br"], col)
        if title:
            tw = 8 * len(title) + 8
            for yy in range(y, y + 8):
                for xx in range(x + 12, min(x + 12 + tw, x + w - 12)):
                    img.putpixel((xx, yy), BG)
            self.text(img, x + 16, y, title, title_col or ACCENT)

    # THE TRAINER CARD'S FRAME: trainer_info.png's 3x3 sheet, laid out as the
    # game's own TrainerCard.lua reads it (0 bottom, 1 right, 2 top-left,
    # 3 top, 4 top-right, 5 left, 6 bottom-left, 7 bottom-right, 8 fill).
    # A pattern made for a white card, so its shades are mapped for a dark one:
    # the white band becomes the background and the texture stays texture.
    CARD_SHADES = {"plain": {170: (112, 124, 112), 85: (66, 74, 68), 0: (40, 44, 42)},
                   "out": {170: (124, 196, 155), 85: (64, 116, 88), 0: (38, 62, 48)},
                   "empty": {170: (66, 72, 68), 85: (44, 48, 46), 0: (32, 35, 34)},
                   "foe": {170: (200, 118, 104), 85: (112, 60, 54), 0: (60, 34, 32)}}

    def card_tiles(self, look):
        key = ("card", look)
        if key not in self.glyphs:
            sheet = Image.open(ASSETS + "trainer_card/trainer_info.png").convert("L")
            shades = self.CARD_SHADES[look]
            tiles = []
            for i in range(9):
                t = sheet.crop(((i % 3) * 8, (i // 3) * 8, (i % 3) * 8 + 8, (i // 3) * 8 + 8))
                tiles.append([(x, y, shades[min(shades, key=lambda s: abs(s - t.getpixel((x, y))))])
                              for y in range(8) for x in range(8) if t.getpixel((x, y)) < 230])
            self.glyphs[key] = tiles
        return self.glyphs[key]

    def card_frame(self, inner, look="plain"):
        """`inner` inside the trainer card's patterned frame, one tile all round."""
        out = Image.new("RGB", (inner.width + 16, inner.height + 16), BG)
        out.paste(inner, (8, 8))
        t = self.card_tiles(look)
        w, h = out.width, out.height

        def put(i, x, y):
            for gx, gy, c in t[i]:
                out.putpixel((x + gx, y + gy), c)
        for x in list(range(8, w - 8, 8)) + [w - 16]:
            put(3, x, 0)
            put(0, x, h - 8)
        for y in list(range(8, h - 8, 8)) + [h - 16]:
            put(5, 0, y)
            put(1, w - 8, y)
        put(2, 0, 0)
        put(4, w - 8, 0)
        put(6, 0, h - 8)
        put(7, w - 8, h - 8)
        return out

    def text(self, img, x, y, s, col=FG):
        for ch in s:
            ch = SUBST.get(ch, ch)
            for gx, gy in self.glyph(ch):
                img.putpixel((x + gx, y + gy), col)
            x += 8

    def text_right(self, img, y, s, col=FG, pad=4, right=W):
        self.text(img, right - 8 * len(s) - pad, y, s, col)

    # THE TRAINER CARD'S BADGES: badges.png is 8 stacked [leader face, badge]
    # 16x16 pairs in the game's order. Earned: the badge on a dark tile in its
    # own shading, lifted to read there; not yet: the outline, faint, so the row reads
    # as eight slots the way the card does.
    BADGE_ORDER = ["BOULDERBADGE", "CASCADEBADGE", "THUNDERBADGE", "RAINBOWBADGE",
                   "SOULBADGE", "MARSHBADGE", "VOLCANOBADGE", "EARTHBADGE"]

    def badge(self, i, earned):
        key = ("badge", i, earned)
        if key not in self.glyphs:
            sheet = Image.open(ASSETS + "trainer_card/badges.png").convert("L")
            b = sheet.crop((0, i * 32 + 16, 16, i * 32 + 32))
            # white is both the badge's background and its highlights: the
            # background is the white reachable from the edge (flood fill)
            outside, todo = set(), [(x, y) for x in range(16) for y in (0, 15)] + \
                [(x, y) for y in range(16) for x in (0, 15)]
            while todo:
                x, y = todo.pop()
                if (x, y) in outside or not (0 <= x < 16 and 0 <= y < 16) or b.getpixel((x, y)) < 250:
                    continue
                outside.add((x, y))
                todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            # the game's own order of shades (outline darkest, highlights
            # brightest), lifted so the outline still shows on the dark tile;
            # turning them over read as a photo negative
            shade = {0: (96, 104, 98), 85: (150, 158, 148), 170: (196, 202, 190), 255: (238, 238, 232)}
            tile = Image.new("RGB", (16, 16), BADGE_TILE if earned else BG)
            for y in range(16):
                for x in range(16):
                    if (x, y) in outside:
                        continue
                    v = b.getpixel((x, y))
                    if earned:
                        tile.putpixel((x, y), shade[min(shade, key=lambda k: abs(k - v))])
                    elif v < 40:
                        tile.putpixel((x, y), (62, 68, 64))
            self.glyphs[key] = tile
        return self.glyphs[key]

    def card(self, species):
        """The front pic on a light card, centred (pics are 40, 48 or 56)."""
        if species not in self.pics:
            name = species.lower().replace(" ", "").replace(".", "")
            card = Image.new("RGB", (52, 52), CARD)
            try:
                pic = Image.open(ASSETS + f"battle/front/{name}.png").convert("RGB")
                pic = pic.point(lambda v: v * 0.88 + 20)
                if pic.width > 50:
                    pic = pic.resize((50, 50), Image.NEAREST)
                card.paste(pic, ((52 - pic.width) // 2, (52 - pic.height) // 2))
            except FileNotFoundError:
                pass
            self.pics[species] = card
        return self.pics[species]

    # THE GAME'S OWN HP BAR (home/pokemon.asm DrawHPBar, via gen1recomp's
    # HudTiles): "HP" $71 + ":[" $62, 8 px cells $63..$6B (n px of fill each),
    # then the cap: $6D double bar on your own side, $6C nub on the foe's.
    # Colour at GetHealthBarColor's thresholds (27 / 10 px of 48), scaled when
    # the bar is stretched over more cells, as the widescreen battle does.
    # The sheet is black outline + one gray fill on white: outline drawn
    # light, fill in the bar colour, white left see-through.
    def hp_tile(self, code):
        key = ("hp", code)
        if key not in self.glyphs:
            if not hasattr(self, "battle_extra"):
                self.battle_extra = Image.open(ASSETS + "battle/font_battle_extra.png").convert("L")
            k = code - 0x62
            t = self.battle_extra.crop(((k % 15) * 8, (k // 15) * 8, (k % 15) * 8 + 8, (k // 15) * 8 + 8))
            self.glyphs[key] = [(x, y, "line" if t.getpixel((x, y)) < 40 else "fill")
                                for y in range(8) for x in range(8) if t.getpixel((x, y)) < 200]
        return self.glyphs[key]

    def hpbar(self, img, x, y, width, frac, cap=0x6D):
        cells = max(1, (width - 24) // 8)
        px = 0 if frac <= 0 else max(1, int(frac * cells * 8))
        green, yellow = -(-27 * cells // 6), -(-10 * cells // 6)
        fill = ACCENT if px >= green else YELLOW if px >= yellow else RED
        cols = {"line": HPLINE, "fill": fill}

        def put(code, tx):
            for gx, gy, kind in self.hp_tile(code):
                img.putpixel((tx + gx, y + gy), cols[kind])
        put(0x71, x)
        put(0x62, x + 8)
        for i in range(cells):
            seg = min(8, max(0, px - i * 8))
            put(0x6B if seg >= 8 else 0x63 + seg, x + 16 + i * 8)
        put(cap, x + 16 + cells * 8)

    def bar(self, img, x, y, w, frac, h=4, col=None):
        """An HP-style bar; `col` pins the colour (progress is not health)."""
        col = col or (ACCENT if frac > 0.5 else YELLOW if frac > 0.2 else RED)
        fill = int(w * max(0.0, min(1.0, frac)))
        for yy in range(h):
            for xx in range(w):
                img.putpixel((x + xx, y + yy), col if xx < fill else TRACK)

    def frame(self, img, x, y, w, h, col):
        for xx in range(x, x + w):
            img.putpixel((xx, y), col)
            img.putpixel((xx, y + h - 1), col)
        for yy in range(y, y + h):
            img.putpixel((x, yy), col)
            img.putpixel((x + w - 1, yy), col)


def draw_moves(img, painter, y, moves):
    """The card's four moves under it, two a line: name and PP left (yellow at
    a quarter or less, red when empty)."""
    colw = (W - 12) // 2                              # two columns, 4 px apart
    for i, m in enumerate(moves[:4]):
        x = 4 + (i % 2) * (colw + 4)
        yy = y + (i // 2) * LINE
        name = str(m.get("id") or m.get("name") or "?").replace("_", " ")
        pp, mx = m.get("pp"), m.get("max_pp")
        tail = "%2d" % pp if isinstance(pp, int) else ""
        ppx = x + colw - 8 * len(tail)                 # PP flush right in its column
        room = (ppx - x - 6) // 8                      # a name stops short of it
        if len(name) > room:
            name = name[:room - 1] + "."
        painter.text(img, x, yy, name, FG if (pp or 0) > 0 or pp is None else DIM)
        if tail:
            col = RED if pp == 0 else YELLOW if mx and pp * 4 <= mx else DIM
            painter.text(img, ppx, yy, tail, col)


CARD_H = ROW + 16                  # a card in its trainer-card frame, and a 2 px gap
FOE_H = 12 + 56 + 16               # "FOE", then its framed card


def render_team(obs, painter):
    """The team as six trainer-card-framed cards (W + 16 wide)."""
    party = obs.get("party") or []
    battle = obs.get("battle") if isinstance(obs.get("battle"), dict) else None
    me = (battle or {}).get("me") or {}
    foe = (battle or {}).get("foe") or {}
    out_slot = me.get("slot")          # 1-based party slot of the mon that is out
    tw = W + 16
    height = TOP + CARD_H * 6 + (FOE_H if foe else 0)
    img = Image.new("RGB", (tw, height), BG)

    have = set(obs.get("badges") or [])
    name = str(obs.get("player_name") or "").strip()[:7]
    painter.text(img, 4, 7, (name + "\ue0bd TEAM") if name else "TEAM", ACCENT)
    for i, name in enumerate(painter.BADGE_ORDER):
        img.paste(painter.badge(i, name in have), (tw - 8 * 18 - 2 + i * 18, 3))

    for i in range(6):
        c = Image.new("RGB", (W, ROW - 2), BG)
        y = 0
        if i >= len(party):
            painter.text(c, 58, y + 24, "-", DIM)
            img.paste(painter.card_frame(c, "empty"), (0, TOP + i * CARD_H))
            continue
        p = party[i]
        c.paste(painter.card(p["species"]), (3, y + 2))
        is_out = out_slot == i + 1
        hp, max_hp = p.get("hp", 0), p.get("max_hp") or 1
        status = me.get("status") if is_out else None
        if is_out:
            hp = me.get("hp", hp)
        painter.text(c, 58, y + 6, (p.get("nickname") or p["species"])[:10])
        painter.text(c, 58, y + 16, p["species"][:10], DIM)
        painter.text_right(c, y + 6, ":L%d" % p.get("level", 0), ACCENT)
        if hp <= 0:
            painter.text_right(c, y + 16, "FNT", RED)
        elif status:
            painter.text_right(c, y + 16, str(status)[:3], YELLOW)
        painter.hpbar(c, 58, y + 28, W - 58 - 2, hp / max_hp, cap=0x6C)   # the nub, as on the foe
        painter.text(c, 58, y + 38, "/".join(t[:3] for t in p.get("types") or []), DIM)
        painter.text_right(c, y + 38, "%d/%d" % (hp, max_hp), DIM)
        draw_moves(c, painter, y + 57, p.get("moves") or [])
        # the one that is out in battle gets its frame in the accent colour
        img.paste(painter.card_frame(c, "out" if is_out else "plain"), (0, TOP + i * CARD_H))

    if foe:
        y = TOP + CARD_H * 6
        painter.text(img, 4, y + 2, "FOE", RED)
        c = Image.new("RGB", (W, 56), BG)
        c.paste(painter.card(foe.get("species") or "?"), (3, 2))
        painter.text(c, 58, 6, (foe.get("species") or "?")[:10])
        if foe.get("level"):
            painter.text_right(c, 6, ":L%s" % foe["level"], RED)
        if foe.get("status"):
            painter.text_right(c, 16, str(foe["status"])[:3], YELLOW)
        frac = (foe.get("hp") or 0) / (foe.get("maxhp") or 1)
        painter.hpbar(c, 58, 30, W - 58 - 2, frac, cap=0x6C)   # Red shows the foe no HP numbers
        img.paste(painter.card_frame(c, "foe"), (0, y + 12))
    return img


# ------- status.txt

LABEL = re.compile(r"^([A-Z][A-Z_]+)(?=[\s{\[]|$)\s*(.*)$")


def parse_status(text):
    """status.txt as {label: value}: a label starts a line in capitals, its
    value may wrap onto indented lines; the trailing `t+Ns` is how long this
    executor process had been running when it wrote the file."""
    fields, order, age, cur = {}, [], None, None
    for line in text.splitlines():
        if not line.strip():
            continue
        m = LABEL.match(line)
        if m and not line.startswith(" "):
            cur = m.group(1)
            fields[cur] = m.group(2).strip()
            order.append(cur)
        elif re.match(r"^t\+\d+s$", line.strip()):
            age = line.strip()[2:]
        elif cur:
            fields[cur] += " " + line.strip()
    return fields, order, age


def tidy(label, value):
    """JSON the executor prints for itself, read out for a person."""
    if label == "PLAN":
        m = re.match(r"leg_(\d+)_(.+?)(?:\.(v\d+))?\.json$", value)
        if m:
            words_ = m.group(2).replace("_", " ")
            # the file name lost its é (pick_a_starter_pok_mon): put it back
            # where Red spells it, Pokémon / Poké Ball / Poké Mart / Pokédex
            words_ = re.sub(r"\bpok (mon|ball|balls|mart|dex|center|flute)\b", r"poké\1", words_)
            words_ = re.sub(r"\bpoké(ball|balls|mart|center|flute)\b", r"poké \1", words_)
            return "leg %d: %s%s" % (int(m.group(1)), words_,
                                     " (%s)" % m.group(3) if m.group(3) else "")
    value = re.sub(r'"([^"]*)":\s*', r"\1 ", value)       # "key": x -> key x
    value = value.replace('"', "").replace("{", "").replace("}", "")
    value = re.sub(r"\[\s*", "", value)
    value = re.sub(r"\s*\]", "", value)
    return re.sub(r"\s+", " ", value).strip()


def clock(sec):
    sec = int(sec)
    if sec < 60:
        return "%ds" % sec
    if sec < 3600:
        return "%dm%02ds" % divmod(sec, 60)
    return "%dh%02dm" % (sec // 3600, sec % 3600 // 60)


def file_age(path):
    try:
        return max(0, time.time() - os.stat(path).st_mtime)
    except OSError:
        return None


# ------- what the model is doing right now

def tail_lines(path, nbytes=65536):
    """The last complete lines of a file, read from its end."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - nbytes))
            chunk = f.read().decode("utf-8", "replace")
    except OSError:
        return []
    lines = chunk.splitlines()
    return lines[1:] if size > nbytes else lines     # the first may be cut


def thinking_pending():
    """True while a thinking call is out: the executor journals think_on just
    before one and escalate_proposal / think_logged just after it."""
    for line in reversed(tail_lines(JOURNAL)):
        if '"think_on"' in line:
            return True
        if '"escalate_proposal"' in line or '"think_logged"' in line:
            return False
    return False


GEN = re.compile(r"n_gen =\s*(\d+), tg =\s*([\d.]+)")
PROG = re.compile(r"prompt processing, n_tokens =\s*(\d+), progress = ([\d.]+)")


def model_activity():
    if not VIEW["live"]:
        return {"phase": "idle", "since": None}      # the copy is showing play, not the model now
    return _model_activity()


def _model_activity():
    """The model's current call, from the ollama service log: None when the
    log cannot be read, else a dict with phase reading / writing / idle."""
    try:
        out = subprocess.run(
            ["journalctl", "-u", "ollama", "-n", "400", "-o", "short-unix",
             "--no-pager", "-q"], capture_output=True, text=True, timeout=3).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    cur = None
    for line in out.splitlines():
        head, _, msg = line.partition(" ")
        try:
            t = float(head)
        except ValueError:
            continue
        if "launch_slot_" in msg and "processing task" in msg:
            cur = {"start": t}
        elif cur is None:
            continue
        elif "new prompt" in msg:
            m = re.search(r"task.n_tokens = (\d+)", msg)
            cur["ptok"] = int(m.group(1)) if m else None
        elif "prompt processing" in msg:
            m = PROG.search(msg)
            if m:
                cur["progress"] = float(m.group(2))
        elif "n_gen =" in msg:
            m = GEN.search(msg)
            if m:
                cur["ngen"], cur["tps"] = int(m.group(1)), float(m.group(2))
        elif "stop processing" in msg:
            cur["end"] = t
    if cur is None:
        return {"phase": "idle", "since": None}
    now = time.time()
    if "end" in cur:
        return {"phase": "idle", "since": now - cur["end"]}
    act = {"phase": "writing" if "ngen" in cur else "reading",
           "elapsed": now - cur["start"], "progress": cur.get("progress", 0.0),
           "ngen": cur.get("ngen", 0), "tps": cur.get("tps"), "ptok": cur.get("ptok")}
    act["thinking"] = thinking_pending()
    return act


def activity_key(act):
    """What of the activity is worth a redraw (coarse, so it is not every poll)."""
    if not act:
        return None
    if act["phase"] == "idle":
        return ("idle", int((act.get("since") or 0) // 5))
    return (act["phase"], act.get("thinking"), int(act["progress"] * 20),
            act["ngen"] // 25, int(act["elapsed"] // 5))


def draw_activity(img, painter, y, act):
    """One line: MODEL and what it is doing, with a bar while it reads."""
    painter.text(img, 4, y, "MODEL", ACCENT)
    x = 52
    if act is None:
        painter.text(img, x, y, "log unreadable", DIM)
        return
    if act["phase"] == "idle":
        since = act.get("since")
        painter.text(img, x, y, "ACTING", ACCENT)
        if since is not None:
            painter.text(img, x + 56, y, "(idle %s)" % clock(since), DIM)
        return
    tag, col = ("THINKING", RED) if act.get("thinking") else (None, None)
    if tag:
        painter.text(img, x, y, tag, col)
        x += 8 * len(tag) + 8
    if act["phase"] == "reading":
        label = "reading %d%%" % round(100 * act["progress"])
        painter.text(img, x, y, label, YELLOW if not tag else DIM)
        bx = x + 8 * len(label) + 8
        bw = img.width - bx - 8 * 7
        if bw > 16:
            painter.bar(img, bx, y + 2, bw, act["progress"], h=4, col=YELLOW)
    else:
        label = "writing %d tok" % act["ngen"]
        if act.get("tps"):
            label += " %d/s" % round(act["tps"])
        painter.text(img, x, y, label, FG)
    painter.text_right(img, y, clock(act["elapsed"]), DIM, right=img.width)


TONE = {"good": ACCENT, "bad": RED, "think": YELLOW, "info": FG}


def bottom_panel(img, painter, y0, height, cols, title, title_col, blocks, right=None):
    """The column's lower panel in its own text box: `blocks` are lists of
    (stamp, text, colour) rows, one list per item so none is cut in half;
    as many as fit, newest at the bottom. The title sits in the top border,
    `right` (if any) at the top border's right end."""
    room = (height - y0 - 24) // LINE
    if room < 2:
        return
    shown = []
    for block in reversed(blocks):
        if len(shown) + len(block) > room:
            break
        shown = block + shown
    bh = LINE * max(len(shown), 1) + 24
    by = height - bh
    painter.box(img, 0, by, img.width, bh, title=title, title_col=title_col)
    if right:
        tx = img.width - 12 - 8 * len(right) - 4
        for yy in range(by, by + 8):
            for xx in range(tx - 4, img.width - 12):
                img.putpixel((xx, yy), BG)
        painter.text(img, tx, by, right, DIM)
    y = by + 12
    if not shown:
        return
    for stamp, text, col in shown:
        if stamp:
            painter.text(img, 12, y, stamp, DIM)
            painter.text(img, 12 + 6 * 8, y, text, col)
        else:
            painter.text(img, 12 if stamp is None else 12 + 6 * 8, y, text, col)
        y += LINE


def _stamped(entries, cols, max_lines=None):
    blocks = []
    for e in entries:
        stamp = time.strftime("%H:%M", time.localtime(e.get("t", 0)))
        wrapped = textwrap.wrap(e.get("text", ""), cols - 9) or [""]
        if max_lines:
            wrapped = wrapped[:max_lines]
        col = TONE.get(e.get("tone"), FG)
        blocks.append([(stamp, wrapped[0], col)] + [("", w, col) for w in wrapped[1:]])
    return blocks


def draw_live(img, painter, y0, height, cols, lc):
    """The words of the call in flight (brock_probe streams them to
    run/model_live.txt, or thinking_live.txt for a thinking call), newest
    lines at the bottom, headed by what kind of call it is."""
    text, started = lc["text"], lc["started"]
    lines = []
    for para in text.splitlines():
        if re.match(r"^\s*```\s*\w*\s*$", para):      # a code fence is not content
            continue
        para = re.sub(r"[`*#]+", "", para)
        if para.strip():
            lines += textwrap.wrap(para.strip(), cols - 3)
    who = (lc.get("who") or "").upper()
    kind = ("THINKING" if lc.get("think") else
            "DRAFTING" if "AUTHOR A PLAN" in who else
            "REVIEWING" if "REVIEW" in who else
            "PICKING" if "PICK" in who or "JUDGE" in who else "WRITING")
    bottom_panel(img, painter, y0, height, cols, kind + ", LIVE", YELLOW,
                 [[(None, l, FG)] for l in lines],
                 right="%s %d chars" % (clock(time.time() - started), len(text)))


def draw_author_log(img, painter, y0, height, cols, log):
    """While a plan is written: the author's own narration from chain.log
    (rounds the validator sent back and why, what the review changed), newest
    at the bottom. The ollama line above says how far the current call is."""
    bottom_panel(img, painter, y0, height, cols, "AUTHOR AT WORK", YELLOW,
                 _stamped(log, cols, max_lines=4))


def draw_events(img, painter, y0, height, cols):
    """The event feed (tools/events.py) in the column's free space, newest at
    the bottom like a chat, as many as fit."""
    blocks = _stamped(feed.last_events(40, min_level=2, until=VIEW["t"]), cols)
    if not blocks:
        blocks = [[(None, "none yet (tools/events.py --follow)", DIM)]]
    bottom_panel(img, painter, y0, height, cols, "EVENTS", ACCENT, blocks)


def draw_authoring(img, painter, y, height, cols, phase):
    """While the model writes a plan the game is closed and status.txt stands
    still, so the column shows the writing: the goal, each draft's route and
    the one picked, with why."""
    what = "REWRITING FROM WHAT IT WALKED" if phase.get("what") == "rewrite" else \
        "WRITING A PLAN" + (" FOR LEG %s" % phase["leg"] if phase.get("leg") else "")
    painter.text(img, 4, y, what, YELLOW)
    painter.text_right(img, y, clock(time.time() - phase.get("since", time.time())), DIM,
                       right=img.width)
    y += LINE + 4
    if phase.get("goal"):
        painter.text(img, 4, y, "GOAL", ACCENT)
        y += LINE
        for line in textwrap.wrap(phase["goal"], cols - 1):
            painter.text(img, 12, y, line, FG)
            y += LINE
        y += 4
    picked = (phase.get("picked") or {}).get("n")
    drafts = phase.get("drafts") or []
    if drafts:
        painter.text(img, 4, y, "DRAFTS", ACCENT)
        y += LINE
    for d in drafts:
        if y + 2 * LINE > height:
            break
        on = d["n"] == picked
        col = townmap.PICKED if on else townmap.DRAFT_COLORS[(d["n"] - 1) % len(townmap.DRAFT_COLORS)]
        if picked and not on:
            col = tuple(int(c * 0.55 + 20) for c in col)    # as the map fades them
        # one line a draft: the map beside it draws the whole route, and the
        # room below is the author's own narration
        head = "%s%d %2d steps  " % (">" if on else " ", d["n"], d["steps"])
        route = d["route"].replace(" -> ", ">")
        room = cols - len(head) - 1
        painter.text(img, 4, y, head + (route if len(route) <= room else route[:room - 3] + "..."), col)
        y += LINE
    if not drafts:
        painter.text(img, 12, y, "drafting...", DIM)
        y += LINE
    # the map's key: the trail colors are not the drafts'
    y += 2
    painter.text(img, 4, y, "MAP", ACCENT)
    x = 44
    for swatches, label in (((townmap.PAST_OLD, townmap.PAST_NEW), "earlier legs"),
                            ((townmap.LAST_ATTEMPT,), "last attempt")):
        for col in swatches:
            for yy in range(3, 7):
                for xx in range(8):
                    img.putpixel((x + xx, y + yy), col)
            x += 10
        painter.text(img, x + 2, y, label, DIM)
        x += 8 * len(label) + 14
    y += LINE + 2
    if phase.get("picked"):
        y += 4
        painter.text(img, 4, y, "PICKED %d OF %d" % (picked, phase["picked"]["of"]), ACCENT)
        y += LINE
        for line in textwrap.wrap(phase["picked"].get("why", ""), cols - 1)[:3]:
            painter.text(img, 12, y, line, DIM)
            y += LINE
    return y + 4


# what a fresh run looks like before its game boots: nobody in the party
NEW_RUN = {"party": [], "new_run": True}


def render_status(text, painter, height, cols=COLS, act=None):
    img = Image.new("RGB", (cols * 8 + 8, height), BG)
    # no status.txt yet: a fresh run is writing its first plan before the
    # game boots. Draw the header, the model line and the authoring box all
    # the same; only the playing fields are missing (user, 2026-10-03:
    # "the start just shows 'no status yet'").
    fields, order, elapsed = parse_status(text or "")
    known = {k for k, _, _ in FIELDS}
    rows = [(k, lab, col) for k, lab, col in FIELDS if fields.get(k)]
    rows += [(k, k.replace("_", " "), DIM) for k in order
             if k not in known and k not in SKIP and fields.get(k)]
    y = 4
    painter.text(img, 4, y, "RUN", ACCENT)
    if elapsed:
        painter.text(img, 40, y, "t+" + clock(int(elapsed[:-1])), DIM)
    age = file_age(STATUS) if text is not None else None
    if text is None:
        painter.text_right(img, y, "no game yet", DIM, right=img.width)
    elif age is not None:
        painter.text_right(img, y, "updated %s ago" % clock(age), YELLOW if age > 120 else DIM,
                           right=img.width)
    y += LINE + 4
    draw_activity(img, painter, y, act)
    y += LINE + 6
    phase = phase_now() or {}
    if phase.get("phase") == "authoring":
        y = draw_authoring(img, painter, y, height, cols, phase)
        rows = []                      # the playing fields are stale meanwhile
    for key, label, col in rows:
        if y + 2 * LINE > height:
            painter.text(img, 4, height - LINE, "...", DIM)
            break
        painter.text(img, 4, y, label, ACCENT if col is not ACCENT else DIM)
        y += LINE
        for line in textwrap.wrap(tidy(key, fields[key]), cols - 1) or [""]:
            if y + LINE > height:
                break
            painter.text(img, 12, y, line, col)
            y += LINE
        y += 4
    lc = feed.live_call() if VIEW["live"] else None
    if lc and not lc["done"] and (lc["think"] or phase.get("phase") == "authoring"):
        # a thinking call anywhere, or any call while a plan is written:
        # the words as they come (a plain round is too quick to be worth it)
        draw_live(img, painter, y + 8, height, cols, lc)
    elif phase.get("phase") == "authoring" and phase.get("log"):
        draw_author_log(img, painter, y + 8, height, cols, phase["log"])
    else:
        draw_events(img, painter, y + 8, height, cols)
    return img


GUTTER = 8


FR = 8                                   # one border tile


def framed(inner, painter, title=None):
    """A panel inside the cartridge's text-box border, one tile all round."""
    out = Image.new("RGB", (inner.width + 2 * FR, inner.height + 2 * FR), BG)
    out.paste(inner, (FR, FR))
    painter.box(out, 0, 0, out.width, out.height, title=title)
    return out


def side_width(cols):
    return (W + 2 * FR) + GUTTER + (cols * 8 + 8 + 2 * FR)     # [team] [status]


def stack_width(cols):
    return max(W, cols * 8 + 8) + 2 * FR                      # [team] over [status]


def render(obs, status_text, painter, layout="side", height=None, width=None,
           act=None):
    """layout "side": team | status, both `height` tall (at least the team's).
    layout "stack": team over status, the status filling down to `height`.
    `width` (1x pixels) widens the status column to fill it; the team column
    keeps its size, since its rows have nothing more to say."""
    if layout == "world":
        # authoring, the hybrid: the whole overworld under the fog takes the
        # game's place (caves and buildings at their doors). Drawn at the
        # window's own size after the HUD is scaled (frame_bytes), so the box
        # here is left empty and its place remembered.
        cols = COLS if (width or 0) >= 900 else MIN_COLS
        col = framed(render_status(status_text, painter, (height or 456) - 2 * FR, cols, act), painter)
        h = col.height
        mw = max(200, (width or 900) - col.width - GUTTER)
        img = Image.new("RGB", (mw + GUTTER + col.width, h), BG)
        painter.box(img, 0, 0, mw, h, title="KANTO")
        img.paste(col, (mw + GUTTER, 0))
        global WORLD_BOX
        WORLD_BOX = (FR, FR + 4, mw - 2 * FR, h - 2 * FR - 4)
        return img
    if layout.startswith("map"):
        # authoring: the game is closed, so the town map with the drafts on it
        # takes the game's place, beside the authoring column (the team does
        # not change while a plan is written)
        k = int(layout[3:] or 2)
        start = ((obs or {}).get("map") or {}).get("id")
        tm = framed(townmap.render(phase_now() or {}, start, k), painter, "KANTO")
        mw = tm.width + 4
        rest = (width or mw + GUTTER + COLS * 8 + 8 + 2 * FR) - mw - GUTTER
        cols = max(MIN_COLS, (rest - 8 - 2 * FR) // 8)
        h = max(tm.height + 8, height or 0)
        col = framed(render_status(status_text, painter, h - 2 * FR, cols, act), painter)
        img = Image.new("RGB", (max(mw + GUTTER + col.width, width or 0), h), BG)
        img.paste(tm, (4, (h - tm.height) // 2))
        img.paste(col, (mw + GUTTER, 0))
        return img
    if layout == "stack":
        team = render_team(obs, painter)          # its cards carry their own frames
        cols = max(MIN_COLS, ((width or stack_width(COLS)) - 8 - 2 * FR) // 8)
        rest = max((height or 0) - team.height, 30 * LINE)
        col = framed(render_status(status_text, painter, rest - 2 * FR, cols, act), painter)
        img = Image.new("RGB", (max(stack_width(cols), width or 0), team.height + col.height), BG)
        img.paste(team, (0, 0))
        img.paste(col, (0, team.height))
        return img
    inner_team = render_team(obs, painter)        # W + 16 wide, cards framed
    cols = max(MIN_COLS, ((width or side_width(COLS)) - (W + 2 * FR) - GUTTER - 8 - 2 * FR) // 8)
    h = max(inner_team.height, height or 0)
    team = Image.new("RGB", (inner_team.width, h), BG)
    team.paste(inner_team, (0, 0))
    col = framed(render_status(status_text, painter, h - 2 * FR, cols, act), painter)
    img = Image.new("RGB", (max(side_width(cols), width or 0), h), BG)
    img.paste(team, (0, 0))
    img.paste(col, (team.width + GUTTER, 0))
    return img


def window_pixels():
    """The kitty window's size in pixels (TIOCGWINSZ), or None."""
    try:
        import fcntl
        import struct
        import termios
        rows, cols, xpx, ypx = struct.unpack(
            "HHHH", fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, b"\0" * 8))
        return (xpx, ypx) if xpx and ypx else None
    except OSError:
        return None


WORLD_BOX = None
_world_cache = {}


def fit_world(win):
    """Authoring, the hybrid: the biggest text scale that leaves the overworld
    a box at least 480 px across beside a minimum-width status column."""
    xpx, ypx = win
    for scale in (3, 2, 1):
        col = (MIN_COLS * 8 + 8 + 2 * FR) * scale
        if xpx - col - GUTTER * scale >= 480 and ypx // scale >= 30 * LINE:
            return "world", scale, ypx // scale, xpx // scale
    return None


_label_painter = []


def _label(img, x, y, text, width=None):
    """A floor's name on a dungeon view in the Game Boy font, as big as fits
    over its floor: 2x where there is room, 1x in a small inset, cut short
    only when even that does not fit."""
    if not _label_painter:
        _label_painter.append(Painter())
    t = text.upper()
    width = width or img.width - x
    k = 2 if 8 * len(t) * 2 <= width else 1
    t = t[:max(1, width // (8 * k))]
    small = Image.new("RGB", (8 * len(t) + 2, 9), BG)
    _label_painter[0].text(small, 1, 0, t, ACCENT)
    big = small.resize((small.width * k, small.height * k), Image.NEAREST)
    img.paste(big, (x, max(0, y - 9 * k + 10)))


def world_view(size):
    """The picture for the KANTO box at `size` real pixels. Outside a dungeon:
    the overworld. Around one (this leg went into Mt. Moon, Silph Co., ...):
    both, the one the party has mostly been in over its last steps big and
    the other as an inset in the corner, so stepping through a cave mouth
    never swaps the view and the way in or out stays on screen (user,
    2026-10-03, on swapping views: "the awkward exit also comes with an
    awkward entrance"). Drawn again only when what it shows changed."""
    phase = phase_now() or {}
    hist = townmap.run_history()
    here = worldmap.where()
    data = worldmap.load()
    path = worldmap.trail(until=VIEW["t"])   # no further than the copy has played
    dg, dungeon_big = worldmap.current_dungeon(data, path, here)
    try:
        seen_t = os.stat(worldmap.SEEN).st_mtime_ns
    except OSError:
        seen_t = 0
    key = json.dumps([phase.get("drafts"), phase.get("picked"), len(hist), len(path), here, size,
                      seen_t, dg[0] if dg else None, dungeon_big])
    if _world_cache.get("key") == key:
        return _world_cache["img"]
    start = (here or [None])[0]

    def over(sz):
        return worldmap.authoring_view(phase, hist, here, sz, start_map=start, until=VIEW["t"])

    def cave(sz):
        return worldmap.dungeon_view(data, dg[0], dg[1], sz, path, here, label=_label)
    if not dg:
        img = over(size)
    else:
        main, side = (cave, over) if dungeon_big else (over, cave)
        img = Image.new("RGB", size, BG)
        m = main(size)
        img.paste(m, ((size[0] - m.width) // 2, (size[1] - m.height) // 2))
        iw, ih = int(size[0] * 0.36), int(size[1] * 0.36)
        inset = side((iw, ih))
        x0, y0 = size[0] - inset.width - 6, size[1] - inset.height - 6
        frame = Image.new("RGB", (inset.width + 6, inset.height + 6), FRAME)
        frame.paste(Image.new("RGB", (inset.width + 2, inset.height + 2), BG), (2, 2))
        frame.paste(inset, (3, 3))
        img.paste(frame, (x0 - 3, y0 - 3))
    _world_cache.update(key=key, img=img)
    return img


def fit_map(win):
    """Authoring layout: the town map at k times the Game Boy's size beside the
    status column, k and the screen scale chosen for the biggest map on screen
    (then the bigger scale, for the text)."""
    xpx, ypx = win
    best = None
    for k in (2, 1):
        width = townmap.W * k + 2 * FR + 4 + GUTTER + MIN_COLS * 8 + 8 + 2 * FR
        min_h = max(townmap.H * k + 2 * FR + 8, 30 * LINE)
        scale = min(xpx // width, ypx // min_h)
        if scale >= 1:
            key = (k * scale, scale)
            if best is None or key > best[0]:
                best = (key, k, scale)
    if best is None:
        return None
    _, k, scale = best
    return "map%d" % k, scale, ypx // scale, xpx // scale


def fit(win, team_h):
    """Pick the layout and whole-number scale that fill the window best (whole
    numbers keep the pixels square; side by side wins a tie), sized against the
    NARROWEST status column, which then widens to take the rest of the width.
    Returns (layout, scale, height, width), height and width at 1x."""
    if not win:
        return "side", 2, None, None
    xpx, ypx = win
    best = None
    for layout, width, min_h in (("side", side_width(MIN_COLS), team_h),
                                 ("stack", stack_width(MIN_COLS), team_h + 20 * LINE)):
        scale = min(xpx // width, ypx // min_h)
        if scale >= 1 and (best is None or scale > best[1]):
            best = (layout, scale)
    layout, scale = best or ("side", 1)
    return layout, scale, ypx // scale, xpx // scale


def read_obs():
    # THE GAME ON SCREEN, NOT THE ONE AHEAD OF IT. On stream the 200x run is
    # hidden and the 1x copy (tools/shadow) is what viewers watch, so the
    # team, badges and battle come from the copy's snapshot while it is
    # fresh; the run's obs.json otherwise (no copy, or the copy idle while
    # the model authors, when the two agree). The shim rewrites obs.json in
    # place; a half-written file is skipped and the next change picks it up.
    obs = worldmap.current_obs(OBS)
    # ...AND THE WORDS BESIDE IT FROM THE SAME MOMENT. The copy says which
    # second of the run it is showing (run_t); the status, the phase and the
    # events are then read as they stood at that second, so the HUD never
    # announces a fight the screen has not reached. Within LIVE_S of now the
    # copy has caught up, and the live model line comes back.
    t = (obs or {}).get("run_t") if (obs or {}).get("source") == "copy" else None
    VIEW["t"] = t
    VIEW["live"] = t is None or time.time() - t < LIVE_S
    return obs


VIEW = {"t": None, "live": True}
LIVE_S = 20


def phase_now():
    if VIEW["t"] is not None:
        p = feed.phase_at(VIEW["t"])
        if p is not None:
            return p
    return feed.read_phase()


def read_status():
    if VIEW["t"] is not None:
        past = feed.status_at(VIEW["t"])
        if past is not None:
            return past
    try:
        with open(STATUS) as f:
            return f.read()
    except OSError:
        return None


_shown_id = [0]


def kitty_show(png_bytes):
    """Show a frame at the top-left through kitty's graphics protocol,
    DOUBLE-BUFFERED: the new frame goes up under the other image id and only
    then is the old one deleted. Deleting first left the window empty while a
    big frame (the overworld map) was still on its way, and it flashed."""
    old = _shown_id[0]
    new = 2 if old == 1 else 1
    data = base64.b64encode(png_bytes).decode()
    out = ["\x1b[H"]
    chunks = [data[i:i + 4096] for i in range(0, len(data), 4096)] or [""]
    for n, chunk in enumerate(chunks):
        more = 1 if n < len(chunks) - 1 else 0
        head = f"a=T,f=100,i={new},C=1,q=2," if n == 0 else ""
        out.append(f"\x1b_G{head}m={more};{chunk}\x1b\\")
    if old:
        out.append(f"\x1b_Ga=d,d=i,i={old},q=2\x1b\\")
    sys.stdout.write("".join(out))
    sys.stdout.flush()
    _shown_id[0] = new


def stamp_of(path):
    try:
        return os.stat(path).st_mtime_ns
    except OSError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--png", help="write one frame to this file and exit")
    ap.add_argument("--scale", type=int, help="force a scale (default: fit the window)")
    ap.add_argument("--poll", type=float, default=0.25, help="seconds between checks")
    args = ap.parse_args()
    painter = Painter()

    def frame_bytes(obs, status_text, win=None, act=None):
        team_h = TOP + CARD_H * 6 + FOE_H              # room for a battle's foe card too
        phase = phase_now() or {}
        fitted = (fit_world(win) or fit_map(win)) if (win and phase.get("phase") == "authoring") else None
        layout, scale, height, width = fitted or fit(win, team_h)
        if args.scale:
            scale = args.scale
            height, width = (win[1] // scale, win[0] // scale) if win else (None, None)
        img = render(obs, status_text, painter, layout, height, width, act)
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        if layout == "world" and WORLD_BOX:
            bx, by, bw, bh = (v * scale for v in WORLD_BOX)
            view = world_view((bw, bh))
            img.paste(view, (bx + (bw - view.width) // 2, by + (bh - view.height) // 2))
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return buf.getvalue()

    if args.png:
        obs = read_obs()
        if obs is None and not os.path.exists(OBS) and read_status() is None:
            obs = NEW_RUN
        if obs is None:
            sys.exit(f"cannot read {OBS}")
        with open(args.png, "wb") as f:
            f.write(frame_bytes(obs, read_status(), act=model_activity()))
        return

    if os.environ.get("TERM") != "xterm-kitty":
        print("warning: not a kitty window; the image may not show "
              "(inside tmux, kitty graphics need allow-passthrough)", file=sys.stderr)
    # name the window, so Hyprland's rule (match:title ^red-recomp HUD$,
    # opaque on) finds it in whatever kitty it was started from
    sys.stdout.write("\x1b]2;%s\x07" % TITLE)
    sys.stdout.write("\x1b[2J\x1b[?25l")    # clear, hide the cursor
    last, obs, act, act_at = None, None, None, 0.0
    try:
        while True:
            win = window_pixels()
            if time.time() - act_at >= 1.0:        # the service log, once a second
                act, act_at = model_activity(), time.time()
            # the age tick repaints "updated Ns ago" every 5 s even when idle
            stamps = (stamp_of(OBS), stamp_of(worldmap.COPY), stamp_of(STATUS), stamp_of(feed.FEED), stamp_of(feed.PHASE),
                      stamp_of(feed.LIVE), stamp_of(feed.MODEL_LIVE), win,
                      int(time.time()) // 5, activity_key(act))
            if stamps != last:
                fresh = read_obs()
                if fresh is None and not os.path.exists(OBS) and read_status() is None:
                    # neither file at all is a fresh run (fresh_discovery clears
                    # both), not a write in progress: drop the old run's team
                    fresh = NEW_RUN
                obs = fresh if fresh is not None else obs
                if obs is not None:
                    # A FRAME THAT FAILS MUST NOT TAKE THE HUD DOWN. Whatever the
                    # run throws at it (a new badge left the world map's trail
                    # empty, 2026-10-01), the last good frame stays up, the
                    # traceback goes to a log, and the next change tries again.
                    try:
                        kitty_show(frame_bytes(obs, read_status(), win, act))
                    except (BrokenPipeError, KeyboardInterrupt):
                        raise
                    except Exception:
                        import traceback
                        try:
                            os.makedirs(os.path.dirname(ERROR_LOG), exist_ok=True)
                            with open(ERROR_LOG, "a") as f:
                                f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + traceback.format_exc() + "\n")
                        except OSError:
                            pass
                    last = stamps
            time.sleep(args.poll)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b_Ga=d,d=i,i=1,q=2\x1b\\\x1b_Ga=d,d=i,i=2,q=2\x1b\\\x1b[?25h\n")


if __name__ == "__main__":
    main()
