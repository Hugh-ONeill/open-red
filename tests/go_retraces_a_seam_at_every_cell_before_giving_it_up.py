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
sys.exit(1 if failed else 0)
