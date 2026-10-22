#!/usr/bin/env python3
"""The explore line says it looks at walls that may have moved before it
leaves the floor, because that is what explore does.

Run 60, 2026-10-22: on Mansion B1F the page's explore line read "THIS AREA
IS FULLY WORKED ... explore walks there" toward 1F, and the stale-wall note
said "explore's own walks will not" go through such a wall, while the deed
(executor _explore_step) walks beside the nearest moved-maybe wall first:
the look at (26,18) that opens the floor's north half and then the key's
corner. Runs 59 and 60 believed the line and left; 10-05 and 10-07 sent
explore anyway and had the key within the hour.

Pinned: with frontier_stale and nothing else, the line names the nearest
stand and wall and does not say FULLY WORKED; unseen ground still comes
first, as in the deed; and the stale-wall note no longer says explore will
not go.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import ledger as L  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


class Ex:
    def _where(self, obs):
        m = obs.get("map") or {}
        return f"{m.get('id')}|{m.get('region')}"


STALE = [{"x": 26, "y": 18, "wx": 26, "wy": 17}, {"x": 10, "y": 6, "wx": 9, "wy": 6}]
obs = {"mode": "overworld", "party": [],
       "map": {"id": "POKEMON_MANSION_B1F", "region": "10,9", "frontier_stale": STALE}}
w = L._plan_explore_words(Ex(), obs, cands=[])
ck("the line names the nearest wall to look at", "(26,18) beside (26,17)" in w, w)
ck("...and how many", "2 such cell(s)" in w, w)
ck("...and does not call the floor worked out", "FULLY WORKED" not in w, w)

obs2 = {"mode": "overworld", "party": [],
        "map": {"id": "POKEMON_MANSION_B1F", "region": "10,9", "frontier_stale": STALE,
                "frontier": [{"x": 3, "y": 3}], "seen": {"frontier_n": 5}}}
w2 = L._plan_explore_words(Ex(), obs2, cands=[])
ck("unseen ground still comes first, as in the deed",
   "nearest edge of the ground you have seen" in w2 and "WALL" not in w2, w2)

src = (ROOT / "planner" / "ledger.py").read_text()
ck("the stale-wall note says explore looks at them before leaving",
   "but explore does walk beside them to look" in src)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {str(d)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
