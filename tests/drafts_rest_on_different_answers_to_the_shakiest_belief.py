#!/usr/bin/env python3
"""The author's drafts rest on different answers to the goal's shakiest belief.

Three independent drafts were mostly one plan, and on the S.S. Ticket leg all
of them shared a belief nothing in the run supported (the ticket is in
Vermilion). With RED_DRAWS=premise (the default) the author first asks what
the goal assumes and where each belief comes from, takes the model's ideas on
different answers to the shakiest one, and writes one draft per idea; every
draft call also carries WHAT PEOPLE HAVE SAID, which before this only the
review after the pick saw (tools/author_ab.py draws, 2026-10-03).

Pinned: one ideas call, under its own system prompt, carrying the heard lines;
draft i is told idea i and the heard lines; an unreadable ideas reply still
drafts, with the heard lines and no idea; one draft asks no ideas;
RED_DRAWS=sample drafts exactly as before; no walked record, no heard lines.
Synthetic: the model, the drafter and the pick are stand-ins.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
os.environ["RED_WARM"] = "0"
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


SAID = "\n\nWHAT PEOPLE HAVE SAID, and where they said it:\n  in ROUTE_25|10,2:\n    HIKER: You're going to see BILL?"
CALLS, DRAFTS = [], []
REPLY = {"text": json.dumps({"assumptions": [{"belief": "the ticket is in Vermilion", "source": "memory of the game"}],
                             "ideas": ["Go south to Vermilion.", "Visit the cottage north of here.",
                                       "Search the houses in town."]})}


def fake_chat(msgs, model, retries=2, think=False, temp=None):
    CALLS.append(msgs)
    return REPLY["text"]


def fake_author(goal, model, rounds=5, start=None, think=False, temp=None, extra=""):
    DRAFTS.append(extra)
    n = len(DRAFTS)
    return {"goal": goal, "subgoals": [{"id": f"s{n}", "done_when": {"map": f"MAP_{n}"}}]}


A.brock_probe.chat = fake_chat
A.author = fake_author
A.people_said_text = lambda observed: SAID if observed else ""
A.archive_draft = lambda goal, p: None
A.pick_plan = lambda goal, plans, model, start=None: plans[0]
A.build_prompt = lambda goal, start: f"GOAL: {goal}"


def run(mode, draws=3, observed="run/explored.json"):
    CALLS.clear()
    DRAFTS.clear()
    A.DRAWS_MODE = mode
    A.author_best_of("Retrieve the S.S. Ticket", "m", draws=draws, start="here", observed=observed)


run("premise")
ck("one ideas call, under its own system prompt",
   len(CALLS) == 1 and CALLS[0][0]["content"] == A.PREMISE_SYS, CALLS)
ck("...asking for the goal's assumptions and as many ideas as drafts",
   CALLS and "ASSUMES" in CALLS[0][-1]["content"] and "name 3 ideas" in CALLS[0][-1]["content"], CALLS)
ck("...with the heard lines in front of it", CALLS and SAID in CALLS[0][-1]["content"])
ck("draft i is told idea i", len(DRAFTS) == 3 and all(
    f"PLAN THIS IDEA, and only this one: {idea}" in DRAFTS[i]
    for i, idea in enumerate(json.loads(REPLY["text"])["ideas"])), DRAFTS)
ck("...and every draft carries the heard lines", all(d.startswith(SAID) for d in DRAFTS), DRAFTS)

REPLY["text"] = "I think the ticket is somewhere."
run("premise")
REPLY["text"] = json.dumps({"ideas": ["a", "b", "c"]})
ck("an unreadable ideas reply still drafts, with the heard lines and no idea",
   len(DRAFTS) == 3 and all(d == SAID for d in DRAFTS), DRAFTS)

run("premise", draws=1)
ck("one draft asks for no ideas", not CALLS and DRAFTS == [SAID], (CALLS, DRAFTS))

run("sample")
ck("RED_DRAWS=sample drafts as before: no ideas call, nothing added",
   not CALLS and DRAFTS == ["", "", ""], (CALLS, DRAFTS))

run("premise", observed=None)
ck("with no walked record there are no heard lines to add",
   CALLS and SAID not in CALLS[0][-1]["content"] and all(not d.startswith("\n\nWHAT PEOPLE") for d in DRAFTS),
   DRAFTS)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
