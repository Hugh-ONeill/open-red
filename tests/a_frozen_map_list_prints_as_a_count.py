#!/usr/bin/env python3
"""new_map_from's frozen not_maps list prints as a count wherever a condition
becomes text, and stays whole in the plan for pred_holds.

Run 36, 2026-10-03: 99 map names on the status line and the page for one
step (user: "also check out the DONEWHEN for that")."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "planner"))
import pred_text as P  # noqa: E402
import executor as E   # noqa: E402
dw = {"new_map_from": "CELADON_CITY", "not_maps": ["A", "B", "C"]}
big = {"new_map_from": "X", "not_maps": [f"M{i}" for i in range(40)]}
txt = P.dumps(big)
checks = [
    ("a long list prints as what it means", '"the 40 map(s) stood on when this step began"' in txt and '"M3"' not in txt, txt),
    ("a short one is shown as it is", '"A"' in P.dumps(dw), P.dumps(dw)),
    ("the condition itself is untouched", dw["not_maps"] == ["A", "B", "C"], ""),
    ("pred_holds still reads the real list",
     not E.pred_holds(dw, {"map": {"id": "B"}, "came_from": "CELADON_CITY"})
     and E.pred_holds(dw, {"map": {"id": "D"}, "came_from": "CELADON_CITY"}), ""),
]
for n, ok, d in checks: print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
raise SystemExit(0 if all(ok for _, ok, _ in checks) else 1)
