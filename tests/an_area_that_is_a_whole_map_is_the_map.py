#!/usr/bin/env python3
"""An area condition holding a bare map name becomes a map condition.

Run 63, 2026-10-24: leg 14's heal_at_cerulean_center was {"area":
"CERULEAN_POKECENTER", "party_healthy": true}; an area is "MAP|x,y" and the
bare name equals no region, so the step was carried past NOT achieved with
the party healed inside that Center, after three rounds of healing.

Pinned: a bare-map area becomes map; one repeating the step's map goes; a
real part id is untouched; a bare area naming a different map than the step's
is left for validation.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))


def norm(dw):
    plan = {"subgoals": [{"id": "s", "goal_text": "g", "done_when": dict(dw)}]}
    A.strip_part_labels(plan)
    return plan["subgoals"][0]["done_when"]


ck("a bare-map area becomes map",
   norm({"area": "CERULEAN_POKECENTER", "party_healthy": True})
   == {"map": "CERULEAN_POKECENTER", "party_healthy": True})
ck("...and goes when it repeats the step's map",
   norm({"map": "CERULEAN_POKECENTER", "area": "CERULEAN_POKECENTER"}) == {"map": "CERULEAN_POKECENTER"})
ck("a part id is untouched", norm({"area": "CERULEAN_POKECENTER|0,3"}) == {"area": "CERULEAN_POKECENTER|0,3"})
ck("two different places are left for validation",
   norm({"map": "CERULEAN_CITY", "area": "CERULEAN_POKECENTER"})
   == {"map": "CERULEAN_CITY", "area": "CERULEAN_POKECENTER"})

ck("words that are not a map id are left for validation",
   norm({"area": "not a part (at all)"}) == {"area": "not a part (at all)"})

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
