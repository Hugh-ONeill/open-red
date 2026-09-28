#!/usr/bin/env python3
"""Four ways run of record 14 lost the S.S. Ticket stretch (2026-09-28), each
closed.

1. check-done crossed off "Rescue Bill from the cave on Route 25" on "The
   player has entered Bill's house, which is only possible after rescuing
   Bill" — a remembered rule about what must come first, with no hedge word.
2. The missing rung inserted "Obtain the S.S. Ticket" in front of a list that
   held "Retrieve the S.S. Ticket"; the pushes that followed put the ticket
   behind Vermilion.
3. Bill's answer — "When I'm in the TELEPORTER, go to my PC and run the Cell
   Separation System!" — came back with a question box open, no map, so the
   region read None and the line was dropped; only "Help me out here!" was
   kept.
4. After the first plan failed walking to VERMILION_CITY, the rewrite walked
   to VERMILION_CITY again: the author was never told.

Pinned: the inference guard catches "only possible after" / "which means" and
still passes a reason that names a record fact, a party member included; a
same-things same-verb-kind proposal is already listed; an answered question's
reply is filed under the asker, in the room after the answer; the author is
told the places the last plan for THIS objective failed to walk to. Synthetic.
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


# 1 --------------------------------------------------------------- inference
ck("'only possible after' is inference",
   A._inferred("The player has entered Bill's house, which is only possible "
               "after rescuing Bill from the cave on Route 25."))
ck("...and so is 'which means'",
   A._inferred("It has fired, which means the leg is done."))
ck("a reason that states the record is not",
   not A._inferred("The player has the CASCADEBADGE and EVENT_BEAT_MISTY has fired."))
tmp = Path(tempfile.mkdtemp(prefix="ticket_"))
(tmp / "obs.json").write_text(json.dumps({"flags": [], "bag": {}, "badges": [],
                                          "party": [{"species": "IVYSAUR"}]}))
ck("a party member named in the reason is a record fact",
   A._record_fact_named("IVYSAUR is a GRASS type, which means the party holds one",
                        tmp / "obs.json") == "IVYSAUR in the party")
ck("...and Bill's house is not",
   A._record_fact_named("entered Bill's house, which is only possible after "
                        "rescuing Bill", tmp / "obs.json") == "")

# 2 --------------------------------------------------------------- duplicates
ck("obtain and retrieve are one kind of deed",
   A._deed_class("Obtain the S.S. Ticket") == A._deed_class("Retrieve the S.S. Ticket") == "get")
ck("...and reaching is another", A._deed_class("Reach Vermilion City") == "reach")
src = (ROOT / "planner/author.py").read_text()
ck("the missing rung counts the same deed in other words as listed",
   "if _names(ins) and _names(t) == _names(ins)\n"
   "                      and _deed_class(t) == _deed_class(ins)), None)" in src
   and "if _norm_obj(ins) in listed or _same:" in src)

# 3 --------------------------------------------------------------- answers
ex = (ROOT / "planner/executor.py").read_text()
ck("an answer is filed under whoever was pressed last",
   'elif op == "menu" and getattr(self, "_last_talker", None):\n'
   '                    who = self._last_talker' in ex)
ck("...in the room after the answer when the one before had no map",
   'if "None" in reg:\n                    reg = self._where(obs)' in ex)

# 4 --------------------------------------------------------------- failed walk
(tmp / "executor_log.jsonl").write_text("\n".join(json.dumps(r) for r in [
    {"kind": "plan_start", "goal": "Retrieve the S.S. Ticket", "t": 1},
    {"kind": "escalate_context", "subgoal": "travel_to_vermilion",
     "target": "map:VERMILION_CITY", "t": 2},
    {"kind": "escalate_end", "subgoal": "travel_to_vermilion", "success": False, "t": 3},
]) + "\n")
t = A.failed_walk_text("Retrieve the S.S. Ticket", tmp)
ck("the author is told where this objective's last plan failed to walk",
   "FAILED WALKING TO: VERMILION_CITY (step travel_to_vermilion)" in t, t)
ck("...and nothing for another objective",
   A.failed_walk_text("Reach Vermilion City", tmp) == "")
ck("build_prompt carries it", "+ failed_walk_text(goal)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
