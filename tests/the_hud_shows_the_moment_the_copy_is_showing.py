#!/usr/bin/env python3
"""The HUD shows the moment the 1x copy is showing, not the run's now.

On stream the game on screen is the copy, minutes behind the 200x run, and a
HUD reading the run's own status and events announced fights the screen had
not reached (user, 2026-10-03: "the hud shows the wrong games state"). The
copy's snapshot carries run_t, the run's second at the copy's step; the HUD
then reads status, phase and events as they stood at that second.

Pinned: status_at / phase_at give the latest change at or before a moment;
last_events stops at `until`; with a fresh copy snapshot the HUD's status,
phase and events come from run_t and the live model line is held back; with
the copy caught up (or none) it reads the live files. Synthetic files only.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP = Path(tempfile.mkdtemp())
os.environ["RED_EVENTS"] = str(TMP / "events.jsonl")
sys.path.insert(0, str(ROOT / "tools"))
import events as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


now = time.time()
T1, T2, T3 = now - 600, now - 300, now - 10
E.hist_append("status", {"text": "PLAN leg 5\nWHERE ROUTE_2"}, t=T1)
E.hist_append("phase", {"phase": {"phase": "playing"}}, t=T1)
E.hist_append("status", {"text": "PLAN leg 6\nWHERE PEWTER_GYM"}, t=T2)
E.hist_append("phase", {"phase": {"phase": "authoring", "goal": "Defeat Brock"}}, t=T3)
with open(E.FEED, "w") as f:
    for t, text in ((T1 + 5, "caught a PIDGEY"), (T2 + 5, "beat JR.TRAINER at PEWTER GYM")):
        f.write(json.dumps({"t": t, "kind": "x", "tone": "good", "level": 2, "text": text}) + "\n")

ck("status_at gives the latest change at or before the moment",
   E.status_at(T1 + 60).startswith("PLAN leg 5") and E.status_at(T2 + 1).startswith("PLAN leg 6"))
ck("...and nothing before the first", E.status_at(T1 - 1) is None)
ck("phase_at likewise", E.phase_at(T2)["phase"] == "playing" and E.phase_at(now)["phase"] == "authoring")
ck("last_events stops at until",
   [e["text"] for e in E.last_events(10, 2, until=T1 + 60)] == ["caught a PIDGEY"])

import worldmap as W  # noqa: E402
import hud as H  # noqa: E402
W.COPY = str(TMP / "shadow_obs.json")
H.OBS = str(TMP / "obs.json")
H.STATUS = str(TMP / "status.txt")
Path(H.STATUS).write_text("PLAN leg 9 (the run's now)\n")
Path(H.OBS).write_text(json.dumps({"mode": "overworld", "party": []}))
Path(W.COPY).write_text(json.dumps({"source": "copy", "run_t": T1 + 60, "party": [], "mode": "overworld"}))
o = H.read_obs()
ck("a fresh copy snapshot is the game the HUD shows", o.get("source") == "copy")
ck("...the status is the one from the copy's moment", (H.read_status() or "").startswith("PLAN leg 5"))
ck("...the phase too", H.phase_now()["phase"] == "playing")
ck("...and the live model line is held back", H.model_activity() == {"phase": "idle", "since": None})
os.utime(W.COPY, (now - 60, now - 60))           # the copy idle: its snapshot goes stale
o = H.read_obs()
ck("with no fresh copy the HUD reads the run itself",
   o.get("source") is None and (H.read_status() or "").startswith("PLAN leg 9")
   and H.VIEW["live"])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
