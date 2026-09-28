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
"""
import argparse
import base64
import io
import json
import os
import re
import sys
import textwrap
import time

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OBS = os.path.join(HERE, "..", "run", "obs.json")
STATUS = os.path.join(HERE, "..", "run", "status.txt")
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

W, ROW, TOP = 248, 58, 16          # the team column
COLS = 46                          # the status column, in 8px characters
LINE = 10

# The cartridge's own charmap: font.png is tiles $80-$FF, 16 to a row, and a
# pixel is ink where its palette index is 1.
CHARMAP = {c: 0x80 + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
CHARMAP.update({c: 0xA0 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})
CHARMAP.update({c: 0xF6 + i for i, c in enumerate("0123456789")})
CHARMAP.update({"(": 0x9A, ")": 0x9B, ":": 0x9C, ";": 0x9D, "[": 0x9E,
                "]": 0x9F, "'": 0xE0, "-": 0xE3, "?": 0xE6, "!": 0xE7,
                ".": 0xE8, "/": 0xF3, ",": 0xF4})
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
SUBST = {"—": "-", "–": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "é": "e"}

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

    def text(self, img, x, y, s, col=FG):
        for ch in s:
            ch = SUBST.get(ch, ch)
            for gx, gy in self.glyph(ch):
                img.putpixel((x + gx, y + gy), col)
            x += 8

    def text_right(self, img, y, s, col=FG, pad=4, right=W):
        self.text(img, right - 8 * len(s) - pad, y, s, col)

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


def render_team(obs, painter):
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
            return "leg %d: %s%s" % (int(m.group(1)), m.group(2).replace("_", " "),
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


def render_status(text, painter, height):
    img = Image.new("RGB", (COLS * 8 + 8, height), BG)
    if text is None:
        painter.text(img, 4, 4, "NO STATUS YET", DIM)
        return img
    fields, order, elapsed = parse_status(text)
    known = {k for k, _, _ in FIELDS}
    rows = [(k, lab, col) for k, lab, col in FIELDS if fields.get(k)]
    rows += [(k, k.replace("_", " "), DIM) for k in order
             if k not in known and k not in SKIP and fields.get(k)]
    y = 4
    painter.text(img, 4, y, "RUN", ACCENT)
    if elapsed:
        painter.text(img, 40, y, "t+" + clock(int(elapsed[:-1])), DIM)
    age = file_age(STATUS)
    if age is not None:
        painter.text_right(img, y, "updated %s ago" % clock(age), YELLOW if age > 120 else DIM,
                           right=img.width)
    y += LINE + 4
    for key, label, col in rows:
        if y + 2 * LINE > height:
            painter.text(img, 4, height - LINE, "...", DIM)
            break
        painter.text(img, 4, y, label, ACCENT if col is not ACCENT else DIM)
        y += LINE
        for line in textwrap.wrap(tidy(key, fields[key]), COLS - 1) or [""]:
            if y + LINE > height:
                break
            painter.text(img, 12, y, line, col)
            y += LINE
        y += 4
    return img


GUTTER = 8
SIDE_W = W + GUTTER + COLS * 8 + 8  # team | status
STACK_W = max(W, COLS * 8 + 8)     # team over status


def render(obs, status_text, painter, layout="side", height=None):
    """layout "side": team | status, both `height` tall (at least the team's).
    layout "stack": team over status, the status filling down to `height`."""
    team = render_team(obs, painter)
    if layout == "stack":
        rest = max((height or 0) - team.height, 30 * LINE)
        col = render_status(status_text, painter, rest)
        img = Image.new("RGB", (STACK_W, team.height + col.height), BG)
        img.paste(team, (0, 0))
        img.paste(col, (0, team.height))
        return img
    h = max(team.height, height or 0)
    col = render_status(status_text, painter, h)
    img = Image.new("RGB", (SIDE_W, h), BG)
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


def fit(win, team_h):
    """Pick the layout and whole-number scale that fill the window best (whole
    numbers keep the pixels square); side by side wins a tie."""
    if not win:
        return "side", 2, None
    xpx, ypx = win
    best = None
    for layout, width, min_h in (("side", SIDE_W, team_h), ("stack", STACK_W, team_h + 20 * LINE)):
        scale = min(xpx // width, ypx // min_h)
        if scale >= 1 and (best is None or scale > best[1]):
            best = (layout, scale)
    layout, scale = best or ("side", 1)
    return layout, scale, ypx // scale


def read_obs():
    # the shim rewrites obs.json in place; a half-written file is simply
    # skipped and the next change picks it up
    try:
        with open(OBS) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def read_status():
    try:
        with open(STATUS) as f:
            return f.read()
    except OSError:
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

    def frame_bytes(obs, status_text, win=None):
        team_h = TOP + ROW * 7 + 12
        layout, scale, height = fit(win, team_h)
        if args.scale:
            scale, height = args.scale, (win[1] // args.scale if win else None)
        img = render(obs, status_text, painter, layout, height)
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return buf.getvalue()

    if args.png:
        obs = read_obs()
        if obs is None:
            sys.exit(f"cannot read {OBS}")
        with open(args.png, "wb") as f:
            f.write(frame_bytes(obs, read_status()))
        return

    if os.environ.get("TERM") != "xterm-kitty":
        print("warning: not a kitty window; the image may not show "
              "(inside tmux, kitty graphics need allow-passthrough)", file=sys.stderr)
    sys.stdout.write("\x1b[2J\x1b[?25l")    # clear, hide the cursor
    last, obs = None, None
    try:
        while True:
            win = window_pixels()
            # the age tick repaints "updated Ns ago" every 5 s even when idle
            stamps = (stamp_of(OBS), stamp_of(STATUS), win, int(time.time()) // 5)
            if stamps != last:
                fresh = read_obs()
                obs = fresh if fresh is not None else obs
                if obs is not None:
                    kitty_show(frame_bytes(obs, read_status(), win))
                    last = stamps
            time.sleep(args.poll)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b_Ga=d,d=i,i=1,q=2\x1b\\\x1b[?25h\n")


if __name__ == "__main__":
    main()
