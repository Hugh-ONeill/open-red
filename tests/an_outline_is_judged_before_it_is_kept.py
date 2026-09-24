#!/usr/bin/env python3
"""A composed outline is judged before it is kept, and a faulty one is
composed again.

compare_outlines.judge has read an outline for a fact the game does not
bear out and for towns arrived at in an order the run cannot walk since
2026-09-19 — as a tool for a hand pick. Run 34 (2026-09-23) played an
outline with "Reach Celadon City" at 16, "Reach Lavender Town" at 24 and
"Navigate through the Rock Tunnel" at 30, the very pair the judge flags,
and leg 14 spent two hours and fourteen plan versions hunting a drink for
a store it could not reach. The chain never asked the judge.

Now the drafts are composed, the composition is judged, and a faulty one
is composed again from the same drafts — at most three times — and the
best-ranked is kept. THE JUDGE STAYS ON THE CHECK SIDE: it chooses among
what the model wrote and says nothing to it, exactly as validate() refuses
a plan.

Pinned: a clean first composition is kept at once; a faulty one is
composed again and the clean second is kept; three faulty ones keep the
fewest-faulted; the notes kept are the winner's; the faults are said in
the log; the judge is imported for the choice and given nothing to say;
the outline path goes through it. Synthetic."""
from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import brock_probe  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


CLEAN = ["Choose a starter Pokemon", "Defeat Brock for the Boulder Badge",
         "Reach Lavender Town", "Reach Celadon City"]
INVERTED = ["Choose a starter Pokemon", "Defeat Brock for the Boulder Badge",
            "Reach Celadon City", "Reach Lavender Town"]
FALSE = ["Retrieve the Poké Ball from the Pallet Town resident",
         "Defeat Brock for the Boulder Badge",
         "Reach Lavender Town", "Reach Celadon City"]
BOTH = ["Retrieve the Poké Ball from the Pallet Town resident",
        "Defeat Brock for the Boulder Badge",
        "Reach Celadon City", "Reach Lavender Town"]

calls = []
chats = []
brock_probe.chat = lambda msgs, model, **kw: chats.append(msgs) or "{}"


def compose_from(seq):
    it = iter(seq)

    def _compose(goal, drafts, model):
        legs = next(it)
        calls.append(legs)
        A.OUTLINE_NOTES.append((legs[0], f"note of composition {len(calls)}"))
        return list(legs), None
    A._outline_compose = _compose


def judged(seq):
    calls.clear()
    A.OUTLINE_NOTES.clear()
    compose_from(seq)
    buf = io.StringIO()
    with redirect_stdout(buf):
        legs, stages = A._outline_judged("goal", [CLEAN], "m")
    return legs, buf.getvalue()


legs, out = judged([CLEAN])
ck("a clean first composition is kept at once",
   legs == CLEAN and len(calls) == 1, (legs, len(calls)))
ck("...and the log says so",
   "[outline judge] composition 1: 0 fault(s)" in out
   and "keeping composition 1" in out, out)

legs, out = judged([INVERTED, CLEAN, INVERTED])
ck("a composition that arrives at Celadon before Lavender is composed again",
   len(calls) == 2, len(calls))
ck("...and the clean second one is kept", legs == CLEAN, legs)
ck("...with the notes that composition wrote, not the first one's",
   A.OUTLINE_NOTES == [(CLEAN[0], "note of composition 2")], A.OUTLINE_NOTES)
ck("the fault is said in the log, for us",
   "reach order: Celadon is reached before Lavender" in out, out)

legs, out = judged([FALSE, CLEAN])
ck("a composition stating what the game does not bear out is composed again",
   legs == CLEAN and len(calls) == 2 and "FALSE FACT" in out, out)

EARLY_KEY = ["Choose a starter Pokemon", "Defeat Brock for the Boulder Badge",
             "Obtain the Secret Key", "Reach Lavender Town", "Reach Celadon City",
             "Reach Cinnabar Island"]
legs, out = judged([EARLY_KEY, CLEAN])
ck("a composition fetching a gate item before the town it is got in is composed again "
   "(the rungs' definition of a fault, one with the draw's; 2026-09-24)",
   legs == CLEAN and len(calls) == 2 and "comes BEFORE" in out, out)

legs, out = judged([BOTH, INVERTED, FALSE])
ck("three faulty compositions keep the fewest-faulted, false facts first",
   len(calls) == 3 and legs == INVERTED, (len(calls), legs))
ck("...and say which was kept", "keeping composition 2" in out, out)

ck("the judge was given nothing to say: no prompt was built for it",
   chats == [], chats)

SRC = (ROOT / "planner/author.py").read_text()
_code = "\n".join(l for l in SRC.splitlines() if not l.lstrip().startswith("#"))
i_def = _code.index("def outline(")
i_next = _code.index("\ndef ", i_def + 10)
ck("the outline path goes through the judge",
   "legs, stages = _outline_judged(goal, drafts, model)" in _code[i_def:i_next])
i_j = _code.index("def _outline_judged(")
i_jn = _code.index("\ndef ", i_j + 10) if "\ndef " in _code[i_j + 10:] else len(_code)
_body = _code[i_j:i_jn]
ck("it composes at most three times, from the same drafts",
   A.OUTLINE_COMPOSITIONS == 3
   and "_outline_compose(goal, drafts, model)" in _body)
ck("...and the composition is handed the drafts and the goal, never the verdict",
   "def _outline_compose(goal: str, drafts: list, model: str)" in _code
   and "judge" not in _code[_code.index("def _outline_compose("):
                            _code.index("OUTLINE_COMPOSITIONS = ")])
ck("the verdict is printed, not spoken",
   'print(f"[outline judge]' in _body and "chat(" not in _body)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
