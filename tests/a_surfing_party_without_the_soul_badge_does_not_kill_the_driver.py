#!/usr/bin/env python3
"""The "SURF known, SOULBADGE missing" flag is written to a seen table
that exists.

Run 27, 2026-09-18, Safari Zone: the party had learned SURF with five
badges and no SOULBADGE, the water-frontier block set
m.seen.surf_badge_missing before the seen table was built, and the driver
died with "attempt to index field 'seen' (a nil value)" — on every
observation with water in view, so every attempt would have died.

Pinned: the flag creates the table if need be, and the builder below
merges into an existing table instead of replacing it. Source-anchored.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def ck(name, cond, detail=""):
    checks.append((name, bool(cond), detail))


shim = (ROOT / "harness/shim.lua").read_text()
ck("the surf-badge flag creates the seen table if it is not there yet",
   'm.seen = m.seen or {}\n        m.seen.surf_badge_missing = "SOULBADGE"' in shim)
ck("the builder merges into an existing seen table",
   "m.seen = m.seen or {}\n  m.seen.n = mask.n or 0\n  m.seen.frontier_n = #front\n  m.seen.frontier_map_n = fmap" in shim)
ck("...and no longer replaces it", "m.seen = { n = mask.n or 0" not in shim)
ck("the flag is written before the builder runs (which is why the merge matters)",
   shim.index('m.seen.surf_badge_missing = "SOULBADGE"') < shim.index("m.seen.frontier_map_n = fmap"))

failed = [n for n, ok, _ in checks if not ok]
for n, ok, d in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not d else f"  {d}"))
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
sys.exit(1 if failed else 0)
