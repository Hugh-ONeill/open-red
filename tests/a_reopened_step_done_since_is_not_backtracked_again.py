#!/usr/bin/env python3
"""A step re-opened (not relocated) and done since is not backtracked again.

Run 69, 2026-10-31: teach_surf failed with no HM, the backtrack re-opened
withdraw_surf (has_item HM_SURF, redo=false), that got HM03 in the Secret
House, teach_surf failed again on a party that cannot learn it, and the
second pass escalated withdraw_surf with redo=True: "This step is done when
you stand in a DIFFERENT part that satisfies DONE_WHEN", for an item already
in the bag. The second pass exists for a relocate (a wrong place guessed);
it now runs only after one.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "planner" / "executor.py").read_text()

checks = []
def ck(n, ok, d=""): checks.append((n, bool(ok), d))

i = src.index('self.log("backtrack_relocated", subgoal=prev["id"])')
blk = src[i:i + 3200]
ck("the second backtrack waits on a relocate",
   "if not ok and backtracks < 2 and _redo:" in blk, blk[:600])
ck("...and a re-open done since is logged and left",
   "if not ok and backtracks < 2 and not _redo:" in blk
   and '"backtrack_again_skipped"' in blk)
ck("the first pass still re-opens a step that does not hold",
   "_redo = bool(pred_holds(prev.get(\"done_when\") or {}," in src)
ck("the old unconditional second pass is gone",
   "if not ok and backtracks < 2:\n" not in blk)

bad = [n for n, ok, _ in checks if not ok]
for n, ok, dd in checks:
    print(("ok   " if ok else "FAIL ") + n + ("" if ok or not dd else f"  {str(dd)[:300]}"))
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
