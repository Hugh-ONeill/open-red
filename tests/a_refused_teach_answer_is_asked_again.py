#!/usr/bin/env python3
"""A teach answer that cannot be carried out is asked again with the
refusal quoted, and one already on the record is re-opened once.

Run 27, 2026-09-18: TM06 arrived, the model chose VENUSAUR and to forget
CUT; CUT is an HM move, the answer was marked unusable and recorded as
asked, and the question never came back — TOXIC sat in the bag (user:
"were there ever explicit denials of teaching mega-drain or toxic to
venu?").

Pinned: a refused answer is re-asked within the same question, up to three
tries, with every refusal quoted; a usable answer is taught; a record that
holds a refusal and was not re-asked is open again; one that was re-asked
and still refused is closed. Synthetic (model and game stubbed).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


WHO = [(3, "VENUSAUR", ["RAZOR_LEAF", "BODY_SLAM", "LEECH_SEED", "CUT"])]


def fake(answers, asked=None):
    ex = object.__new__(E.Executor)
    ex._tm_asked = dict(asked or {})
    ex.model = "m"
    ex.log = lambda *a, **k: None
    ex.settle = lambda: {"ok": True}
    sent = []
    ex._send_safe = lambda op, **kw: (sent.append((op, kw)) or {"result": {"ok": True}})
    ex._teachable_now = lambda obs: [("TM_TOXIC", "TOXIC", WHO)]
    ex._teach_question = lambda obs, item, move, who, sg: "THE QUESTION"
    seen = []
    it = iter(answers)
    E.brock_probe.chat = lambda msgs, model: (seen.append(msgs[1]["content"]) or json.dumps(next(it)))
    return ex, sent, seen


SG = {"id": "x"}
ex, sent, seen = fake([{"teach": 3, "forget": "CUT", "why": "stall"},
                       {"teach": 3, "forget": "LEECH_SEED", "why": "stall"}])
ex._ask_teach({}, SG)
ck("an answer that forgets an HM move is asked again",
   len(seen) == 2 and "YOUR LAST ANSWER COULD NOT BE CARRIED OUT: CUT is an HM move and cannot be forgotten" in seen[1], seen)
ck("...and the usable second answer is taught",
   sent == [("use_item", {"item": "TM_TOXIC", "slot": 3, "forget": "LEECH_SEED"})], sent)
ck("...and the record keeps it, not the refusal",
   ex._tm_asked["TM_TOXIC|VENUSAUR"]["forget"] == "LEECH_SEED" and not ex._tm_asked["TM_TOXIC|VENUSAUR"]["bad"])

ex, sent, seen = fake([{"teach": 3, "forget": "CUT"}] * 3)
ex._ask_teach({}, SG)
ck("three refused answers teach nothing and close the question",
   sent == [] and len(seen) == 3 and ex._tm_asked["TM_TOXIC|VENUSAUR"]["reasked"] is True, (sent, len(seen)))
ck("...with every refusal quoted on the last try", seen[2].count("CUT is an HM move") == 2, seen[2:])

OLD = {"TM_TOXIC|VENUSAUR": {"teach": 3, "forget": "CUT", "why": "stall",
                             "bad": "CUT is an HM move and cannot be forgotten"}}
ex, sent, seen = fake([{"teach": 3, "forget": "LEECH_SEED"}], asked=OLD)
ex._ask_teach({}, SG)
ck("a refusal already on the record is asked again, quoted from the first question",
   len(seen) == 1 and "CUT is an HM move" in seen[0]
   and sent == [("use_item", {"item": "TM_TOXIC", "slot": 3, "forget": "LEECH_SEED"})], (seen, sent))
closed = {"TM_TOXIC|VENUSAUR": dict(OLD["TM_TOXIC|VENUSAUR"], reasked=True)}
ex, sent, seen = fake([{"teach": 3}], asked=closed)
ex._ask_teach({}, SG)
ck("...but not once it has been re-asked", seen == [] and sent == [])
ex, sent, seen = fake([{"teach": None, "why": "not worth it"}])
ex._ask_teach({}, SG)
ck("a plain no is a no, asked once", len(seen) == 1 and sent == [] and not ex._tm_asked["TM_TOXIC|VENUSAUR"]["reasked"])

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
