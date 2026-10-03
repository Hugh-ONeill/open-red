#!/usr/bin/env python3
"""Keep the stream's two windows laid out: the 1x copy left and the HUD right
while there is a game to show; the HUD across the whole screen while the
model authors and the copy has nothing left to play (user, 2026-10-03: "when
its authoring the hud can be fullscreen, it shows the map better").

Started by stream.sh with the tile geometry it worked out. The copy's window
comes and goes with every boot of the game, so the HUD only widens once the
phase says authoring AND the copy has been gone a few seconds, and narrows the
moment the copy is back. Viewer-only: reads phase.json and the window list.

It also KEEPS both windows where they belong, checking every second: the
window rules stream.sh adds are runtime only (a `hyprctl reload` drops them)
and the copy opens a new window at every boot, so one landed off screen at
(-1592,-145) with the HUD left wherever it was (2026-10-03).

  tools/stream_layout.py W H LX LY RX RY FW
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

PHASE = Path.home() / ".local/state/red-recomp/phase.json"
HUD = "title:^(red-recomp HUD)$"
GRACE = 3.0          # seconds the copy must be gone before the HUD widens


def clients() -> list[dict]:
    try:
        return json.loads(subprocess.check_output(["hyprctl", "clients", "-j"], timeout=5))
    except (OSError, subprocess.SubprocessError, ValueError):
        return []


def authoring() -> bool:
    try:
        return json.loads(PHASE.read_text()).get("phase") == "authoring"
    except (OSError, ValueError):
        return False


def place(c: dict, w: int, h: int, x: int, y: int) -> None:
    """Float the window at exactly (x, y) w x h, unless it already is."""
    at, size = c.get("at") or [0, 0], c.get("size") or [0, 0]
    if (c.get("floating") and abs(at[0] - x) <= 1 and abs(at[1] - y) <= 1
            and abs(size[0] - w) <= 1 and abs(size[1] - h) <= 1):
        return
    target = f"address:{c['address']}"
    if not c.get("floating"):
        subprocess.run(["hyprctl", "-q", "dispatch", "setfloating", target], timeout=5)
    subprocess.run(["hyprctl", "-q", "dispatch", "resizewindowpixel", f"exact {w} {h},{target}"], timeout=5)
    subprocess.run(["hyprctl", "-q", "dispatch", "movewindowpixel", f"exact {x} {y},{target}"], timeout=5)


def main() -> None:
    w, h, lx, ly, rx, ry, fw = (int(v) for v in sys.argv[1:8])
    gone_since = None
    while True:
        cs = clients()
        huds = [c for c in cs if c.get("title") == "red-recomp HUD"]
        copies = [c for c in cs if c.get("class") == "love"]
        now = time.time()
        gone_since = None if copies else (gone_since or now)
        wide = (not copies) and authoring() and now - gone_since >= GRACE
        try:
            for c in copies:
                place(c, w, h, lx, ly)
            for c in huds:
                if wide:
                    place(c, fw, h, lx, ly)
                else:
                    place(c, w, h, rx, ry)
        except (OSError, subprocess.SubprocessError, KeyError):
            pass
        time.sleep(1)


if __name__ == "__main__":
    main()
