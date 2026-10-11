#!/usr/bin/env python3
"""A THROUGH leg is not put off while the run stands inside the place.

Run 51 (2026-10-11): on MT_MOON_B2F with the Super Nerd beaten, the
"later" rung pushed "Navigate Mt. Moon and fight Team Rocket" (and "Exit
Mt. Moon" with it) behind "Reach Cerulean City", which only that crossing
reaches; the next plan used an ESCAPE_ROPE and walked out the way it came
in (user: "it shouldnt have been able to finish the mt moon leg since its
not finished").

Pinned on run 51's own record at that moment: refused for the navigate and
the exit leg from B2F; allowed from outside the place, and for a leg that
is not a through. Mixed (real record, source pin).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

REC = ROOT / "tests/fixtures/run51_mt_moon/inside_b2f.json"
IN = "standing in MT_MOON_B2F with IVYSAUR L23"
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


r = A._inside_unfinished_through("Navigate Mt. Moon and fight Team Rocket", IN, REC)
ck("navigate leg, inside, one mouth: refused", "inside MT_MOON" in r, r)
ck("exit leg too", A._inside_unfinished_through("Exit Mt. Moon", IN, REC) != "")
ck("from outside the place it may move",
   A._inside_unfinished_through("Navigate Mt. Moon and fight Team Rocket",
                                "standing in PEWTER_CITY", REC) == "")
ck("a leg that is not a through is not judged",
   A._inside_unfinished_through("Reach Cerulean City", IN, REC) == "")
src = (ROOT / "planner/author.py").read_text()
cl = src[src.index("def check_later("):]
ck("check_later refuses on it before asking the model",
   cl.index("_inside_unfinished_through(goal, start)") < cl.index("brock_probe.chat("))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
