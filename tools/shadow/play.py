#!/usr/bin/env python3
"""Play a recorded boot of the run again in a second game, at watching speed.

harness/replay_rec.lua writes one directory per boot of the 200x game under
$RED_BRIDGE_DIR/replay/. This starts a second game on one of them with the
shadow driver (tools/shadow/shadow.lua) under its OWN love identity
("red-shadow"): the save it continues from and the options are the ones the
run booted with, copied into that identity, so nothing the copy saves can
reach the run's save.

  tools/shadow/play.py                 the newest boot, headed, 1x, following
  tools/shadow/play.py SEG --headless  verify a finished boot without a window
  tools/shadow/play.py --chain         every boot in order, one after another
  tools/shadow/play.py --live          follow the run: each boot in order as the
                                       game restarts, waiting for the next one
                                       (--since EPOCH: only boots after then)

Viewer-only: nothing here is read by the planner or the model.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAME_DIR = Path(os.environ.get("GEN1RECOMP_DIR") or Path.home() / "Developer/gen1recomp")
LOVE = Path.home() / ".local/share/love"
LIVE_IDENT = "pokemon-love2d"
SHADOW_IDENT = "red-shadow"
RUN = Path(os.environ.get("RED_BRIDGE_DIR") or ROOT / "run")


def segments(run: Path = RUN) -> list[Path]:
    d = run / "replay"
    return sorted(p for p in d.iterdir() if (p / "log").exists()) if d.is_dir() else []


def prepare(seg: Path, ident: str = SHADOW_IDENT, game: str = "red") -> None:
    """The copy's identity holds what the run booted with and nothing else."""
    home = LOVE / ident
    saves = home / "saves" / game
    saves.mkdir(parents=True, exist_ok=True)
    cache = LOVE / LIVE_IDENT / game
    if cache.is_dir() and not (home / game).is_dir():
        shutil.copytree(cache, home / game)        # the decoded ROM (~5 MB)
    for name in ("slot1.lua", "slot1.lua.bak"):
        (saves / name).unlink(missing_ok=True)
    if (seg / "slot1.lua").exists():
        shutil.copy(seg / "slot1.lua", saves / "slot1.lua")
    if (seg / "options.lua").exists():
        shutil.copy(seg / "options.lua", home / "options.lua")


def play(seg: Path, headless: bool = False, speed: float = 1, follow: bool = True,
         quiet: bool = False, ident: str = SHADOW_IDENT) -> int:
    prepare(seg, ident)
    env = dict(os.environ,
               POKEPORT_DRIVER=str(ROOT / "tools/shadow/shadow.lua"),
               POKEPORT_SPEED="1", POKEPORT_GAME="red", POKEPORT_IDENTITY=ident,
               SHADOW_SEG=str(seg), SHADOW_SPEED=str(speed),
               SHADOW_FOLLOW="1" if follow else "0", SHADOW_QUIET="1" if quiet else "0",
               # a boot recorded before the recorder kept seen.json: the run's own
               SHADOW_SEEN_FALLBACK=str(RUN / "seen.json"))
    env.pop("RED_BRIDGE_DIR", None)
    if headless:
        env["SDL_AUDIODRIVER"] = "dummy"
        env.pop("WAYLAND_DISPLAY", None)
        env["SDL_VIDEODRIVER"] = "x11"
        # a screen big enough for the run's window: the window size is logic
        # here (shadow.lua, THE VIEW IS LOGIC TOO), and xvfb's default is 640x480
        cmd = ["xvfb-run", "-a", "-s", "-screen 0 3840x2160x24", "love", "."]
    else:
        cmd = ["love", "."]
    return subprocess.call(cmd, cwd=GAME_DIR, env=env)


def _started(seg: Path) -> float:
    try:
        return float(seg.name.split("-")[0])
    except ValueError:
        return 0.0


def live(a) -> None:
    """Each boot in order, then wait for the next. The shadow ends a boot
    once a newer one exists and the old log is played out, so a restarted
    game (every attempt boots afresh) carries straight on."""
    last = None                             # the boot played last; only later ones follow
    while True:
        segs = [s for s in segments()
                if (last is None or s.name > last) and (a.since is None or _started(s) >= a.since)]
        if last is None and a.since is None and segs:
            segs = segs[-1:]                # attaching: start with the newest
        if not segs:
            time.sleep(2)
            continue
        seg = segs[0]
        print(f"[shadow] playing {seg}", flush=True)
        play(seg, a.headless, a.speed, follow=True, quiet=a.quiet)
        last = seg.name


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("seg", nargs="?", help="a replay/<boot> directory (default: the newest)")
    ap.add_argument("--headless", action="store_true", help="no window, no sound")
    ap.add_argument("--speed", type=float, default=1, help="speed where something happens (1 = the game's own)")
    ap.add_argument("--no-follow", action="store_true", help="stop at the end of the log instead of waiting")
    ap.add_argument("--chain", action="store_true", help="play every boot in order")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--live", action="store_true", help="follow the run's boots as they come")
    ap.add_argument("--since", type=float, default=None, help="with --live: only boots started after this epoch")
    a = ap.parse_args()
    if a.live:
        live(a)
        return
    segs = segments()
    if a.chain:
        todo = segs
    elif a.seg:
        todo = [Path(a.seg)]
    else:
        todo = segs[-1:]
    if not todo:
        sys.exit(f"no recorded boots under {RUN / 'replay'}")
    for seg in todo:
        print(f"[shadow] playing {seg}")
        rc = play(seg, a.headless, a.speed, follow=not a.no_follow, quiet=a.quiet)
        if rc:
            sys.exit(rc)


if __name__ == "__main__":
    main()
