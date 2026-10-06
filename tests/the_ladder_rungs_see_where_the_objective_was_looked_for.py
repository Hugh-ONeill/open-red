#!/usr/bin/env python3
"""The ladder's rungs are shown where the objective has already been looked
for, as the drafts are.

Run 37, 2026-10-06: "Obtain HM04 from the Warden in the Safari Zone" went
down the ladder with every rung reasoning "the Warden is at the gate" —
the gate worker pressed seven times, Fuchsia's door at 27,27 never gone
through, the sign beside it saying "SAFARI ZONE WARDEN's HOME" — and was
passed over. The rungs were shown none of that record (user: "maybe build
that rung-version thing").

Pinned (source): the blocker, missing-step and wording rungs each add
looked_text(observed, goal) when they have the record; check_later, which
is not given it, is left alone."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/author.py").read_text()
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def body(fn):
    i = src.index(f"\ndef {fn}(")
    j = src.find("\ndef ", i + 5)
    return src[i:j]


ck("the blocker rung reads it",
   '_looked = looked_text(observed, goal) if observed else ""' in body("check_blocker")
   and "+ _heldtxt + _looked)" in body("check_blocker"))
ck("the missing-step rung reads it",
   "+ (looked_text(observed, goal) if observed else \"\"))" in body("check_missing"))
ck("the wording rung reads it",
   "+ (looked_text(observed, goal) if observed else \"\"))" in body("check_wording"))
ck("the drafts still read it", "said += looked_text(observed, goal)" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
