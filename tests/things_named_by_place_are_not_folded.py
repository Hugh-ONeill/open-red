#!/usr/bin/env python3
"""In the walked record, things named by their place (ITEM_<MAP>_x_y) are
listed whole; only numbered kin are folded.

Run 38, 2026-10-08: Mt Moon 1F's six item balls read "ITEM_MT_MOON_1F_2 x2*,
ITEM_MT_MOON_1F_20*, _35*, _36*, _5*" — last coordinates cut, two merged —
while the Moon Stone draft searched B2F, a floor with no balls left.

Pinned: coordinate-named things keep both coordinates and are never
merged; numbered kin still fold (SLOT_MACHINE_1, _2 -> x2). Synthetic."""
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


d = {"explored": {"MT_MOON_1F|3,2": {}}, "visits": {"MT_MOON_1F|3,2": 3},
     "sightings": {"MT_MOON_1F|3,2": ["ITEM_MT_MOON_1F_2_2", "ITEM_MT_MOON_1F_2_20",
                                      "SLOT_MACHINE_1", "SLOT_MACHINE_2"]},
     "touched": {}, "hints": {}, "frontier": {}, "dead_ends": {}, "flag_sites": {}}
with tempfile.TemporaryDirectory() as t:
    p = Path(t) / "explored.json"
    p.write_text(json.dumps(d))
    w = A.observed_text(p)
line = next((l for l in w.splitlines() if "MT_MOON_1F|3,2:" in l), "")
ck("both balls keep both coordinates",
   "ITEM_MT_MOON_1F_2_2*" in line and "ITEM_MT_MOON_1F_2_20*" in line, line)
ck("...and are not merged", "ITEM_MT_MOON_1F_2 x2" not in line, line)
ck("numbered kin still fold", "SLOT_MACHINE x2*" in line, line)

failed = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
