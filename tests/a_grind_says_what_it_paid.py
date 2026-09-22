#!/usr/bin/env python3
"""A grind says what it earned in MONEY as well as in experience, and what
every grind of the run has paid.

Run 29 stood on Route 2 with 93 yen and wrote the same plan eight rounds
running: "I need more money to buy 3 Poke Balls and 1 Potion at the Pewter
City Mart. I currently have 93 yen. I will grind for money by fighting wild
Pokemon on Route 2 until I have sufficient funds" (user, 2026-09-21: "its
also currently training because it thinks you get money from wild pokemon").
Wild Pokemon carry none. The belief is the model's and wrong, and nothing
in the harness could tell it so: the grind's own summary reported exp and
encounters and never the purse, which is the one number that settles it.

So the op measures it — the money before against the money after, the
run's own record, no rule of ours about what pays — says it for this grind
and totals it over the run once there is enough of it to mean anything.
Whether to keep grinding stays the model's call.

Pinned: a grind that met wilds says what it paid; the words tell nothing
from something; the run's total is kept across legs and processes and is
held back until a dozen encounters have been met; money lost is reported
as lost but never counted as pay; a grind that met nothing says nothing;
the exp line is untouched. Synthetic."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


SRC = (ROOT / "planner/executor.py").read_text()
_g = SRC[SRC.index('note += f" earned {_gain} exp"'):]
_g = _g[:_g.index("# WHO EARNED IT.")]


# the comment above the block quotes the wording it replaced, so the
# negative checks read CODE only
_gc = "\n".join(l for l in _g.splitlines() if not l.lstrip().startswith("#"))


def has(*bits):
    return all(b in _g for b in bits)


ck("the purse is read before and after the op, off the observation",
   has('_m0, _m1 = (pre_obs or {}).get("money"), (obs or {}).get("money")'))
ck("...and only when wilds were actually met",
   has("if _nb and isinstance(_m0, int) and isinstance(_m1, int):"))
ck("what this grind paid is said ONLY when the purse moved",
   has("if _paid:", 'note += f" and {_paid:+d} money"')
   and "and no money" not in _gc)
ck("the run's own total is kept, encounters and money together",
   has("_tally[0] += _nb", "_tally[1] += max(0, _paid)",
       "self._wild_pay = _tally"))
ck("...and money LOST is never counted as money earned",
   "max(0, _paid)" in _g)
ck("the count is still kept every grind, for the plan-words answer",
   has("_tally[0] += _nb", "self._wild_pay = _tally"))
ck("...but the running total is not recited on the page",
   "over this whole run" not in _gc)
# the money block alone: the comment above it may explain the bug to a
# reader, but what reaches the MODEL must be arithmetic and nothing else
_note = _g[_g.index("_m0, _m1"):_g.index("# THE BALLS IT THREW")]
ck("the words put on the page state no rule about what pays",
   not any(w in _note.lower() for w in
           ("trainer", "carry none", "cannot", "never", "instead", "should")),
   _note[:200])
ck("the total survives a relaunch with the rest of the memory",
   '"wild_pay": list(getattr(self, "_wild_pay", None) or [0, 0]),' in SRC
   and 'self._wild_pay = list(data.get("wild_pay") or [0, 0])' in SRC)
ck("the experience line is untouched",
   'note += f" earned {_gain} exp"' in SRC
   and 'note += f" over {_nb} wild encounter(s)"' in SRC)
ck("what it paid is said after what it earned and met",
   _g.index('{_nb} wild encounter(s)') < _g.index("_m0, _m1"))

# ------- the arithmetic itself, played by hand the way the op does -------
def grind(before, after, n, tally):
    out, t = "", list(tally)
    if n and isinstance(before, int) and isinstance(after, int):
        paid = after - before
        t[0] += n
        t[1] += max(0, paid)
        if paid:
            out = f" and {paid:+d} money"
    return out, t


w, t = grind(93, 93, 12, [0, 0])
ck("a grind that paid nothing says nothing about money", w == "", w)
ck("...but its encounters are still counted for the plan-words answer",
   t == [12, 0], t)
w2, t2 = grind(93, 93, 11, t)
ck("...and the next grind carries the first one's count", t2 == [23, 0], t2)
w, _ = grind(1175, 1100, 6, [20, 0])
ck("a grind that cost money says it cost money", w == " and -75 money", w)
w, t3 = grind(1000, 1240, 4, [20, 0])
ck("a grind that PAID says so, which is what PAY_DAY looks like",
   w == " and +240 money" and t3 == [24, 240], (w, t3))
w, _ = grind(None, 1100, 6, [20, 0])
ck("no reading, no claim", w == "")
w, _ = grind(93, 93, 0, [20, 0])
ck("a grind that met nothing says nothing about money", w == "")

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
