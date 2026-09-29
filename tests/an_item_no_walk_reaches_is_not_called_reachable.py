#!/usr/bin/env python3
"""An untouched item no walk reaches is not called one "you can reach".

Silph 5F's CARD KEY was refused "no reachable tile adjacent" and the same
round then said "you can reach 2 thing(s) here you have never interacted
with (ITEM_SILPH_CO_5F_4_6, ITEM_SILPH_CO_5F_21_16)"; the run kept going
back to the main floor for it (run 19, 2026-09-29). Now those are said
apart, with any pad the run knows sets it down on this floor.

Synthetic.
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


x = object.__new__(E.Executor)
x.pad_lands = {"SILPH_CO_9F|17,15": {"map": "SILPH_CO_5F", "at": "9,15"}}
cur = {"map": {"id": "SILPH_CO_5F", "objects": [
    {"name": "ITEM_SILPH_CO_5F_21_16", "kind": "item", "reachable": False},
    {"name": "ITEM_SILPH_CO_5F_4_6", "kind": "item", "reachable": False},
    {"name": "SILPHCO5F_ROCKER", "kind": "person", "reachable": True}]}}

out = x._untouched_lines(cur, ["ITEM_SILPH_CO_5F_21_16", "ITEM_SILPH_CO_5F_4_6"], [])
txt = " ".join(out)
ck("unreachable items are not called reachable", "you can reach" not in txt, txt)
ck("...they are named as no walk reaching them",
   "NO WALK FROM WHERE YOU STAND REACHES THEM: ITEM_SILPH_CO_5F_21_16" in txt, txt)
ck("...with the pad known to set you down on this floor",
   "SILPH_CO_9F (17,15) sets you down ON this floor's pad at (9,15)" in txt, txt)
ck("...and the room is not called finished", "The way on is not in this room" not in txt, txt)

out = x._untouched_lines(cur, ["SILPHCO5F_ROCKER", "ITEM_SILPH_CO_5F_21_16"], [])
txt = " ".join(out)
ck("a reachable one is still offered as reachable",
   "you can reach 1 thing(s)" in txt and "(SILPHCO5F_ROCKER)" in txt, txt)
ck("...and the unreachable one said apart", "REACHES THEM: ITEM_SILPH_CO_5F_21_16" in txt, txt)

out = x._untouched_lines({"map": {"id": "SILPH_CO_3F", "objects": [
    {"name": "ITEM_X", "kind": "item", "reachable": False}]}}, ["ITEM_X"], [])
ck("no pad known for this floor: no pad named",
   "You know of" not in " ".join(out), out)

out = x._untouched_lines({"map": {"id": "M", "objects": []}}, [], ["PC"])
ck("nothing untouched but a PC: the old finished line stays",
   any("The way on is not in this room" in t for t in out), out)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
