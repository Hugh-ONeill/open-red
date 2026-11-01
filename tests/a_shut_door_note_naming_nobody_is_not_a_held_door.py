#!/usr/bin/env python3
"""A shut-door note that names nobody is not a door someone holds.

Run 70, Mt Moon (2026-11-01): "Places you have already been that still
have ways you have NEVER taken" read "MT_MOON_B2F|23,21 (5,7(the way onto
it is blocked; nobody)" and "MT_MOON_B2F|20,5 (5,7(s) never on screen, and
the way may run through them)". The held-door parse split each note on its
last "(" and took what followed as the person, which only fits the
"(WHO is standing there)" form.

Pinned: only that form becomes "x,y(WHO)"; every other form, and the
standing region, is left out. Synthetic.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


notes = {
    "CERULEAN_CITY|4,4": ["27,9 (CERULEANCITY_GUARD2 is standing there)"],
    "MT_MOON_B2F|23,21": ["5,7 (the way onto it is blocked; nobody is standing there)"],
    "MT_MOON_B2F|20,5": ["5,7 (no walk over ground you have SEEN reaches it yet; "
                         "this floor has 10 spot(s) never on screen, and the way "
                         "may run through them)"],
    "MT_MOON_B2F|27,5": ["5,7 (the way onto it is blocked; nearest person "
                         "MTMOONB2F_SUPER_NERD, 8 cells off)"],
    "CELADON_GYM|4,17": ["4,17 (None is standing there)"],
    "ROUTE_9|0,8": ["3,3 (ROCKET is standing there)"],
}
h = E.Executor._held_doors(notes, "ROUTE_9|0,8")
ck("a named person is a held door",
   h.get("CERULEAN_CITY|4,4") == ["27,9(CERULEANCITY_GUARD2)"], h)
ck("blocked by nobody is not held", h.get("MT_MOON_B2F|23,21") == [], h)
ck("unseen ground is not held", h.get("MT_MOON_B2F|20,5") == [], h)
ck("a nearest person is not a holder", h.get("MT_MOON_B2F|27,5") == [], h)
ck("None is not a person", h.get("CELADON_GYM|4,17") == [], h)
ck("the standing region is left out", "ROUTE_9|0,8" not in h, h)
ck("nothing garbled anywhere",
   not any("(s)" in d or "nobody" in d or "blocked" in d
           for v in h.values() for d in v), h)
ck("empty input is fine", E.Executor._held_doors(None, "") == {})

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
