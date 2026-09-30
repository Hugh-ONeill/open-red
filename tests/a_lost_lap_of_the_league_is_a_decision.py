#!/usr/bin/env python3
"""A lap of the league lost past the first ends the plan, and the rewrite
reads what the laps showed.

Every E4 loss used to replay the plan from Lorelei inside the same attempt
(the league resets its wins, the plan regressed to the first undone step):
run 19 lapped the league twelve times by attrition and never reached the
rewrite, where training is on the table, or the ladder (user, 2026-09-29;
2026-09-30: "pass the first lap"). The first lap lost still replays, like a
gym's first wipe; every one after ends the attempt at the lobby.

Source checks on the executor; journal_text on a small journal.
"""
from __future__ import annotations

import inspect
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


import executor as E  # noqa: E402
import author as A  # noqa: E402

rp = inspect.getsource(E.Executor.run_plan)
i_dec = rp.index('self.log("league_lap_decision"')
i_reg = rp.index('self.log("plan_regress"')
ck("the lap decision is taken before the replay", i_dec < i_reg)
blk = rp[rp.index("_in_league = bool("):i_reg]
ck("...only for a wipe the league made", "_in_league and _rg < idx" in blk)
ck("...and only from the second lap lost (the first replays)",
   'len(getattr(self, "_league_laps", None) or []) >= 2' in blk)
ck("...ending the plan as a failure the rewrite reads",
   'self.failed_subgoal = sg["id"]' in blk and "return False" in blk
   and 'self.log("plan_failed_at"' in blk)
ww = inspect.getsource(E.Executor._watch_for_a_wipe)
ck("the wipe watcher says whether the league put the deeds back",
   "self._regress_league = was_map in LEAGUE_MAPS" in ww)
ex = (ROOT / "planner/executor.py").read_text()
ck("each battle turn names the foe on screen",
   'foe=(f"{_bf.get(\'species\')} L{_bf.get(\'level\')}"' in ex)
nf = inspect.getsource(E.Executor._note_fight)
ck("a fight's recap lists every foe seen and the party's levels",
   '"foes": foes_seen' in nf and '"party": [f"{m.get(\'species\')} L{m.get(\'level\')}"' in nf)
lg = inspect.getsource(E.Executor.log)
ck("a lap keeps who was beaten on it", '"beaten": list(getattr(self, "_lap_wins"' in lg)
ck("a failed plan still saves the game where it stands (the lobby, the loss kept)",
   "(after a failed plan, to keep what it earned)" in ex)

rows = [
    {"kind": "fight_recap", "who": "LORELEI", "where": "LORELEIS_ROOM", "lost": False},
    {"kind": "fight_recap", "who": "LORELEI", "where": "LORELEIS_ROOM", "lost": False},
    {"kind": "fight_recap", "who": "BRUNO", "where": "BRUNOS_ROOM", "lost": True,
     "foes": ["ONIX L53", "HITMONCHAN L55"], "party": ["GRAVELER L50", "KADABRA L44"]},
    {"kind": "fight_recap", "who": "LORELEI", "where": "LORELEIS_ROOM", "lost": False},
    {"kind": "fight_recap", "who": "a trainer", "where": "BRUNOS_ROOM", "lost": False},
    {"kind": "fight_recap", "who": "BRUNO", "where": "BRUNOS_ROOM", "lost": True,
     "foes": ["ONIX L53"], "party": ["GRAVELER L51", "KADABRA L44"]},
    {"kind": "league_lap_decision", "subgoal": "defeat_bruno", "laps": 2},
    {"kind": "fight_recap", "who": "BROCK", "where": "PEWTER_GYM", "lost": True},
]
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "j.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    t = A.journal_text(p)
lines = [l for l in t.splitlines() if "LEAGUE" in l or "ENDED" in l]
ck("each lost lap is one line", sum("LEAGUE  lap" in l for l in lines) == 2, lines)
ck("...naming who went down that lap, once each",
   any("lap 1 ended in a blackout: beat LORELEI; lost to BRUNO" in l for l in lines), lines)
ck("...what the winner sent out and the party then",
   any("who sent out ONIX L53, HITMONCHAN L55 — your party then: GRAVELER L50, KADABRA L44" in l
       for l in lines), lines)
ck("...no unnamed fight in the beaten list",
   any("lap 2 ended in a blackout: beat LORELEI; lost to BRUNO" in l for l in lines), lines)
ck("the plan's end at the lobby is said", any("ENDED   the plan ended in the lobby after lap 2" in l
                                             for l in lines), lines)
ck("a gym loss is not a lap", not any("BROCK" in l for l in lines))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
