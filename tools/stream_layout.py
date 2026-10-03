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
SNAP = Path.home() / ".local/state/red-recomp/shadow_obs.json"
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


def copy_idle(copies: list) -> bool:
    """No copy window, or a copy holding still at the end of what the run has
    played (it writes no snapshot while it holds): nothing to show. The copy
    stays open while the model authors, caught up, so its window alone did not
    say that (2026-10-03: "showing the game when it should be fullscreen hud
    during authoring")."""
    if not copies:
        return True
    try:
        return time.time() - SNAP.stat().st_mtime > GRACE
    except OSError:
        return True


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
    was_wide = None
    while True:
        cs = clients()
        huds = [c for c in cs if c.get("title") == "red-recomp HUD"]
        copies = [c for c in cs if c.get("class") == "love"]
        wide = authoring() and copy_idle(copies)
        try:
            for c in copies:
                place(c, w, h, lx, ly)
            for c in huds:
                if wide:
                    place(c, fw, h, lx, ly)
                    if was_wide is not True:          # over the copy's idle window
                        subprocess.run(["hyprctl", "-q", "dispatch", "alterzorder",
                                        f"top,address:{c['address']}"], timeout=5)
                else:
                    place(c, w, h, rx, ry)
            was_wide = wide
        except (OSError, subprocess.SubprocessError, KeyError):
            pass
        time.sleep(1)


if __name__ == "__main__":
    main()
