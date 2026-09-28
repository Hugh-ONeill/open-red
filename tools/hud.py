#!/usr/bin/env python3
"""Team HUD for watching a run: the party drawn with its own front pics, the
Game Boy font and HP bars, redrawn whenever run/obs.json changes.

Everything it draws comes from the game's extraction of YOUR ROM
(~/.local/share/love/pokemon-love2d/red/assets/generated/), so nothing is
shipped. It only READS: obs.json and the asset folder. Safe beside a live chain.

  tools/hud.py                 # live, in this kitty window (graphics protocol)
  tools/hud.py --png hud.png   # write one frame and exit
  tools/hud.py --scale 2       # smaller

In battle the Pokemon that is out is framed and carries its status (SLP, PSN,
...), and the foe gets a line of its own under the team.
"""
import argparse
import base64
import io
import json
import os
import sys
import time

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OBS = os.path.join(HERE, "..", "run", "obs.json")
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

W, ROW, TOP = 248, 58, 16

# The cartridge's own charmap: font.png is tiles $80-$FF, 16 to a row, and a
# pixel is ink where its palette index is 1.
CHARMAP = {c: 0x80 + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
CHARMAP.update({c: 0xA0 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})
CHARMAP.update({c: 0xF6 + i for i, c in enumerate("0123456789")})
CHARMAP.update({"(": 0x9A, ")": 0x9B, ":": 0x9C, ";": 0x9D, "[": 0x9E,
                "]": 0x9F, "'": 0xE0, "-": 0xE3, "?": 0xE6, "!": 0xE7,
                ".": 0xE8, "/": 0xF3, ",": 0xF4})


class Painter:
    def __init__(self):
        self.font = Image.open(ASSETS + "fonts/font.png")
        self.glyphs = {}
        self.pics = {}

    def glyph(self, code):
        if code not in self.glyphs:
            k = code - 0x80
            g = self.font.crop(((k % 16) * 8, (k // 16) * 8,
                                (k % 16) * 8 + 8, (k // 16) * 8 + 8))
            self.glyphs[code] = [(x, y) for y in range(8) for x in range(8)
                                 if g.getpixel((x, y)) == 1]
        return self.glyphs[code]

    def text(self, img, x, y, s, col=FG):
        for ch in s:
            code = CHARMAP.get(ch)
            if code is not None:
                for gx, gy in self.glyph(code):
                    img.putpixel((x + gx, y + gy), col)
            x += 8

    def text_right(self, img, y, s, col=FG, pad=4):
        self.text(img, W - 8 * len(s) - pad, y, s, col)

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

    def bar(self, img, x, y, w, frac, h=4):
        col = ACCENT if frac > 0.5 else YELLOW if frac > 0.2 else RED
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


def render(obs, painter):
    party = obs.get("party") or []
    battle = obs.get("battle") if isinstance(obs.get("battle"), dict) else None
    me = (battle or {}).get("me") or {}
    foe = (battle or {}).get("foe") or {}
    out_slot = me.get("slot")          # 1-based party slot of the mon that is out
    height = TOP + ROW * 6 + (ROW + 12 if foe else 0)
    img = Image.new("RGB", (W, height), BG)

    badges = len(obs.get("badges") or [])
    painter.text(img, 4, 4, "TEAM", ACCENT)
    painter.text_right(img, 4, "%d BADGE%s" % (badges, "" if badges == 1 else "S"), DIM)

    for i in range(6):
        y = TOP + i * ROW
        if i >= len(party):
            painter.text(img, 58, y + 24, "-", DIM)
            continue
        p = party[i]
        img.paste(painter.card(p["species"]), (3, y + 2))
        is_out = out_slot == i + 1
        hp, max_hp = p.get("hp", 0), p.get("max_hp") or 1
        status = me.get("status") if is_out else None
        if is_out:
            hp = me.get("hp", hp)
            painter.frame(img, 1, y, W - 2, ROW - 2, ACCENT)
        painter.text(img, 58, y + 6, (p.get("nickname") or p["species"])[:10])
        painter.text(img, 58, y + 16, p["species"][:10], DIM)
        painter.text_right(img, y + 6, ":L%d" % p.get("level", 0), ACCENT)
        if hp <= 0:
            painter.text_right(img, y + 16, "FNT", RED)
        elif status:
            painter.text_right(img, y + 16, str(status)[:3], YELLOW)
        painter.bar(img, 58, y + 30, W - 58 - 6, hp / max_hp)
        painter.text(img, 58, y + 38, "/".join(t[:3] for t in p.get("types") or []), DIM)
        painter.text_right(img, y + 38, "%d/%d" % (hp, max_hp), DIM)

    if foe:
        y = TOP + ROW * 6
        painter.text(img, 4, y + 2, "FOE", RED)
        img.paste(painter.card(foe.get("species") or "?"), (3, y + 14))
        painter.text(img, 58, y + 20, (foe.get("species") or "?")[:10])
        if foe.get("status"):
            painter.text_right(img, y + 20, str(foe["status"])[:3], YELLOW)
        frac = (foe.get("hp") or 0) / (foe.get("maxhp") or 1)
        painter.bar(img, 58, y + 36, W - 58 - 6, frac)
    return img


def read_obs():
    # the shim rewrites obs.json in place; a half-written file is simply
    # skipped and the next change picks it up
    try:
        with open(OBS) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def kitty_show(png_bytes):
    """Replace image id 1 at the top-left, through kitty's graphics protocol,
    so a redraw swaps the picture in place instead of scrolling."""
    data = base64.b64encode(png_bytes).decode()
    out = ["\x1b[H", "\x1b_Ga=d,d=i,i=1,q=2\x1b\\"]
    chunks = [data[i:i + 4096] for i in range(0, len(data), 4096)] or [""]
    for n, chunk in enumerate(chunks):
        more = 1 if n < len(chunks) - 1 else 0
        head = "a=T,f=100,i=1,C=1,q=2," if n == 0 else ""
        out.append(f"\x1b_G{head}m={more};{chunk}\x1b\\")
    sys.stdout.write("".join(out))
    sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--png", help="write one frame to this file and exit")
    ap.add_argument("--scale", type=int, default=3)
    ap.add_argument("--poll", type=float, default=0.25, help="seconds between checks")
    args = ap.parse_args()
    painter = Painter()

    def frame_bytes(obs):
        img = render(obs, painter)
        img = img.resize((img.width * args.scale, img.height * args.scale), Image.NEAREST)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return buf.getvalue()

    if args.png:
        obs = read_obs()
        if obs is None:
            sys.exit(f"cannot read {OBS}")
        with open(args.png, "wb") as f:
            f.write(frame_bytes(obs))
        return

    if os.environ.get("TERM") != "xterm-kitty":
        print("warning: not a kitty window; the image may not show "
              "(inside tmux, kitty graphics need allow-passthrough)", file=sys.stderr)
    sys.stdout.write("\x1b[2J\x1b[?25l")    # clear, hide the cursor
    last = None
    try:
        while True:
            try:
                stamp = os.stat(OBS).st_mtime_ns
            except OSError:
                stamp = None
            if stamp is not None and stamp != last:
                obs = read_obs()
                if obs is not None:
                    kitty_show(frame_bytes(obs))
                    last = stamp
            time.sleep(args.poll)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b_Ga=d,d=i,i=1,q=2\x1b\\\x1b[?25h\n")


if __name__ == "__main__":
    main()
