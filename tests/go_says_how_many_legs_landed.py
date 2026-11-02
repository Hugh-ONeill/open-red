#!/usr/bin/env python3
"""go's summary counts the legs that landed, not the route's length.

Run 70, 2026-11-02, go_to_celadon_game_corner r4: go printed "walked 18
leg(s) over walked ground toward GAME_CORNER|8,5 — now at SAFARI_ZONE_GATE"
when its first leg (walk:SAFARI_ZONE_GATE|3,5) did not arrive; it had walked
none. A harness-sourced false count.

Pinned by source: _walk_route keeps _route_legs_done (reset on the first
call, carried through a re-planned remainder, set before each hop and to
the whole path at the end), and go's summary says "walked N of M" when N is
short of M.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()
checks = []
def ck(n, ok): checks.append((n, bool(ok)))

i = src.index("    def _walk_route(self, sg, path, _replans=0):")
body = src[i:src.index("\n    def ", i + 10)]
ck("the count is reset on the first call only",
   "if not _replans:\n            self._route_legs_done = 0" in body)
ck("each hop sets the legs done before it",
   "self._route_legs_done = _legs_base + _hop_i" in body)
ck("a whole walk counts the whole path",
   "self._route_legs_done = _legs_base + len(path)" in body)
j = src.index('_done = getattr(self, "_route_legs_done", None)')
ck("go says walked N of M when it fell short",
   'f"go: walked {_done} of {len(path)} leg(s)" if _done < len(path)' in src[j:j + 400])
ck("...and no longer prints the route's length as legs walked",
   'tr = [f"go: walked {len(path)} leg(s) over walked ground toward "' not in src)

bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
