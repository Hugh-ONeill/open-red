#!/usr/bin/env python3
"""The harness's buttonless write of the party list's cursor is recorded and
replayed, so the copy teaches the same Pokemon the run did.

Run 36, 2026-10-03: use_item sets partyMenuSavedIndex directly (next40); the
recorder logged buttons only, the copy's list opened on slot 1, and it sat
refused teaching RAZOR_WIND to GRAVELER where the run taught PIDGEOTTO (user:
"it *was* stuck for a bit trying to teach it to grav"). In game: a recorded
HM_CUT teach to slot 3 replays with every check matched; the same log with
the P line removed mismatches right after the teach. Source pins."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
rec = (ROOT / "harness/replay_rec.lua").read_text()
shim = (ROOT / "harness/shim.lua").read_text()
sh = (ROOT / "tools/shadow/shadow.lua").read_text()
checks = [
    ("the recorder can log a buttonless write", "function R.event(kind, arg)" in rec),
    ("the shim logs the cursor where it writes it",
     'if wd.rec and wd.rec.event then pcall(wd.rec.event, "P", _want) end' in shim),
    ("the copy reads P lines", 'or kind == "W" or kind == "P" then' in sh),
    ("...and makes the same write", "game.partyMenuSavedIndex = tonumber(arg)" in sh),
]
for n, ok in checks: print(("ok   " if ok else "FAIL ") + n)
raise SystemExit(0 if all(ok for _, ok in checks) else 1)
