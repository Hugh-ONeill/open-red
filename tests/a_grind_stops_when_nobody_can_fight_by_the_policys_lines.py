#!/usr/bin/env python3
"""A grind stops when nobody can fight by the policy's own HP lines.

Run 47, Route 2 (2026-10-10): a slot_level step for PIDGEY. After two
fights PIDGEY was at 6/18 (the train block fights only at 0.4) and
BULBASAUR at 7/34 (the spec flees a wild under 0.2). The grind re-sent
anyway: five wilds met with a switch and a run, then a run failed, PIDGEY
fought a PIDGEY L5 at 6 HP and the party blacked out.

Pinned on that party: the grind is spent and says who stands where; one
member above its line keeps it going; the trainee's own line is the train
block's, a helper's is the flee line; and the grind loop checks it after
each battle. Synthetic.
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


E.ACTIVE_SPEC = {"flee_wild": {"when_traversal": True, "hp_below": 0.2},
                 "train": json.loads((ROOT / "plans/train_model_v3.json").read_text())["train"]}
SG = {"id": "grind_pidgey",
      "done_when": {"slot_level": {"slot": 2, "min": 12, "who": {"species": "PIDGEY"}}}}


def party(pidgey_hp, bulb_hp):
    return {"party": [{"species": "PIDGEY", "level": 4, "hp": pidgey_hp, "max_hp": 18},
                      {"species": "BULBASAUR", "level": 12, "hp": bulb_hp, "max_hp": 34}]}


ex = E.Executor.__new__(E.Executor)
why = ex._grind_spent(SG, party(6, 6))
ck("run 47's party is spent", bool(why), why)
ck("...and the reason names both", "PIDGEY 6/18" in why and "BULBASAUR 6/34" in why, why)
ck("a helper above the flee line keeps the grind going", ex._grind_spent(SG, party(6, 10)) == "")
ck("the trainee at its own fight line keeps it going", ex._grind_spent(SG, party(8, 6)) == "")
ck("a trainee above the flee line but under its own is not enough",
   bool(ex._grind_spent(SG, party(5, 6))))
E.ACTIVE_SPEC = {"flee_wild": {"hp_below": 0.2}}
ck("with no train block only the flee line counts", ex._grind_spent(SG, party(5, 6)) == "")
src = (ROOT / "planner/executor.py").read_text()
ck("the grind loop asks after each battle and stops",
   'if op == "grind" and not pred_holds(done, obs):\n                        _spent = self._grind_spent(sg, obs)' in src)
ck("the round says it stopped and why", '" (stopped early: {self._grind_spent_note})"' in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
