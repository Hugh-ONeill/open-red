#!/usr/bin/env python3
"""The Pokemon League counts its blackouts as one place, across laps.

Every lap of the Elite Four starts a new step, so the per-step count behind
the gym leaders' "something about the plan has to change" and the rows of
wild ground to train on never passed one; run 19 won by attrition, never
going back to train (user, 2026-09-30: "something similar to how we do the
gym leaders just scoped to the whole thing").

Synthetic log hook, plus source checks for the page block.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


x = object.__new__(E.Executor)
x.logf = io.StringIO()
x.t0 = 0
x._last_overworld_map = "LANCES_ROOM"
x._recent_foes = [("GYARADOS L58", "LANCES_ROOM"), ("DRAGONITE L62", "LANCES_ROOM")]
x.log("fight_recap", who="JERK", where="LANCES_ROOM", lost=True, text="...")
ck("a lost fight in the league is kept as a lap (the Champion wrote no blackout row)",
   getattr(x, "_league_laps", None) == [{"room": "LANCES_ROOM", "who": "JERK",
                                         "foes": ["GYARADOS L58", "DRAGONITE L62"]}],
   getattr(x, "_league_laps", None))
x.log("fight_recap", who="LORELEI", where="LORELEIS_ROOM", lost=False, text="...")
x.log("fight_recap", who="BROCK", where="PEWTER_GYM", lost=True, text="...")
x.log("blackout", subgoal="defeat_lance")
ck("a won fight, a loss outside the league and a bare blackout row are not laps",
   len(x._league_laps) == 1, x._league_laps)

src = (ROOT / "planner/executor.py").read_text()
ck("a ledger from before laps were kept is rebuilt from the journal",
   'if "league_laps" not in data:' in src and "_league_laps_from_journal()" in src)
ck("the league is one place", 'LEAGUE_MAPS = ("INDIGO_PLATEAU_LOBBY", "LORELEIS_ROOM"' in src)
blk = src[src.index("THE LEAGUE IS ONE PLACE"):][:7000]
ck("the page count is the laps in the league, the step's own count otherwise",
   '_bo_eff = max(getattr(self, "_bo_here", 0), len(_laps))' in blk)
ck("the gym-leader lines key on it", "if _bo_eff > 1 else" in blk and "if (_bo_eff > 1" in blk)
ck("the laps are listed", "LAPS OF THE POKEMON LEAGUE THAT ENDED IN A BLACKOUT" in blk)
ck("the round pardons still read the step's own count",
   "_bo_n = getattr(self, \"_bo_here\", 0)" in src and "self._bo_here = len(_laps)" not in src)
ck("the laps are saved with the run", '"league_laps": getattr(self, "_league_laps", [])' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
