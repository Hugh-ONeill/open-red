#!/usr/bin/env python3
"""A leg whose rounds keep finding nothing is cut, across its attempts, and
the drafts are told where the objective has already been looked for.

Run 36 (2026-10-04) spent some 790 rounds on the Secret Key and the Coin
Case, 85% of them finding nothing, while each rewrite sent the party back
to the prize room it had stood in 45 times (user: "it runs through the
same actions over and over again").
"""
from __future__ import annotations
import json, os, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E   # noqa: E402
import author as A     # noqa: E402

checks = []
def ck(name, ok): checks.append((name, bool(ok)))

ex = E.Executor.__new__(E.Executor)
logged = []
ex.log = lambda k, **kw: logged.append((k, kw))
sg = {"id": "get_secret_key", "done_when": {"has_item": {"SECRET_KEY": 1}}}

def run(gains):
    out = None
    for i, g in enumerate(gains, 1):
        if ex._leg_dry_round(sg, i, g):
            return i
    return out

# 1. a fresh attempt is never cut inside its grace, even on a dry window
ex._leg_rounds = [0] * 60
ex._attempt_rounds = 0
ex._leg_dry = None
ck("a new attempt gets its grace rounds before a dry window can cut it",
   run([False] * (E.Executor.LEG_DRY_GRACE - 1)) is None)
ck("...and is cut on the round its grace runs out",
   run([False]) == 1 and (ex._leg_dry or {}).get("subgoal") == "get_secret_key"
   and any(k == "leg_dry_end" for k, _ in logged))

# 2. a leg that keeps finding things is never cut
ex._leg_rounds, ex._attempt_rounds, ex._leg_dry = [], 0, None
ck("one find in every five rounds keeps the leg going",
   run([i % 5 == 0 for i in range(120)]) is None)

# 3. the window is the leg's, across attempts
ex._leg_rounds, ex._attempt_rounds, ex._leg_dry = [], 0, None
ck("a dry leg from a standing start is cut once the window fills",
   run([False] * 60) == E.Executor.LEG_DRY_WINDOW)

# 4. party legs pay in experience, not news
ex._leg_rounds, ex._attempt_rounds, ex._leg_dry = [], 0, None
party = {"id": "train", "done_when": {"party_min_level": 35}}
ck("a party leg is never counted",
   not any(ex._leg_dry_round(party, i, False) for i in range(1, 100))
   and not ex._leg_rounds)

# 5. off switch
_w = E.Executor.LEG_DRY_WINDOW
E.Executor.LEG_DRY_WINDOW = 0
ex._leg_rounds, ex._attempt_rounds, ex._leg_dry = [], 0, None
ck("RED_LEG_DRY_WINDOW=0 turns it off", run([False] * 100) is None)
E.Executor.LEG_DRY_WINDOW = _w

# 6. the plan ends, the verdict says so, and the campaign hands it on
src = (ROOT / "planner/executor.py").read_text()
ck("a cut leg ends the plan like a declared block",
   'if not ok and (getattr(self, "_leg_dry", None) or {}).get("subgoal") == sg.get("id"):' in src)
ck("the window is kept with the leg's record and cleared with it",
   '"leg_rounds": list(' in src and 'self._leg_rounds = []' in src)
ck("the verdict reads LEG DRY", 'f"LEG DRY (' in src)
camp = (ROOT / "campaign.sh").read_text()
ck("campaign.sh sends a LEG DRY result to the ladder, not a rewrite",
   'grep -qE "RESULT: LEG DRY" "$LOG"' in camp)

# 7. the drafts see where the objective was already looked for
d = {"leg_goal": "Retrieve the Secret Key from the Game Corner", "leg_tries": 3,
     "leg_looked": {"CELADON_CITY": 40, "GAME_CORNER_PRIZE_ROOM": 12},
     "press_log": {"CELADON_CITY|2,1": [["CELADONCITY_GRAMPS3", "hi"]] * 5}}
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
    json.dump(d, f)
t = A.looked_text(f.name, "Retrieve the Secret Key from the Game Corner")
ck("the drafts are shown the leg's own search record",
   "GAME_CORNER_PRIZE_ROOM: stood on 12x" in t and "CELADONCITY_GRAMPS3 5x" in t
   and "across 3 attempt(s)" in t)
ck("...and nothing for another objective",
   A.looked_text(f.name, "Reach Saffron City") == "")
os.unlink(f.name)
asrc = (ROOT / "planner/author.py").read_text()
ck("the draws and the review both carry it",
   "said += looked_text(observed, goal)" in asrc
   and "+ (looked_text(observed, goal) if observed else \"\")" in asrc)

bad = [n for n, ok in checks if not ok]
for n, ok in checks: print(("ok  " if ok else "FAIL"), n)
sys.exit(1 if bad else 0)
