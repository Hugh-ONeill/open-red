#!/usr/bin/env python3
"""A rewrite or an inserted leg that says a thing comes from somewhere the
game does not keep it is refused, and the model is told the shape to fix,
never the fact.

Run 28 rewrote leg 13 from "Retrieve the S.S. Ticket from Bill" to
"...from Bill on the S.S. Anne" — the ship the ticket buys passage onto —
and then wrote four plans to board it, each needing the ticket it was
fetching (user, 2026-09-19: "it should have been caught and guarded against
in the first place"). The same rung had earlier inserted "Obtain the Coin
Case from the Game Corner", where the case is used and not given.

THE DANGER IS THE OTHER WAY TOO (user, 2026-09-20: "what were running the
danger of is this grabbing true facts too"): the check reads only the
clause that says where the thing comes from, so a sentence that fetches it
in one clause and uses it in the next is untouched. And the model keeps its
own reasoning: this guards what goes into the OUTLINE, the list every later
leg is written against, not what the model may think or try.

Pinned: the false source is caught, beside a right name and all; the true
compound sentences are not; the wording rung and the missing rung both
refuse; what goes back to the model names no place and no item. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import outline_facts as F  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


FALSE = [
    ("run 28's own rewrite",
     "Retrieve the S.S. Ticket from Bill on the S.S. Anne"),
    ("...and the ship by another name",
     "Obtain the S.S. Ticket from Bill aboard the ship"),
    ("run 28's inserted leg", "Obtain the Coin Case from the Game Corner"),
    ("a wrong source with nothing else in the clause",
     "Retrieve the Secret Key from the Game Corner"),
]
TRUE = [
    ("the leg as first written", "Retrieve the S.S. Ticket from Bill"),
    ("the right source", "Retrieve the S.S. Ticket from Bill at the Sea Cottage"),
    ("fetched in one clause, used in the next",
     "Retrieve the S.S. Ticket from Bill at the Sea Cottage, then board "
     "the S.S. Anne"),
    ("...and with 'to' joining them",
     "Obtain the Coin Case from the man in the Celadon diner to use it at "
     "the Game Corner"),
    ("a right source that names the same place twice",
     "Retrieve the Secret Key from the Pokemon Mansion on Cinnabar Island"),
    ("a plain deed", "Defeat Misty for the Cascade Badge"),
    ("a place to reach", "Reach Vermilion City"),
    ("a party state", "every party member is at least level 20"),
]
for name, t in FALSE:
    ck(f"caught: {name}", A.says_a_false_fact(t), t)
for name, t in TRUE:
    ck(f"left alone: {name}", not A.says_a_false_fact(t),
       (t, A.says_a_false_fact(t)))

src = (ROOT / "planner/author.py").read_text()
ck("the wording rung refuses one",
   "_ff = says_a_false_fact(new)" in src
   and "a rewrite may not put a " in src)
ck("the missing rung refuses one",
   "_ff = says_a_false_fact(ins)" in src
   and "turned_down.append((ins, FALSE_FACT_FEEDBACK))" in src)
ck("what the model is told names no place, no item and no fact",
   not any(w in A.FALSE_FACT_FEEDBACK.lower() for w in
           ("anne", "bill", "corner", "mansion", "ticket", "key", "not got",
            "is wrong", "false"))
   and "without claiming where" in A.FALSE_FACT_FEEDBACK.lower())
ck("the reason itself is kept for our side",
   A.says_a_false_fact(FALSE[0][1]) == "S.S. Ticket is not got there")
ck("the tables are the judge's own",
   A.says_a_false_fact is not None and F.SOURCES)
ck("a clause boundary ends the source claim",
   F._CLAUSE_END.search(", then board") is not None
   and F._CLAUSE_END.search(" to board") is not None
   and F._CLAUSE_END.search(" on the S.S. Anne") is None)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
