#!/usr/bin/env python3
"""Run of record 15 (2026-09-28), the ticket stretch again, three closures.

1. Every rewrite walked to VERMILION_CITY after the last plan failed walking
   there — with that fact in front of every draft. A rewrite whose steps
   before that place are only travel is now refused; a plan that does
   something first may go there after it.
2. After the Cell Separator, BILLSHOUSE_BILL1 stood in Bill's house never
   spoken to, and "Talk to Bill" was turned down as ALREADY DONE. A proposal
   naming someone seen and never pressed is not done; the author is told
   who, and where.
3. Catch-ahead threw at any wild that answered a later leg without asking
   (user: "i dont want to end up with an exploding electrode"). It now asks
   the new-species question and throws only on a yes, a stored yes included.

Synthetic.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


run = Path(tempfile.mkdtemp(prefix="r15_"))
(run / "executor_log.jsonl").write_text("\n".join(json.dumps(r) for r in [
    {"kind": "plan_start", "goal": "Retrieve the S.S. Ticket", "t": 1},
    {"kind": "escalate_context", "subgoal": "travel_to_vermilion",
     "target": "map:VERMILION_CITY", "t": 2},
    {"kind": "escalate_end", "subgoal": "travel_to_vermilion", "success": False, "t": 3},
]) + "\n")
G = "Retrieve the S.S. Ticket"
bare = {"subgoals": [{"id": "back", "done_when": {"area": "CERULEAN_CITY|20,0"}},
                     {"id": "heal", "done_when": {"party_healthy": True}},
                     {"id": "go", "done_when": {"map": "VERMILION_CITY"}}]}
deed = {"subgoals": [{"id": "bill", "done_when": {"has_item": {"S_S_TICKET": 1}}},
                     {"id": "go", "done_when": {"map": "VERMILION_CITY"}}]}
away = {"subgoals": [{"id": "r25", "done_when": {"map": "ROUTE_25"}}]}
p = A.same_failed_walk_problems(bare, G, run)
ck("a rewrite that only travels to where the last plan failed is refused",
   p and "walks to VERMILION_CITY" in p[0] and "same walk" in p[0], p)
ck("...one that does something first may go there after it",
   A.same_failed_walk_problems(deed, G, run) == [])
ck("...one that goes somewhere else is untouched",
   A.same_failed_walk_problems(away, G, run) == [])
ck("...and another objective's plan is untouched",
   A.same_failed_walk_problems(bare, "Reach Vermilion City", run) == [])
ck("validate() runs it", "probs += same_failed_walk_problems(plan)" in
   (ROOT / "planner/author.py").read_text())

(run / "explored.json").write_text(json.dumps({
    "sightings": {"BILLS_HOUSE|0,2": ["BILLSHOUSE_BILL1", "CELL_SEPARATION_SYSTEM",
                                      "TEXT_BILLSHOUSE_SIGN"],
                  "CERULEAN_GYM|0,1": ["CERULEANGYM_MISTY"]},
    "touched": {"BILLS_HOUSE|0,2": ["CELL_SEPARATION_SYSTEM"],
                "CERULEAN_GYM|0,1": ["CERULEANGYM_MISTY"]}}))
ex = run / "explored.json"
ck("someone seen and never spoken to, named in the proposal, is found",
   A.untouched_named("Talk to Bill in Cerulean City", ex)
   == [("BILLS_HOUSE|0,2", "BILLSHOUSE_BILL1")])
ck("...someone already spoken to is not",
   A.untouched_named("Defeat Misty for the Cascade Badge", ex) == [])
ck("...nor a sign, nor a place word",
   A.untouched_named("Read the sign in Bill's house", ex)
   == [("BILLS_HOUSE|0,2", "BILLSHOUSE_BILL1")]
   and A.untouched_named("Reach Cerulean City", ex) == [])
A.brock_probe.chat = lambda *a, **k: json.dumps({"done": True, "why": "met Bill"})
ck("the already-done check refuses while that person stands unspoken to",
   A.check_already_done("Talk to Bill in Cerulean City", "start", "m", observed=ex) is False)
src = (ROOT / "planner/author.py").read_text()
ck("the author is told who, and where", "+ untouched_named_text(goal)" in src)

exs = (ROOT / "planner/executor.py").read_text()
ck("catch-ahead asks the new-species question before it throws",
   "_yes = bool(self._ask_new_species(obs, subgoal))" in exs
   and 'self.log("catch_ahead_declined"' in exs)
ck("...and an answer already given stands, a yes included",
   "_prior = (getattr(self, \"_new_species_asked\", {}) or {}).get(_sp)" in exs
   and '_yes = bool(_prior.get("catch"))' in exs)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
