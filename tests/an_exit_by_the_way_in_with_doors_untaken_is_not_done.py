#!/usr/bin/env python3
"""An objective to EXIT a place is not judged done when every walked way out
lands on one road and the place has ways out seen and never taken.

Run 57 (2026-10-16): "Exit Victory Road" closed on "[check-done] done: The
player is currently standing in ROUTE_23, which is the area reached after
exiting Victory Road", with the party out by the 1F door it went in through,
nothing gained, and 2F's (29,7) on its own page as never taken.

Synthetic; the judge is never called on a refusal.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import author as A  # noqa: E402

checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


def rec(extra_out=None, unreached=None, town=False):
    out_to = "CINNABAR_ISLAND|0,0" if town else "ROUTE_23|4,31"
    ex = {"ROUTE_23|4,31": {"4,31": {"n": 28, "to": "VICTORY_ROAD_1F|5,9"}},
          "VICTORY_ROAD_1F|5,9": {"8,17": {"n": 45, "to": out_to},
                                  "1,1": {"n": 6, "to": "VICTORY_ROAD_2F|1,5"}},
          "VICTORY_ROAD_2F|1,5": {"1,1": {"n": 6, "to": "VICTORY_ROAD_1F|5,9"}}}
    if extra_out:
        ex["VICTORY_ROAD_2F|1,5"]["29,7"] = {"n": 1, "to": extra_out}
    f = Path(tempfile.mkdtemp(prefix="exitwayin_")) / "explored.json"
    f.write_text(json.dumps({"explored": ex, "visits": {k: 3 for k in ex},
                             "unreached_at": ({"VICTORY_ROAD_2F|1,5": ["29,7", "27,7"]}
                                              if unreached is None else unreached)}))
    return str(f)


G = "Exit Victory Road"
r = A._exit_by_way_in(G, rec())
ck("one mouth onto a road, doors seen and untaken: named", r and "ROUTE_23|4,31" in r
   and "VICTORY_ROAD_2F (29,7)" in r, r)
ck("...and check_done refuses without asking the model",
   A.check_done(G, "standing on ROUTE_23 with a party", "no-model", observed=rec(),
                gained="NOTHING new") is False)
ck("out by a second mouth too: not this rule",
   A._exit_by_way_in(G, rec(extra_out="ROUTE_23|14,31")) is None)
ck("no way out seen and untaken (a one-mouth place): not this rule",
   A._exit_by_way_in(G, rec(unreached={})) is None)
ck("one mouth onto a town: not this rule",
   A._exit_by_way_in(G, rec(town=True)) is None)
ck("an objective that does not say exit: not this rule",
   A._exit_by_way_in("Reach the Indigo Plateau", rec()) is None)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, det in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not det else f"  {str(det)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
