#!/usr/bin/env python3
"""The hand-pick judge counts a town reached before the town that opens it
— and the author no longer asks the model to fix that, because it cannot.

Run 28's outline was nearly ideal except for its order (user, 2026-09-20:
"if you ignore the out of order bits the outline is pretty ideal" …
"basically the ordering issue here was in which towns were included in
which stages"). It grouped "Celadon & Saffron City" before "Lavender &
Fuchsia City": Lavender gates the road to Celadon, Celadon sells the drink
Saffron's guards want. It hid because the BADGE order was perfect (user:
"its hard to tell in this case because badge order is correct"), so the
judge reads the order the towns are ARRIVED in against the order the game
lets a run reach them.

A stage-order pass was built beside it, and measured the next day
(2026-09-21): five draws, all five still wrong, four "the order stands" and
one where walkable stages were made unwalkable, Lavender moved behind
Saffron for the Tower's sake. A stage bundles an arrival with its deeds.
And the knowledge is not there: asked about arrivals alone, 0 of 6 answers
put Lavender first; asked for the road from Vermilion to Celadon, 0 of 6
named Rock Tunnel or Lavender (user: "the stage ordering pass doesnt work
so might as well take it out"). The run finds that road by walking it.

Pinned: the judge flags Celadon and Saffron before Lavender, ranks a draft
with that fault below one without, and shows the badge order can be perfect
while it is wrong; the pass is gone from the author and nothing calls it;
the stages are still drawn and still asked what each is missing; the
judge's table cannot reach a prompt. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402
import compare_outlines as C  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


BAD = ["Reach Cerulean City", "Reach Vermilion City", "Reach Celadon City",
       "Reach Saffron City", "Reach Lavender Town", "Reach Fuchsia City"]
GOOD = ["Reach Cerulean City", "Reach Vermilion City", "Reach Lavender Town",
        "Reach Celadon City", "Reach Saffron City", "Reach Fuchsia City"]
jb, jg = C.judge(BAD), C.judge(GOOD)
ck("a town reached before the one that opens it is flagged",
   ("celadon", "lavender") in jb["reach_bad"]
   and ("saffron", "lavender") in jb["reach_bad"], jb["reach_bad"])
ck("...and the right order is not", jg["reach_bad"] == [], jg["reach_bad"])
ck("the flag says which way round it has to be",
   any("Celadon is reached before Lavender" in f for f in jb["flags"]),
   jb["flags"][:3])
ck("a draft with the fault ranks below one without",
   C.rank(jg) < C.rank(jb) and C.rank(jb)[1] == 2 and C.rank(jg)[1] == 0)
ck("the badge order alone cannot show it",
   jb["badges"] == jg["badges"] == "")
ck("the order the towns open in is named once",
   C.REACH_ORDER.index("lavender") < C.REACH_ORDER.index("celadon")
   < C.REACH_ORDER.index("saffron") < C.REACH_ORDER.index("fuchsia")
   < C.REACH_ORDER.index("cinnabar"))

# ------------------------------------------------ the pass that was removed
src = (ROOT / "planner/author.py").read_text()
_code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
ck("the author no longer asks the stages for their order",
   not hasattr(A, "_stage_order") and not hasattr(A, "STAGE_ORDER_SYS")
   and "_stage_order(" not in _code and "STAGE_ORDER_SYS" not in _code)
ck("...and says where it stood, and what the measurement was",
   "THERE WAS A STAGE-ORDER PASS HERE, AND IT IS GONE" in src
   and "0 of 6" in src)
ck("the stages are still drawn, and each still asked what it is missing",
   "stages = _stage_outline(legs, model)\n    if stages:\n" in src
   and "_dedupe_outline(_stage_missing(goal, legs, stages, model))" in src)
for f in ("author.py", "executor.py", "ledger.py", "state_text.py"):
    _c = "\n".join(l for l in (ROOT / "planner" / f).read_text().splitlines()
                   if not l.lstrip().startswith("#"))
    ck(f"the judge's town order cannot reach a prompt from {f}",
       "REACH_ORDER" not in _c and "import compare_outlines" not in _c
       and "from compare_outlines" not in _c)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
