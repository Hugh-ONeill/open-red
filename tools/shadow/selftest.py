#!/usr/bin/env python3
"""Record a stretch of play at 200x and check the shadow plays it back exactly.

Boots this checkout's shim (run.sh) on its OWN love identity and bridge dir,
so it is safe beside a live chain: it continues SAVE (a save standing in
grass), captures a checkpoint, grinds wild battles, writes a harness save,
restores the checkpoint and grinds again. Then the shadow replays the log
headless at 1x. Passes when every sync check matched.

  tools/shadow/selftest.py SAVE [--own-audio]

--own-audio is the control: the copy asks its own speakers instead of the
run's recorded answers, and should drift (2026-10-03: step 88,200 of 133,199,
in the wild battles), which is why the answers are recorded.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOVE = Path.home() / ".local/share/love"
IDENT = "red-shadowtest"


def record(save: Path, out: Path) -> Path:
    home = LOVE / IDENT
    (home / "saves/red").mkdir(parents=True, exist_ok=True)
    if not (home / "red").is_dir():
        shutil.copytree(LOVE / "pokemon-love2d/red", home / "red")
    shutil.copy(save, home / "saves/red/slot1.lua")
    for n in ("options.lua", "options.lua.bak"):
        if (LOVE / "pokemon-love2d" / n).exists():
            shutil.copy(LOVE / "pokemon-love2d" / n, home / n)
    env = dict(os.environ, RED_BRIDGE_DIR=str(out), POKEPORT_IDENTITY=IDENT, RED_MUTE="1")
    env.pop("RED_REPLAY_REC", None)
    proc = subprocess.Popen([str(ROOT / "run.sh"), "200"], env=env, start_new_session=True,
                            stdout=open(out / "game.log", "wb"), stderr=subprocess.STDOUT)
    try:
        for _ in range(90):
            if (out / "obs.json").exists():
                break
            time.sleep(1)
        else:
            sys.exit("the recording game did not come up")
        os.environ["RED_BRIDGE_DIR"] = str(out)       # before the planner imports
        sys.path.insert(0, str(ROOT / "planner"))
        from bridge import Bridge
        from executor import bootstrap
        b = Bridge(out, timeout=300)
        bootstrap(b, cont=True)
        battles = 0

        def fight():
            nonlocal battles
            if (b.obs() or {}).get("mode") == "battle":
                battles += 1
            for _ in range(40):
                if (b.obs() or {}).get("mode") != "battle":
                    return
                b.send("battle_move", index=1)

        b.send("checkpoint_capture", token="esc")
        for _ in range(3):
            b.send("grind", steps=60)
            fight()
        b.send("save_game")
        b.send("checkpoint_restore", token="esc")
        b.send("grind", steps=60)
        fight()
        b.send("wait", frames=600)
        print(f"[selftest] recorded {battles} battle(s)")
    finally:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
    segs = sorted((out / "replay").iterdir())
    if not segs:
        sys.exit("nothing was recorded")
    return segs[-1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("save", type=Path, help="a slot1.lua standing in grass")
    ap.add_argument("--own-audio", action="store_true", help="the control: no recorded answers")
    a = ap.parse_args()
    out = Path(tempfile.mkdtemp(prefix="shadowtest."))
    seg = record(a.save, out)
    log = (seg / "log").read_text()
    kinds = {k: len(re.findall(rf"^{k} ", log, re.M)) for k in "BIAHRGW"}
    print(f"[selftest] {seg}: " + " ".join(f"{k}={n}" for k, n in kinds.items()))
    env = dict(os.environ, SHADOW_OWN_AUDIO="1" if a.own_audio else "0")
    t = time.time()
    out_txt = subprocess.run(
        [sys.executable, str(ROOT / "tools/shadow/play.py"), str(seg), "--headless",
         "--speed", "1", "--no-follow", "--quiet"],
        capture_output=True, text=True, env=env).stdout
    end = [l for l in out_txt.splitlines() if "end of the log" in l]
    print(f"[selftest] replayed at 1x in {time.time() - t:.0f}s: " + (end[-1] if end else "no end line"))
    ok = bool(end) and "every check matched" in end[-1]
    if a.own_audio:
        print("[selftest] control " + ("DRIFTED, as expected" if not ok else "did NOT drift"))
        sys.exit(0 if not ok else 1)
    sys.exit(0 if ok and kinds["H"] > 0 else 1)


if __name__ == "__main__":
    main()
