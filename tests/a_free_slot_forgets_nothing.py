#!/usr/bin/env python3
"""A machine taught into a free slot forgets nothing, whatever the answer
named.

Run 60, 2026-10-21: TM01 went to GEODUDE L8, who knew only TACKLE; the
model answered forget=TACKLE, the game learned MEGA_PUNCH into the empty
slot, and the log read "taught MEGA_PUNCH to slot 3, forgetting TACKLE"
(user: "it taught megapunch to ivysaur?").

Pinned: with fewer than four moves no forget= is sent or recorded; with
four, the named forget still goes through. Synthetic (model and game
stubbed).
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


def fake(who, answer):
    ex = object.__new__(E.Executor)
    ex._tm_asked = {}
    ex.model = "m"
    ex.log = lambda *a, **k: None
    ex.settle = lambda: {"ok": True}
    sent = []
    ex._send_safe = lambda op, **kw: (sent.append((op, kw)) or {"result": {"ok": True}})
    ex._teachable_now = lambda obs: [("TM_MEGA_PUNCH", "MEGA_PUNCH", who)]
    ex._teach_question = lambda obs, item, move, who, sg: "THE QUESTION"
    E.brock_probe.chat = lambda msgs, model: json.dumps(answer)
    return ex, sent


SG = {"id": "x"}
ex, sent = fake([(3, "GEODUDE", ["TACKLE"])], {"teach": 3, "forget": "TACKLE"})
ex._ask_teach({}, SG)
ck("a free slot is taught with no forget sent",
   sent == [("use_item", {"item": "TM_MEGA_PUNCH", "slot": 3})], sent)
ck("...and none recorded", ex._tm_asked["TM_MEGA_PUNCH|GEODUDE"]["forget"] is None,
   ex._tm_asked)

ex, sent = fake([(3, "GEODUDE", ["TACKLE", "DEFENSE_CURL", "ROCK_THROW", "SELFDESTRUCT"])],
                {"teach": 3, "forget": "TACKLE"})
ex._ask_teach({}, SG)
ck("four moves still forget the one named",
   sent == [("use_item", {"item": "TM_MEGA_PUNCH", "slot": 3, "forget": "TACKLE"})], sent)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
