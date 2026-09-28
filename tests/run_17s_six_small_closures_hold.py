#!/usr/bin/env python3
"""Run of record 17 (2026-09-28), six closures.

1. The same-walk refusal read only the journal's LAST plan: the ticket leg,
   pushed away and back, re-authored its Vermilion walk unrefused. It now
   reads this objective's own most recent plan, and an event fired since
   re-opens the walk — a numbered trainer beaten on the way does not.
2. The missing rung returned at once on "no parseable answer"; the ladder
   pushed the ticket behind Vermilion. Rung asks are asked again.
3. "a party Pokemon knows CUT" was refused as not done because CUT matched
   CUT_TREE; field moves and obstacles are not people.
4. status.txt printed the carried step's DVs and OT id; it renders
   conditions as the page does.
5. "Route 24 has no wild grass" on 50 of its 720 cells seen; walked routes
   with no wild ground on screen are said to be not known, and ground seen
   and never fought on is named.
6. Three Pewter <-> Route 3 round trips said only "crossed — now on
   PEWTER_CITY"; a crossing that undoes the last says so.

Synthetic, plus source checks.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def journal(rows):
    d = Path(tempfile.mkdtemp(prefix="r17_"))
    (d / "executor_log.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return d


T = "Retrieve the S.S. Ticket"
base = [{"kind": "plan_start", "goal": T},
        {"kind": "escalate_context", "subgoal": "go", "target": "map:VERMILION_CITY"},
        {"kind": "escalate_end", "subgoal": "go", "success": False},
        {"kind": "plan_start", "goal": "Reach Vermilion City"},
        {"kind": "flag_fired", "flag": "EVENT_BEAT_ROUTE_24_TRAINER_3"}]
ck("1: this objective's own last plan is read, not the journal's last",
   A._failed_walk_places(T, journal(base)) == [("go", "VERMILION_CITY")])
ck("1: a real event since re-opens the walk",
   A._failed_walk_places(T, journal(base + [{"kind": "flag_fired",
                                             "flag": "EVENT_GOT_SS_TICKET"}])) == [])

calls = []


def flaky(msgs, model):
    calls.append(1)
    return "I think so" if len(calls) == 1 else '{"insert": null, "why": "x"}'


A.brock_probe.chat = flaky
ck("2: an unreadable reply is asked again",
   A.chat_json([], "m") == '{"insert": null, "why": "x"}' and len(calls) == 2)
src = (ROOT / "planner/author.py").read_text()
ck("2: the blocker, missing, wording and check-done asks use it",
   src.count("reply = chat_json(") >= 4)

ex = Path(tempfile.mkdtemp(prefix="r17u_")) / "explored.json"
ex.write_text(json.dumps({"sightings": {"VIRIDIAN_CITY|17,0": ["CUT_TREE"],
                                        "BILLS_HOUSE|0,2": ["BILLSHOUSE_BILL1"]},
                          "touched": {}}))
ck("3: a field move is not a person, nor is a bush",
   A.untouched_named("a party Pokemon knows CUT", ex) == [])
ck("3: a person still is",
   A.untouched_named("Talk to Bill", ex) == [("BILLS_HOUSE|0,2", "BILLSHOUSE_BILL1")])

exs = (ROOT / "planner/executor.py").read_text()
ck("4: status.txt renders a carried condition as the page does",
   'f"{c} NOT achieved {pred_text.dumps(_dws.get(c) or {})}"' in exs)

x = object.__new__(E.Executor)
x._wild_seen = {"ROUTE_1": {"grass": 104}, "PALLET_TOWN": {"grass": 4}}
x.visits = {"ROUTE_1|0,0": 3, "ROUTE_24|4,4": 2, "PALLET_TOWN|0,0": 1}
w = x._wild_unknown_words("CERULEAN_CITY", {"ROUTE_1"})
ck("5: a walked route with no wild ground on screen is said not known",
   "ROUTES YOU HAVE WALKED WHERE NO WILD GROUND HAS COME ON SCREEN YET: ROUTE_24" in w
   and "whether they have any is not known" in w, w)
ck("5: ground seen and never fought on is named",
   "WILD GROUND YOU HAVE SEEN AND NEVER FOUGHT ON: PALLET_TOWN (4 cell(s) of tall grass)" in w, w)
ck("5: ground already fought on is not repeated there", "ROUTE_1 (" not in w)

ck("6: a crossing back to where the last came from says so",
   "where you crossed \"\n" in exs and "from last time: this crossing undid that one" in exs
   and 'if _prev and _prev[0] == _to and _prev[1] == _frm:' in exs)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
