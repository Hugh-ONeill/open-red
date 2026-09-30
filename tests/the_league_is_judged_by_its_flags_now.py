#!/usr/bin/env python3
"""The Pokemon League is judged by its flags as they stand NOW.

After a loss the game puts every member back, but the run's history still
says they were beaten: "Defeat the Elite Four" was crossed off on "the
player is currently in Lorelei's room" (run 19, 2026-09-30). History is
marked where the game has unset it; a Defeat objective needs the win set
now; a reset win can be waited on again; and a flag the game took back does
not count as already holding before a plan starts.

Synthetic.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


d = Path(tempfile.mkdtemp(prefix="league_"))
(d / "run").mkdir()
live = ["EVENT_BEAT_LORELEIS_ROOM_TRAINER_0", "EVENT_GOT_HM04"]
(d / "run/obs.json").write_text(json.dumps({"flags": live}))
(d / "run/executor_log.jsonl").write_text("\n".join(json.dumps(
    {"kind": "flag_fired", "flag": f, "t": i}) for i, f in enumerate(
    ["EVENT_GOT_HM04", "EVENT_BEAT_LORELEIS_ROOM_TRAINER_0",
     "EVENT_BEAT_LANCES_ROOM_TRAINER_0", "EVENT_BEAT_LANCE"])) + "\n")
here = os.getcwd()
os.chdir(d)
try:
    ck("a Defeat objective whose win the game took back is not done",
       A._league_win_not_set("Defeat the Elite Four") == "ELITE FOUR")
    ck("...naming the member whose win is gone",
       A._league_win_not_set("Defeat Lance, the Dragon master") == "LANCE")
    ck("...but one whose win still stands is judged as before",
       A._league_win_not_set("Defeat Lorelei") is None)
    ck("an objective that only goes somewhere is not refused by this",
       A._league_win_not_set("Reach the Elite Four") is None)
    ck("a reset win can be waited on again",
       A.reset_flag_problem("EVENT_BEAT_LANCES_ROOM_TRAINER_0") == "")
    ev = A.recent_events()
    ck("the history marks what the game has put back",
       "EVENT_BEAT_LANCE — NOT SET NOW" in ev and "EVENT_GOT_HM04 — NOT SET" not in ev, ev[:400])
    plan = {"goal": "Defeat the Elite Four", "subgoals": [
        {"id": "beat_lance", "goal_text": "Beat Lance", "done_when": {"flag": "EVENT_BEAT_LANCE"}}]}
    probs = [p for p in A.validate(plan) if "ALREADY FIRED" in p]
    ck("a flag the game has unset is not 'already fired' for a new plan", not probs, probs)
    plan["subgoals"][0]["done_when"] = {"flag": "EVENT_GOT_HM04"}
    probs = [p for p in A.validate(plan) if "ALREADY FIRED" in p]
    ck("...while one still set is refused as before", bool(probs))
    (d / "run/last_state.json").write_text(json.dumps({"flags": live, "hall_of_fame": 1}))
    ck("a run in the Hall of Fame is past all of it",
       A._league_win_not_set("Defeat the Elite Four") is None)
finally:
    os.chdir(here)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
