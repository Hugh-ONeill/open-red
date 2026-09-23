#!/usr/bin/env python3
"""Among equally fresh ways out, the one on the side the model's own plan
named comes first, and a way is one entry on the page, not two.

Route 6, 2026-09-23 11:34, under go_to_vermilion_city. The plan sentence
of the round before said "to reach Vermilion City, I need to continue
south". The page's line 1 was the explore pick, "take door (10,7) ... in
the north part of this map", line 2 the same door on its own row, and
line 3 "walk south -> UNKNOWN — never taken from here". Among fresh,
reachable ways the rank's tie fell to kind and key, "door" before "seam".
It took line 1 (the Saffron gate), heard "the road's closed", pinned that
on the direction it had been heading, and hunted a drink for an hour with
the south edge still untaken.

Nothing of ours steers this: the direction is read from the model's own
sentence, a fresh reachable seam on that side ranks above a fresh door and
says why, and the way the explore line names is folded into that line so a
door cannot take two lines ahead of a seam. Which to take is still the
model's.

Pinned: the direction read from a sentence, and none from two; the
promotion, its note, and the explore line that follows it; no promotion
without a direction, so the order is what it was; one entry per way on the
page; the promotion needs a fresh, reachable, unrefused seam; the rank term
sits after the refused term. Synthetic, tests/candidates.py's fixture."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
sys.path.insert(0, str(ROOT / "tests"))
import ledger as L  # noqa: E402
import candidates as C  # noqa: E402
import untried as U  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


D = L.plan_direction
ck("a sentence naming one direction gives it",
   D(SimpleNamespace(_plan_said="To reach Vermilion City, I need to continue south.")) == "south")
ck("...however it is spelled",
   D(SimpleNamespace(_plan_said="The southern edge is unseen; I will head SOUTHWARD.")) == "south")
ck("two directions are none", D(SimpleNamespace(_plan_said="I will go north, then east.")) is None)
ck("a compound word is not a direction",
   D(SimpleNamespace(_plan_said="the northeast corner")) is None)
ck("no sentence is none", D(SimpleNamespace(_plan_said="")) is None
   and D(SimpleNamespace()) is None)


def page(plan, target="map:VERMILION_CITY"):
    ex = C.make(frontier={U.HERE: ["10,7", "north", "south"]})
    ex._plan_said = plan
    o = C.obs(ex, ["10,7"], ["north", "south"])
    cands = L.build(ex, o, target=target)
    return cands, L.render(cands, ex, o, target=target)


cands, text = page("To reach Vermilion City, I need to continue south.")
keys = [c.key for c in cands]
south = next(c for c in cands if c.kind == "seam" and c.key == "south")
ck("the seam on the side the plan named ranks above the fresh door",
   keys.index("south") < keys.index("10,7"), keys)
ck("...and says why, in the model's own terms",
   "the direction your own plan named" in (south.note or ""), south.note)
ck("...and the explore line names it, with why",
   cands[0].kind == "op" and "walk south" in cands[0].note
   and "the direction your own plan named" in cands[0].note, cands[0].note)
ck("the page leads with it", " 1. explore — take walk south" in text, text[:600])
ck("one entry per way: the way the explore line names has no second row",
   text.count("walk south") == 1, text[:900])
ck("...while the other ways keep theirs",
   "(10,7)" in text and "walk north" in text, text[:900])
ck("the seam is still the model's to take or leave: nothing says the door is wrong",
   "wrong" not in text.lower() and "should" not in text.lower(), text[:900])

cands2, text2 = page("I will go north, then east.")
keys2 = [c.key for c in cands2]
ck("with no one direction named, the order is what it was",
   keys2.index("10,7") < keys2.index("south")
   and "the direction your own plan named" not in text2, keys2)
ck("...and the explore line names the door, folded with its row",
   " 1. explore — take door (10,7)" in text2 and text2.count("(10,7)") == 1, text2[:700])

cands3, _ = page("I will continue north to the gate.")
keys3 = [c.key for c in cands3]
ck("the promotion follows whatever side is named", keys3.index("north") < keys3.index("10,7"), keys3)

SRC = (ROOT / "planner/ledger.py").read_text()
_code = "\n".join(l for l in SRC.splitlines() if not l.lstrip().startswith("#"))
ck("the rank term sits after the refused term, before the goal's kinds",
   "1 if _refused(c) else 0, _plan_way,\n                  0 if (c.kind in _goal_kinds or _leader) else 1," in _code)
i = _code.index("_plan_way = 1")
ck("the promotion needs a fresh, reachable, unrefused seam on that side",
   'c.kind == "seam" and c.status == "untried"' in _code[i:i + 400]
   and "c.reachable and not _refused(c)" in _code[i:i + 400]
   and '== _said_dir' in _code[i:i + 400])
ck("the page folds a way into the explore line only when that line is shown",
   'getattr(ex, "_explore_lead_key", None) == (c.kind, c.key)' in _code
   and 'any(x.kind == "op" for x in shown)' in _code)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
