#!/usr/bin/env python3
"""Neither the wording rung nor the missing rung may move a leg towards the
place its plan has just failed to walk to.

Run of record 11 (2026-09-27): the plan for "Retrieve the S.S. Ticket"
failed on go_to_vermilion_city from Cerulean, and the wording rung
reworded the leg to "Obtain the S.S. Ticket from Bill in Vermilion City"
straight away. The refusal for exactly this was built on 2026-09-14 and
never fired live: the wording rung handed it the journal's RENDERED text,
it tried to open that as a file, and the error was swallowed. The missing
rung, whose REWORD: answers are the same rewrite by another door, never
asked at all (run 10: "...from the Captain in Vermilion City").

Pinned: the wording rung refuses it when given the journal's path; the CLI
passes that path; the missing rung turns it down, says why in the re-ask,
and still takes the next answer; an answer that does not name the failed
place is untouched. Synthetic: the model is stubbed.
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


tmp = Path(tempfile.mkdtemp(prefix="failedwalk_"))
(tmp / "run").mkdir()
os.chdir(tmp)
J = tmp / "run/executor_log.jsonl"
J.write_text("\n".join(json.dumps(r) for r in [
    {"kind": "plan_start", "plan": "leg_12_retrieve_the_s_s_ticket.json", "t": 1},
    {"kind": "escalate_context", "subgoal": "go_to_vermilion_city",
     "target": "map:VERMILION_CITY", "t": 2},
    {"kind": "escalate_end", "subgoal": "go_to_vermilion_city",
     "success": False, "t": 3},
    {"kind": "chain_subgoal_failed", "subgoal": "go_to_vermilion_city", "t": 3},
]) + "\n")

GOAL = "Retrieve the S.S. Ticket"
ahead = [(12, GOAL), (13, "Reach Vermilion City")]
behind = [(11, "Defeat Misty for the Cascade Badge")]
A.recent_events = lambda: ""
A.done_ledger_text = lambda: ""
A.check_already_done = lambda *a, **k: False

# ---------------------------------------------------------------- wording
said = []


def wording_chat(msgs, model):
    said.append(msgs[-1]["content"])
    return json.dumps({"why": "Bill is in Vermilion",
                       "reword": "Obtain the S.S. Ticket from Bill in Vermilion City"})


A.brock_probe.chat = wording_chat
new = A.check_wording(GOAL, ahead, behind, "start", "rendered account", "m",
                      asked=(), journal_path=J)
ck("the wording rung refuses a rewrite towards the place the plan failed to reach",
   new == "", new)
src = (ROOT / "planner/author.py").read_text()
ck("...and the chain hands it the journal's path, not its rendered text",
   "journal_path=args.journal" in src)

# ---------------------------------------------------------------- missing
replies = [
    {"why": "the S.S. Ticket is obtained from Bill in his house",
     "insert": "Obtain the S.S. Ticket from Bill in Vermilion City"},
    {"why": "the S.S. Ticket is obtained from Bill in his house",
     "insert": "Obtain the S.S. Ticket from Bill on Route 25"},
]
asks = []


def missing_chat(msgs, model):
    asks.append(msgs[-1]["content"])
    return json.dumps(replies[len(asks) - 1])


A.brock_probe.chat = missing_chat
got = A.check_missing(GOAL, ahead, "start", "m", behind=behind, journal=J)
ck("the missing rung turns down a leg named after the place it failed to reach",
   "Vermilion" not in got, got)
ck("...says why in the re-ask",
   len(asks) == 2 and "VERMILION_CITY: this leg's plan has just failed walking there"
   in asks[1], asks[1:][:1])
ck("...and still takes the next answer",
   got.endswith("Obtain the S.S. Ticket from Bill on Route 25"), got)

asks.clear()
replies[:] = [{"why": "the S.S. Ticket is obtained from Bill in his house",
               "insert": "Obtain the S.S. Ticket from Bill on Route 25"}]
got = A.check_missing(GOAL, ahead, "start", "m", behind=behind, journal=J)
ck("an answer that does not name the failed place is untouched",
   len(asks) == 1 and got.endswith("from Bill on Route 25"), got)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
