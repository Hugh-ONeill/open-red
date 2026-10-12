#!/usr/bin/env python3
"""The pull check sees what the leg it would move already did when it ran.

Run 53 (2026-10-12): stuck in Silph Co. without the CARD KEY, the blocker
rung pulled "Retrieve the Secret Key from the Game Corner" ahead of it, and
the confirmation ("what does that leg HAND you?") answered "CARD KEY". That
leg had already run 9 tries over CELADON_CITY x156, GAME_CORNER x100 and the
prize room x35 and found no key, and the question showed none of it, only
the stuck leg's record (user: "it should know its not because its exhausted
celadon looking for that exact thing already").

Pinned: the confirmation carries the pulled leg's own yield record and its
search record, labelled as that leg's; a leg never played adds nothing.
Synthetic: the model is stubbed, no game.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

import author as A            # noqa: E402

checks = []


def ck(name, cond, d=""):
    checks.append((name, bool(cond), d))


SK = "Retrieve the Secret Key from the Game Corner"
SILPH = "Infiltrate Silph Co. and defeat the rival"
tmp = Path(tempfile.mkdtemp(prefix="pullcheck_prior_"))
(tmp / "run").mkdir()
(tmp / "run" / "attempt_yield").write_text(
    f"{SK}\t28\t3\tWHAT CHANGED WHILE THIS LEG RAN — events that fired: "
    f"EVENT_GOT_COIN_CASE; items gained: COIN_CASE x1.\n"
    f"{SK}\t28\t0\tDISPOSED: moved to after leg 31\n")
observed = tmp / "run" / "explored.json"
observed.write_text(json.dumps({
    "leg_goal": SILPH, "leg_looked": {"SILPH_CO_5F": 34}, "leg_tries": 4,
    "legs_past": {SK: {"tries": 9, "looked": {
        "CELADON_CITY": 156, "GAME_CORNER": 100, "GAME_CORNER_PRIZE_ROOM": 35}}}}))
bodies = []


def chat(msgs, model):
    bodies.append(msgs[-1]["content"])
    return '{"why": "x", "provides": null}'


A.brock_probe.chat = chat
os.chdir(tmp)
A.confirm_blocker(SILPH, 30, SK, 1, "standing in SILPH_CO_10F", "", "m",
                  held={}, observed=observed)
b = bodies[-1] if bodies else ""
ck("the question says the pulled leg has been played before",
   "THE LEG YOU WANT TO MOVE HAS BEEN PLAYED BEFORE" in b, b[-600:])
ck("...with what its runs yielded", "COIN_CASE" in b and "moved to after leg 31" in b, b[-600:])
ck("...and where it already looked", "GAME_CORNER" in b and "CELADON_CITY" in b
   and "ALREADY BEEN LOOKED FOR" in b, b[-600:])
ck("...after the stuck leg and the pulled leg are named",
   b.index("THE LEG YOU WANT TO MOVE, number 30") < b.index("HAS BEEN PLAYED BEFORE"))

A.confirm_blocker(SILPH, 31, "Defeat Sabrina for the Marsh Badge", 2,
                  "standing in SILPH_CO_10F", "", "m", held={}, observed=observed)
ck("a leg never played adds nothing", "PLAYED BEFORE" not in bodies[-1], bodies[-1][-300:])

src = (ROOT / "planner" / "author.py").read_text()
ck("check_blocker passes the observed record through",
   "held=held, observed=observed):" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
