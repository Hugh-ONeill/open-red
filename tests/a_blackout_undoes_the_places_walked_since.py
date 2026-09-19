#!/usr/bin/env python3
"""A blackout undoes the place steps walked since the last step that still
holds, and the plan regresses to the first of them.

Run 27, 2026-09-18, the Elite Four: lobby -> defeat_lorelei (map BRUNOS_ROOM)
-> defeat_bruno (map AGATHAS_ROOM) -> defeat_agatha (map LANCES_ROOM) ...;
the Champion wiped the party, it woke in the lobby, the plan still stood at
defeat_agatha, and the run in Lorelei's room with her unbeaten tried the
north door fifteen times (user: "we might need to make the e4 repressable
once per attempt so it can actually get through after failing on the first
go-around").

Pinned: a wake in the lobby regresses to defeat_lorelei, the first place
step after the last step that still holds; the note names the undone steps;
flag steps still regress as before. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


subs = [{"id": "reach_indigo_plateau", "done_when": {"map": "INDIGO_PLATEAU"}},
        {"id": "heal_at_plateau", "done_when": {"party_healthy": True}},
        {"id": "enter_elite_four_chamber", "done_when": {"map": "INDIGO_PLATEAU_LOBBY"}},
        {"id": "defeat_lorelei", "done_when": {"map": "BRUNOS_ROOM"}},
        {"id": "defeat_bruno", "done_when": {"map": "AGATHAS_ROOM"}},
        {"id": "defeat_agatha", "done_when": {"map": "LANCES_ROOM"}},
        {"id": "defeat_champion", "done_when": {"hall_of_fame": True}}]


def fake():
    ex = object.__new__(E.Executor)
    ex.plan = {"subgoals": subs}
    ex._cur_sg_idx = 5
    ex._wipe_watch = (47000, "LANCES_ROOM", "LANCES_ROOM|5,0")
    ex._faint_at = None
    ex._cur_target = None
    ex._plan_regress = None
    ex.logs = []
    ex.log = lambda k, **kw: ex.logs.append((k, kw))
    ex._where = lambda o: "INDIGO_PLATEAU_LOBBY|8,0"
    return ex


woke = {"mode": "overworld", "money": 23500, "map": {"id": "INDIGO_PLATEAU_LOBBY"},
        "party": [{"species": "LAPRAS", "hp": 200, "max_hp": 200}], "flags": [], "badges": []}
ex = fake()
note = ex._watch_for_a_wipe(woke)
ck("a wake in the lobby regresses to defeat_lorelei", ex._plan_regress == 3, ex._plan_regress)
ck("...and the note names the undone place steps",
   "defeat_lorelei, defeat_bruno" in (note or ""), note)
ck("...not the lobby step, which still holds",
   "enter_elite_four_chamber" not in (note or "").split("UNDONE")[-1], note)

subs_flag = [{"id": "get_key", "done_when": {"flag": "EVENT_X"}},
             {"id": "walk_on", "done_when": {"map": "ROUTE_1"}},
             {"id": "last", "done_when": {"map": "ROUTE_2"}}]
ex = fake()
ex.plan = {"subgoals": subs_flag}
ex._cur_sg_idx = 2
ex._wipe_watch = (1000, "ROUTE_1", "ROUTE_1|0,0")
ex._where = lambda o: "PEWTER_POKECENTER|0,0"
woke2 = dict(woke, money=500, map={"id": "PEWTER_POKECENTER"})
ex._watch_for_a_wipe(woke2)
ck("a flag step that came undone still regresses first", ex._plan_regress == 0, ex._plan_regress)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
