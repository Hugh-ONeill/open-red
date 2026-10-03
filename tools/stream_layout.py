#!/usr/bin/env python3
"""Keep the stream's two windows laid out: the 1x copy left and the HUD right
while there is a game to show; the HUD across the whole screen while the
model authors and the copy has nothing left to play (user, 2026-10-03: "when
its authoring the hud can be fullscreen, it shows the map better").

Started by stream.sh with the tile geometry it worked out. The copy's window
comes and goes with every boot of the game, so the HUD only widens once the
phase says authoring AND the copy has been gone a few seconds, and narrows the
moment the copy is back. Viewer-only: reads phase.json and the window list.

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


def place(w: int, h: int, x: int, y: int) -> None:
    for args in (["setfloating", HUD],
                 ["resizewindowpixel", f"exact {w} {h},{HUD}"],
                 ["movewindowpixel", f"exact {x} {y},{HUD}"]):
        subprocess.run(["hyprctl", "-q", "dispatch", *args], timeout=5)


def main() -> None:
    w, h, lx, ly, rx, ry, fw = (int(v) for v in sys.argv[1:8])
    wide = None                   # what the HUD is now: None until first placed
    gone_since = None
    while True:
        cs = clients()
        hud = [c for c in cs if c.get("title") == "red-recomp HUD"]
        copy_up = any(c.get("class") == "love" for c in cs)
        now = time.time()
        gone_since = None if copy_up else (gone_since or now)
        want = (not copy_up) and authoring() and now - gone_since >= GRACE
        if hud and want != wide:
            if want:
                place(fw, h, lx, ly)
            else:
                place(w, h, rx, ry)
            wide = want
        time.sleep(1)


if __name__ == "__main__":
    main()
