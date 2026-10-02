#!/usr/bin/env python3
"""What the run said is shown as belief, not evidence, and its newest
sentence is shown beside its most repeated.

Run 20 (2026-10-01): about twenty rounds restated "the Silph Scope is given by
Mr. Fuji"; one round reasoned "I must obtain the Silph Scope from another
source first". Sorted by count, the restatement led, and the wording rung
reworded the leg to "from Mr. Fuji" because "the executor's logs confirm"
it, which wrote the false premise into the outline.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("RED_BRIDGE_DIR", tempfile.mkdtemp())
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(n, ok, d=""):
    checks.append((n, bool(ok), d))


old = "The Scope is given by Mr. Fuji, who is behind the Ghost."
rows = [{"kind": "plan_start", "goal": "Retrieve the Silph Scope"},
        {"kind": "escalate_start", "subgoal": "get_scope", "goal": "get it"}]
for i in range(7):
    rows.append({"kind": "escalate_proposal", "subgoal": "get_scope", "plan": f"{old} Try {i % 3}.",
                 "macro": [{"op": "explore"}]})
rows.append({"kind": "escalate_proposal", "subgoal": "get_scope",
             "plan": "This implies I must obtain the Silph Scope from another source first.",
             "macro": [{"op": "go", "to": "CELADON_CITY"}]})
td = Path(tempfile.mkdtemp())
j = td / "log.jsonl"
j.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

w = A.words_text(j)
ck("the run's words are labeled as belief", "BELIEVED" in w and "still one belief" in w, w[:300])
ck("...and the newest sentence is shown though it was said once",
   "the newest) \"This implies I must obtain" in w, w)
t = A.tried_text([json.loads(l) for l in j.read_text().splitlines()])
ck("the per-step digest says the same", "BELIEVED then" in t, t[:400])
ck("...and keeps the newest beside the most repeated",
   "the newest): \"This implies I must obtain" in t, t)

rows.append({"kind": "escalate_proposal", "subgoal": "get_scope",
             "plan": "I am stuck in a paradox: the Ghost needs the Scope and Fuji gives it.",
             "macro": [{"op": "explore"}]})
j.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
jt = A.journal_text(j)
ck("a round that called it circular is quoted back with the logic, not an answer",
   "CALLED THIS CIRCULAR, 1 time(s)" in jt and "one of the facts" in jt
   and "Celadon" not in jt.split("CALLED THIS CIRCULAR")[1], jt[-500:])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:400]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
