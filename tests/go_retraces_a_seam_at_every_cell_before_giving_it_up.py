#!/usr/bin/env python3
"""go retraces a seam at every cell before giving it up (run 19, 2026-09-29).

The uncork tried skips 1-3 and declined once every cell already tried landed
in the pocket, so Saffron's west edge was tried at rows 20-23 and (0,17), the
cell the party had arrived on from the Route 7 gate strip, never; the reverse
edge was condemned and `go` stopped offering a walk it had made (user: "the
issue is really more that go is failing in the first place ... its been
through the area before"). Every cell never crossed at is now tried, a
reverse edge is condemned only when none are left, and verdicts saved under
the old rule are set aside once. Source checks.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner/executor.py").read_text()
un = src[src.index("    def _uncork_seam"):src.index("    def _recross_for_target")]
checks = [
    ("no fixed three-cell limit", "for skip in (1, 2, 3):" not in un),
    ("no up-front decline on cells already tried",
     "every cell of that seam already tried lands here" not in un),
    ("the far side's cells are read and the untried ones tried in order",
     '.get(_OPP[back]) or [])' in un and "if i not in _taken]" in un and "skip = _skips.pop(0)" in un),
    ("it says how many were left", "self._uncork_left = len(_skips) if _skips is not None else None" in un),
    ("a declined uncork leaves no stale count", "self._uncork_left = None          # a declined uncork" in un),
    ("a reverse edge is kept while cells are untried",
     'if getattr(self, "_uncork_left", None):' in src and '"inference_kept_cells_untried"' in src),
    ("old verdicts are set aside once", 'if not data.get("bad_seam_v2") and self._bad_seam:' in src
     and '"bad_seam_v2": True,' in src),
    ("the go-failure note is gone (wrong layer)", "_note_b + _note_g + _note_m + _note_c" not in src),
]
failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")

# ...and a crossing that was made is replayed at the cell it was made at: a
# skip counts from where the party stands, so "west#skip5" from elsewhere is
# another cell.
import json, sys as _s  # noqa: E401,E402
_s.path.insert(0, str(ROOT / "planner"))
import executor as E  # noqa: E402
x = object.__new__(E.Executor)
x.explored, x.visits, x._bad_seam = {}, {}, set()
x.logged = []
x.log = lambda k, **kw: x.logged.append(k)
bo = {"mode": "overworld", "map": {"id": "SAFFRON_CITY", "region": "12,0"}, "player": {"x": 0, "y": 17}}
ao = {"mode": "overworld", "map": {"id": "ROUTE_7", "region": "18,2"}, "player": {"x": 19, "y": 8}}
for _ in range(80):
    try:
        x.note_transition(bo, {"dir": "west", "skip": 5}, ao,
                          op_detail="ok (crossed — now on ROUTE_7 at (19,8) (from SAFFRON_CITY (0,17), via the gap at (0,17)))")
        break
    except AttributeError as e:
        setattr(x, str(e).split("'")[-2], {})
_e = (x.explored.get("SAFFRON_CITY|12,0") or {}).get("west#skip5") or {}
ck2 = [("the crossing keeps the cell it was made at", _e.get("cell") == [0, 17]),
       ("go replays the cell, not the skip",
        '_args.pop("skip", None)\n                        _args["x"], _args["y"] = int(_cell[0]), int(_cell[1])' in src),
       ("the uncork's crossings keep theirs too", 'reason="uncork",\n                                     op_detail=' in src)]
for n, ok in ck2:
    print(("ok   " if ok else "FAIL ") + n)
sys.exit(1 if failed or not all(ok for _n, ok in ck2) else 0)
