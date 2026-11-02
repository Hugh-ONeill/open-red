#!/usr/bin/env python3
"""fresh_run.sh clears the old observation before launch and polls the bridge dir.

Code-health pass, 2026-11-02 (run 70 stop): run.sh removes obs.json inside the
detached setsid after fresh_run.sh has begun polling, so a leftover file from
the previous run could satisfy the 60 s wait and the badge read; and the poll
read run/ whatever RED_BRIDGE_DIR said. Pinned by source.
"""
import sys
from pathlib import Path

sh = (Path(__file__).resolve().parents[1] / "fresh_run.sh").read_text()
checks = [
    ("the bridge dir is the one polled", '_BD="${RED_BRIDGE_DIR:-$PWD/run}"' in sh
     and '[ -f "$_BD/obs.json" ]' in sh and "run/obs.json" not in sh),
    ("the old observation is cleared before the launch",
     sh.index('rm -f "$_BD/obs.json" "$_BD/cmd.lua"') < sh.index("setsid ./run.sh")),
    ("the badge read follows RED_BRIDGE_DIR", 'os.environ.get("RED_BRIDGE_DIR")' in sh),
]
bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
sys.exit(1 if bad else 0)
